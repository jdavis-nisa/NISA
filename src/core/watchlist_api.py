import os
import json
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import psycopg2
import psycopg2.extras
from datetime import datetime

app = FastAPI(title="NISA CVE Watchlist API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:5176","http://127.0.0.1:5173","http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health",) or request.method == "OPTIONS":
        return await call_next(request)
    if NISA_API_KEY:
        key = request.headers.get("X-NISA-API-Key", "")
        if key != NISA_API_KEY:
            return JSONResponse(status_code=403, content={"error": "Invalid or missing API key"})
    return await call_next(request)

DB = dict(host="localhost", port=5432, dbname="nisa", user="nisa_user", password="nisa_secure_2026")

def get_conn():
    return psycopg2.connect(**DB)

# ── Create tables ─────────────────────────────────────────────────
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_entries (
            id SERIAL PRIMARY KEY,
            entry_type VARCHAR(20) NOT NULL,
            value VARCHAR(255) NOT NULL,
            label VARCHAR(255),
            severity VARCHAR(20) DEFAULT 'high',
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            last_checked TIMESTAMP,
            hit_count INTEGER DEFAULT 0,
            UNIQUE(value)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist_alerts (
            id SERIAL PRIMARY KEY,
            entry_id INTEGER REFERENCES watchlist_entries(id) ON DELETE CASCADE,
            asset_id INTEGER,
            asset_ip VARCHAR(50),
            port INTEGER,
            service VARCHAR(100),
            match_type VARCHAR(50),
            detail TEXT,
            severity VARCHAR(20),
            recommendation TEXT,
            acknowledged BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ── Models ────────────────────────────────────────────────────────
class WatchEntry(BaseModel):
    entry_type: str  # cve | service | keyword
    value: str
    label: Optional[str] = ""
    severity: Optional[str] = "high"

class AckAlert(BaseModel):
    alert_ids: list[int]

# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "watchlist_api"}

# ── Watch Entries ─────────────────────────────────────────────────
@app.get("/watchlist")
def list_entries():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM watchlist_entries ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return {"entries": [dict(r) for r in rows]}

@app.post("/watchlist")
def add_entry(entry: WatchEntry):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO watchlist_entries (entry_type, value, label, severity)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (entry.entry_type, entry.value.strip(), entry.label or entry.value, entry.severity))
        eid = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return {"id": eid, "status": "added"}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=409, detail="Entry already exists")

