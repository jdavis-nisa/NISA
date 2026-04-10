import os
import json
import asyncio
import httpx
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
from datetime import datetime, timedelta

app = FastAPI(title="NISA Continuous Monitoring API", version="1.0.0")

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

# ── Monitoring state ──────────────────────────────────────────────
monitor_task = None
monitoring_active = False

# ── Models ────────────────────────────────────────────────────────
class MonitoringUpdate(BaseModel):
    enabled: Optional[bool] = None
    interval_minutes: Optional[int] = None
    targets: Optional[list[str]] = None
    use_asset_inventory: Optional[bool] = None
    scan_type: Optional[str] = None

# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "monitoring_api", "monitoring_active": monitoring_active}

# ── Config ────────────────────────────────────────────────────────
@app.get("/monitoring/config")
def get_config():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM monitoring_config ORDER BY id LIMIT 1")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}

@app.put("/monitoring/config")
def update_config(update: MonitoringUpdate):
    conn = get_conn()
    cur = conn.cursor()
    if update.enabled is not None:
        cur.execute("UPDATE monitoring_config SET enabled=%s, updated_at=NOW()", (update.enabled,))
    if update.interval_minutes is not None:
        cur.execute("UPDATE monitoring_config SET interval_minutes=%s, updated_at=NOW()", (update.interval_minutes,))
    if update.targets is not None:
        cur.execute("UPDATE monitoring_config SET targets=%s, updated_at=NOW()", (update.targets,))
    if update.use_asset_inventory is not None:
        cur.execute("UPDATE monitoring_config SET use_asset_inventory=%s, updated_at=NOW()", (update.use_asset_inventory,))
    if update.scan_type is not None:
        cur.execute("UPDATE monitoring_config SET scan_type=%s, updated_at=NOW()", (update.scan_type,))
    conn.commit()
    conn.close()
    return {"status": "updated"}

# ── Deltas ────────────────────────────────────────────────────────
@app.get("/monitoring/deltas")
def get_deltas(limit: int = 50, unacked_only: bool = False):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if unacked_only:
        cur.execute("SELECT * FROM monitoring_deltas WHERE acknowledged=FALSE ORDER BY scan_at DESC LIMIT %s", (limit,))
    else:
        cur.execute("SELECT * FROM monitoring_deltas ORDER BY scan_at DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    conn.close()
    return {"deltas": [dict(r) for r in rows]}

@app.post("/monitoring/deltas/acknowledge")
def ack_deltas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE monitoring_deltas SET acknowledged=TRUE")
    conn.commit()
    conn.close()
    return {"status": "acknowledged"}

# ── Scan Engine ───────────────────────────────────────────────────
async def get_scan_targets(config: dict) -> list:
    targets = []
    if config.get("use_asset_inventory"):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    "http://127.0.0.1:8097/assets",
                    headers={"X-NISA-API-Key": NISA_API_KEY},
                    timeout=5.0
                )
                if res.status_code == 200:
                    assets = res.json().get("assets", [])
                    targets = [a["ip"] for a in assets]
        except Exception as e:
            print(f"[Monitoring] Failed to fetch assets: {e}")
    manual = config.get("targets") or []
    for t in manual:
        if t and t not in targets:
            targets.append(t)
    return targets if targets else ["127.0.0.1"]

async def run_nmap_scan(target: str, scan_type: str) -> dict:
    try:
        async with httpx.AsyncClient() as client:
            headers = {"X-NISA-API-Key": NISA_API_KEY, "Content-Type": "application/json"}
            tr = await client.post("http://127.0.0.1:8082/token",
                                   json={"tool": "nmap"}, headers=headers, timeout=10)
            token = tr.json()["token"]
            res = await client.post(
                f"http://127.0.0.1:8082/scan/nmap?token={token}",
                json={"target": target, "scan_type": scan_type},
                headers=headers, timeout=120
            )
            return res.json()
    except Exception as e:
        print(f"[Monitoring] Scan failed for {target}: {e}")
        return {}

def get_previous_ports(ip: str, conn) -> set:
    cur = conn.cursor()
    cur.execute("""
        SELECT ap.port FROM asset_ports ap
        JOIN assets a ON a.id = ap.asset_id
        WHERE a.ip = %s
    """, (ip,))
    return {r[0] for r in cur.fetchall()}

def detect_deltas(ip: str, new_ports: list, prev_ports: set, conn) -> list:
    deltas = []
    new_port_nums = {p.get("port") or p.get("port_number") for p in new_ports if p.get("port") or p.get("port_number")}

    # New ports opened
    for port_data in new_ports:
        pnum = port_data.get("port") or port_data.get("port_number")
        if not pnum:
            continue
        try:
            pnum = int(str(pnum).split("/")[0])
        except:
            continue
        if pnum not in prev_ports:
            service = port_data.get("service", "unknown")
            critical_svcs = ["rdp", "telnet", "vnc", "ms-wbt-server"]
            high_svcs = ["smb", "ftp", "ssh", "mssql", "mysql"]
            sev = "critical" if any(s in service.lower() for s in critical_svcs) else \
                  "high" if any(s in service.lower() for s in high_svcs) else "medium"
            deltas.append({
                "asset_ip": ip, "delta_type": "new_port",
                "detail": f"New port opened: {pnum}/{service} on {ip}",
                "severity": sev
            })

    # Ports closed
    for prev_port in prev_ports:
        if prev_port not in new_port_nums:
            deltas.append({
                "asset_ip": ip, "delta_type": "port_closed",
                "detail": f"Port {prev_port} closed on {ip}",
                "severity": "info"
            })

    return deltas

