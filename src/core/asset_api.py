import os
import json
import re
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

app = FastAPI(title="NISA Asset Inventory API", version="1.0.0")

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

# ── Models ────────────────────────────────────────────────────────
class AssetUpdate(BaseModel):
    hostname: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None
    risk_level: Optional[str] = None

class IngestScan(BaseModel):
    target: Optional[str] = None
    ports: Optional[list[dict]] = []
    summary: Optional[str] = ""
    raw: Optional[str] = ""

# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "asset_api"}

# ── Asset CRUD ────────────────────────────────────────────────────
@app.get("/assets")
def list_assets():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT a.*,
               COUNT(DISTINCT ap.id) as port_count,
               COUNT(DISTINCT av.id) FILTER (WHERE av.resolved = FALSE) as vuln_count
        FROM assets a
        LEFT JOIN asset_ports ap ON ap.asset_id = a.id
        LEFT JOIN asset_vulns av ON av.asset_id = a.id
        GROUP BY a.id
        ORDER BY a.last_seen DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return {"assets": [dict(r) for r in rows]}

@app.get("/assets/{asset_id}")
def get_asset(asset_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM assets WHERE id=%s", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        conn.close()
        raise HTTPException(status_code=404, detail="Asset not found")
    cur.execute("SELECT * FROM asset_ports WHERE asset_id=%s ORDER BY port", (asset_id,))
    ports = cur.fetchall()
    cur.execute("SELECT * FROM asset_vulns WHERE asset_id=%s ORDER BY severity DESC, first_detected DESC", (asset_id,))
    vulns = cur.fetchall()
    cur.execute("SELECT * FROM asset_risk_history WHERE asset_id=%s ORDER BY recorded_at DESC LIMIT 30", (asset_id,))
    history = cur.fetchall()
    conn.close()
    return {
        **dict(asset),
        "ports": [dict(p) for p in ports],
        "vulns": [dict(v) for v in vulns],
        "risk_history": [dict(h) for h in history]
    }

@app.put("/assets/{asset_id}")
def update_asset(asset_id: int, update: AssetUpdate):
    conn = get_conn()
    cur = conn.cursor()
    if update.hostname is not None:
        cur.execute("UPDATE assets SET hostname=%s WHERE id=%s", (update.hostname, asset_id))
    if update.notes is not None:
        cur.execute("UPDATE assets SET notes=%s WHERE id=%s", (update.notes, asset_id))
    if update.tags is not None:
        cur.execute("UPDATE assets SET tags=%s WHERE id=%s", (update.tags, asset_id))
    if update.risk_level is not None:
        cur.execute("UPDATE assets SET risk_level=%s WHERE id=%s", (update.risk_level, asset_id))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.delete("/assets/{asset_id}")
def delete_asset(asset_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM assets WHERE id=%s", (asset_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# ── Scan Ingestion ────────────────────────────────────────────────
def calculate_risk(ports: list) -> str:
    if not ports:
        return "low"
    services = [p.get("service", "").lower() for p in ports]
    critical_services = ["rdp", "ms-wbt-server", "vnc", "telnet", "ftp"]
    high_services = ["ssh", "smb", "netbios", "msrpc", "mssql", "mysql", "postgres"]
    if any(s in critical_services for s in services):
        return "critical"
    if any(s in high_services for s in services):
        return "high"
    if len(ports) > 10:
        return "medium"
    return "low"

@app.post("/assets/ingest")
def ingest_scan(scan: IngestScan):
    if not scan.target:
        return {"status": "skipped", "reason": "no target"}

    ip = scan.target.strip()
    ports = scan.ports or []
    risk = calculate_risk(ports)

    conn = get_conn()
    cur = conn.cursor()

    # Upsert asset
    cur.execute("""
        INSERT INTO assets (ip, risk_level, last_seen, scan_count)
        VALUES (%s, %s, NOW(), 1)
        ON CONFLICT (ip) DO UPDATE SET
            risk_level = EXCLUDED.risk_level,
            last_seen = NOW(),
            scan_count = assets.scan_count + 1
        RETURNING id
    """, (ip, risk))
    asset_id = cur.fetchone()[0]

    # Upsert ports
    for p in ports:
        port_num = p.get("port") or p.get("port_number")
        if not port_num:
            continue
        try:
            port_int = int(str(port_num).split("/")[0])
        except:
            continue
        service = p.get("service", "unknown")
        version = p.get("version", "")
        cur.execute("""
            INSERT INTO asset_ports (asset_id, port, service, version, last_seen)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (asset_id, port, protocol) DO UPDATE SET
                service = EXCLUDED.service,
                version = EXCLUDED.version,
                last_seen = NOW()
        """, (asset_id, port_int, service, version))

    # Record risk history
    cur.execute("""
        INSERT INTO asset_risk_history (asset_id, risk_level, open_ports)
        VALUES (%s, %s, %s)
    """, (asset_id, risk, len(ports)))

    conn.commit()
    conn.close()

    return {
        "status": "ingested",
        "asset_id": asset_id,
        "ip": ip,
        "risk": risk,
        "ports_ingested": len(ports)
    }

# ── Bulk ingest from nmap result ──────────────────────────────────
@app.post("/assets/ingest/nmap")
def ingest_nmap(data: dict):
    results = []
    # Handle single host result
    if "target" in data:
        result = ingest_scan(IngestScan(
            target=data.get("target"),
            ports=data.get("ports", []),
            summary=data.get("summary", "")
        ))
        results.append(result)
    return {"status": "ok", "results": results, "count": len(results)}

# ── Stats ─────────────────────────────────────────────────────────
@app.get("/assets/stats/summary")
def get_stats():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(*) as total FROM assets")
    total = cur.fetchone()["total"]
    cur.execute("SELECT risk_level, COUNT(*) as count FROM assets GROUP BY risk_level")
    by_risk = {r["risk_level"]: r["count"] for r in cur.fetchall()}
    cur.execute("SELECT COUNT(*) as total FROM asset_ports")
    total_ports = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as total FROM asset_vulns WHERE resolved=FALSE")
    open_vulns = cur.fetchone()["total"]
    conn.close()
    return {
        "total_assets": total,
        "by_risk": by_risk,
        "total_ports": total_ports,
        "open_vulns": open_vulns
    }

if __name__ == "__main__":
    uvicorn.run("asset_api:app", host="127.0.0.1", port=8097, reload=False)