@app.delete("/watchlist/{entry_id}")
def delete_entry(entry_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM watchlist_entries WHERE id=%s", (entry_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# ── Alerts ────────────────────────────────────────────────────────
@app.get("/alerts")
def get_alerts(unacked_only: bool = True):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if unacked_only:
        cur.execute("SELECT * FROM watchlist_alerts WHERE acknowledged=FALSE ORDER BY created_at DESC")
    else:
        cur.execute("SELECT * FROM watchlist_alerts ORDER BY created_at DESC LIMIT 100")
    rows = cur.fetchall()
    conn.close()
    return {"alerts": [dict(r) for r in rows]}

@app.post("/alerts/acknowledge")
def acknowledge_alerts(req: AckAlert):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE watchlist_alerts SET acknowledged=TRUE WHERE id=ANY(%s)", (req.alert_ids,))
    conn.commit()
    conn.close()
    return {"status": "acknowledged"}

@app.post("/alerts/acknowledge/all")
def acknowledge_all():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE watchlist_alerts SET acknowledged=TRUE")
    conn.commit()
    conn.close()
    return {"status": "all acknowledged"}

# ── Check Engine ──────────────────────────────────────────────────
RECOMMENDATIONS = {
    "rdp":  "Disable RDP if not required. Enable NLA. Restrict to VPN only. Apply latest Windows patches.",
    "ssh":  "Disable root login. Use key-based auth only. Restrict to known IPs. Update OpenSSH.",
    "smb":  "Disable SMBv1. Apply MS17-010 patch. Block ports 139/445 at perimeter.",
    "ftp":  "Replace FTP with SFTP. Disable anonymous access. Apply latest patches.",
    "telnet": "Disable immediately. Replace with SSH. Telnet transmits credentials in plaintext.",
    "vnc":  "Restrict to localhost or VPN. Require strong password. Disable if not needed.",
}

def get_recommendation(service: str, cve: str = "") -> str:
    svc = service.lower()
    for key, rec in RECOMMENDATIONS.items():
        if key in svc:
            return rec
    if cve:
        return f"Apply vendor patch for {cve}. Check NVD for affected versions and mitigations."
    return "Review service necessity. Apply latest patches. Restrict network access."

@app.post("/check")
def run_check():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get active watch entries
    cur.execute("SELECT * FROM watchlist_entries WHERE active=TRUE")
    entries = cur.fetchall()

    # Get all asset ports
    cur.execute("""
        SELECT ap.*, a.ip, a.id as asset_id, a.risk_level
        FROM asset_ports ap
        JOIN assets a ON a.id = ap.asset_id
    """)
    ports = cur.fetchall()

    new_alerts = []
    cur2 = conn.cursor()

    for entry in entries:
        etype = entry["entry_type"]
        value = entry["value"].lower()

        for port in ports:
            service = (port["service"] or "").lower()
            matched = False
            match_detail = ""

            if etype == "service" and value in service:
                matched = True
                match_detail = f"Service '{port['service']}' on port {port['port']} matches watchlist entry '{entry['value']}'"

            elif etype == "keyword" and value in service:
                matched = True
                match_detail = f"Keyword '{entry['value']}' found in service '{port['service']}' on port {port['port']}"

            elif etype == "cve":
                # CVE matching — check if service is in known affected services for common CVEs
                cve_service_map = {
                    "CVE-2017-0144": ["smb", "microsoft-ds", "netbios"],
                    "CVE-2019-0708": ["rdp", "ms-wbt-server"],
                    "CVE-2021-44228": ["http", "https", "java"],
                    "CVE-2022-26134": ["http", "confluence"],
                    "CVE-2023-44487": ["http", "https"],
                }
                affected = cve_service_map.get(value.upper(), [])
                if any(s in service for s in affected):
                    matched = True
                    match_detail = f"CVE {entry['value']} potentially affects '{port['service']}' on port {port['port']}"

            if matched:
                rec = get_recommendation(port["service"], entry["value"] if etype == "cve" else "")
                try:
                    cur2.execute("""
                        INSERT INTO watchlist_alerts
                        (entry_id, asset_id, asset_ip, port, service, match_type, detail, severity, recommendation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        entry["id"], port["asset_id"], port["ip"],
                        port["port"], port["service"], etype,
                        match_detail, entry["severity"], rec
                    ))
                    alert_id = cur2.fetchone()[0]
                    new_alerts.append({
                        "id": alert_id,
                        "asset_ip": port["ip"],
                        "port": port["port"],
                        "service": port["service"],
                        "detail": match_detail,
                        "severity": entry["severity"],
                        "recommendation": rec,
                        "entry_value": entry["value"]
                    })
                except Exception:
                    pass

        # Update last checked
        cur2.execute("UPDATE watchlist_entries SET last_checked=NOW(), hit_count=hit_count+%s WHERE id=%s",
                     (sum(1 for a in new_alerts if True), entry["id"]))

    conn.commit()
    conn.close()

    return {
        "status": "complete",
        "new_alerts": len(new_alerts),
        "alerts": new_alerts
    }

# ── Stats ─────────────────────────────────────────────────────────
@app.get("/stats")
def get_stats():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM watchlist_entries WHERE active=TRUE")
    entries = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as total FROM watchlist_alerts WHERE acknowledged=FALSE")
    unacked = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as total FROM watchlist_alerts")
    total_alerts = cur.fetchone()["total"]
    conn.close()
    return {"active_entries": entries, "unacknowledged_alerts": unacked, "total_alerts": total_alerts}

if __name__ == "__main__":
    uvicorn.run("watchlist_api:app", host="127.0.0.1", port=8098, reload=False)