async def run_monitoring_cycle():
    print(f"[Monitoring] Cycle starting at {datetime.now()}")
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM monitoring_config LIMIT 1")
    config = dict(cur.fetchone())
    conn.close()

    targets = await get_scan_targets(config)
    scan_type = config.get("scan_type", "quick")
    all_deltas = []

    for target in targets:
        print(f"[Monitoring] Scanning {target}...")
        scan_result = await run_nmap_scan(target, scan_type)
        if not scan_result:
            continue

        conn = get_conn()
        prev_ports = get_previous_ports(target, conn)
        new_ports = scan_result.get("ports", [])
        deltas = detect_deltas(target, new_ports, prev_ports, conn)

        # Check for new host
        cur2 = conn.cursor()
        cur2.execute("SELECT id FROM assets WHERE ip=%s", (target,))
        if not cur2.fetchone():
            deltas.append({
                "asset_ip": target, "delta_type": "new_host",
                "detail": f"New host discovered: {target}",
                "severity": "critical"
            })

        # Store deltas
        for delta in deltas:
            if delta["severity"] != "info":
                cur2.execute("""
                    INSERT INTO monitoring_deltas (asset_ip, delta_type, detail, severity)
                    VALUES (%s, %s, %s, %s)
                """, (delta["asset_ip"], delta["delta_type"], delta["detail"], delta["severity"]))

        # Ingest scan into asset inventory
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://127.0.0.1:8097/assets/ingest/nmap",
                    json=scan_result,
                    headers={"X-NISA-API-Key": NISA_API_KEY, "Content-Type": "application/json"},
                    timeout=10
                )
        except Exception:
            pass

        conn.commit()
        conn.close()
        all_deltas.extend([d for d in deltas if d["severity"] != "info"])

    # Update last_run and next_run
    conn = get_conn()
    cur = conn.cursor()
    interval = config.get("interval_minutes", 15)
    next_run = datetime.now() + timedelta(minutes=interval)
    cur.execute("UPDATE monitoring_config SET last_run=NOW(), next_run=%s", (next_run,))
    conn.commit()
    conn.close()

    print(f"[Monitoring] Cycle complete. {len(all_deltas)} deltas detected.")
    return all_deltas

async def monitoring_loop():
    global monitoring_active
    while monitoring_active:
        try:
            conn = get_conn()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("SELECT * FROM monitoring_config LIMIT 1")
            config = dict(cur.fetchone())
            conn.close()

            if not config.get("enabled"):
                monitoring_active = False
                break

            await run_monitoring_cycle()
            interval = config.get("interval_minutes", 15)
            print(f"[Monitoring] Next scan in {interval} minutes")
            await asyncio.sleep(interval * 60)

        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Monitoring] Loop error: {e}")
            await asyncio.sleep(60)

    monitoring_active = False
    print("[Monitoring] Loop stopped")

# ── Toggle ────────────────────────────────────────────────────────
@app.post("/monitoring/start")
async def start_monitoring():
    global monitor_task, monitoring_active
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE monitoring_config SET enabled=TRUE, updated_at=NOW()")
    conn.commit()
    conn.close()
    if not monitoring_active:
        monitoring_active = True
        monitor_task = asyncio.create_task(monitoring_loop())
        return {"status": "started", "message": "Continuous monitoring active"}
    return {"status": "already_running"}

@app.post("/monitoring/stop")
async def stop_monitoring():
    global monitor_task, monitoring_active
    monitoring_active = False
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE monitoring_config SET enabled=FALSE, updated_at=NOW()")
    conn.commit()
    conn.close()
    if monitor_task:
        monitor_task.cancel()
        monitor_task = None
    return {"status": "stopped", "message": "Continuous monitoring stopped"}

@app.post("/monitoring/run_now")
async def run_now():
    deltas = await run_monitoring_cycle()
    return {"status": "complete", "deltas_found": len(deltas), "deltas": deltas}

@app.get("/monitoring/status")
def get_status():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM monitoring_config LIMIT 1")
    config = dict(cur.fetchone())
    cur.execute("SELECT COUNT(*) as total FROM monitoring_deltas WHERE acknowledged=FALSE")
    unacked = cur.fetchone()["total"]
    conn.close()
    return {
        "enabled": config.get("enabled", False),
        "monitoring_active": monitoring_active,
        "interval_minutes": config.get("interval_minutes", 15),
        "last_run": str(config.get("last_run")) if config.get("last_run") else None,
        "next_run": str(config.get("next_run")) if config.get("next_run") else None,
        "unacked_deltas": unacked,
        "scan_type": config.get("scan_type", "quick"),
        "use_asset_inventory": config.get("use_asset_inventory", True)
    }

if __name__ == "__main__":
    uvicorn.run("monitoring_api:app", host="127.0.0.1", port=8099, reload=False)
