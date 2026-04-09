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
from typing import Optional, Any
import uvicorn
import psycopg2
import psycopg2.extras
from datetime import datetime

app = FastAPI(title="NISA Playbook API", version="1.0.0")

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
class PlaybookStep(BaseModel):
    id: str
    name: str
    operation: str
    params: dict = {}
    condition: str = "always"  # always | on_success | on_finding

class PlaybookCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    steps: list[PlaybookStep] = []

class PlaybookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[list[PlaybookStep]] = None

# ── Health ────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "playbook_api"}

# ── CRUD ─────────────────────────────────────────────────────────
@app.get("/playbooks")
def list_playbooks():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, name, description, steps, created_at, updated_at, run_count, last_run FROM playbooks ORDER BY updated_at DESC")
    rows = cur.fetchall()
    conn.close()
    return {"playbooks": [dict(r) for r in rows]}

@app.post("/playbooks")
def create_playbook(pb: PlaybookCreate):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO playbooks (name, description, steps) VALUES (%s, %s, %s) RETURNING id",
        (pb.name, pb.description, json.dumps([s.dict() for s in pb.steps]))
    )
    pid = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": pid, "status": "created"}

@app.get("/playbooks/{pid}")
def get_playbook(pid: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM playbooks WHERE id=%s", (pid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return dict(row)

@app.put("/playbooks/{pid}")
def update_playbook(pid: int, pb: PlaybookUpdate):
    conn = get_conn()
    cur = conn.cursor()
    if pb.name:
        cur.execute("UPDATE playbooks SET name=%s, updated_at=NOW() WHERE id=%s", (pb.name, pid))
    if pb.description is not None:
        cur.execute("UPDATE playbooks SET description=%s, updated_at=NOW() WHERE id=%s", (pb.description, pid))
    if pb.steps is not None:
        cur.execute("UPDATE playbooks SET steps=%s, updated_at=NOW() WHERE id=%s",
                    (json.dumps([s.dict() for s in pb.steps]), pid))
    conn.commit()
    conn.close()
    return {"status": "updated"}

@app.delete("/playbooks/{pid}")
def delete_playbook(pid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM playbooks WHERE id=%s", (pid,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

# ── Execution Engine ──────────────────────────────────────────────
API_ENDPOINTS = {
    "nmap_scan":         ("http://127.0.0.1:8082", "POST", "/scan/nmap"),
    "zap_scan":          ("http://127.0.0.1:8082", "POST", "/scan/zap"),
    "suricata_check":    ("http://127.0.0.1:8085", "GET",  "/alerts"),
    "log_analysis":      ("http://127.0.0.1:8083", "POST", "/analyze/logs"),
    "cve_lookup":        ("http://127.0.0.1:8093", "POST", "/cve/search"),
    "adversarial_sim":   ("http://127.0.0.1:8094", "POST", "/simulate"),
    "compliance_report": ("http://127.0.0.1:8086", "POST", "/compliance/generate"),
    "nisaba_query":      ("http://127.0.0.1:8081", "POST", "/chat"),
}

def check_condition(condition: str, prev_result: dict) -> bool:
    if condition == "always":
        return True
    if condition == "on_success":
        return prev_result.get("status") == "success"
    if condition == "on_finding":
        r = prev_result.get("result", {})
        ports = r.get("ports", [])
        findings = r.get("findings", [])
        alerts = r.get("alerts", [])
        return len(ports) > 0 or len(findings) > 0 or len(alerts) > 0
    return True

async def execute_step(step: dict, prev_result: dict, token_client: httpx.AsyncClient) -> dict:
    op = step["operation"]
    params = step.get("params", {})
    headers = {"X-NISA-API-Key": NISA_API_KEY, "Content-Type": "application/json"}

    try:
        if op == "nmap_scan":
            # Get JIT token first
            tr = await token_client.post("http://127.0.0.1:8082/token",
                                          json={"tool": "nmap"}, headers=headers, timeout=10)
            token = tr.json()["token"]
            r = await token_client.post(f"http://127.0.0.1:8082/scan/nmap?token={token}",
                                         json={"target": params.get("target", "127.0.0.1"),
                                               "scan_type": params.get("scan_type", "quick")},
                                         headers=headers, timeout=120)
            data = r.json()
            finding = len(data.get("ports", [])) > 0
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Nmap: {data.get('target')} - {len(data.get('ports',[]))} open ports",
                    "has_finding": finding}

        elif op == "zap_scan":
            tr = await token_client.post("http://127.0.0.1:8082/token",
                                          json={"tool": "zap"}, headers=headers, timeout=10)
            token = tr.json()["token"]
            r = await token_client.post(f"http://127.0.0.1:8082/scan/zap?token={token}",
                                         json={"target": params.get("target", "http://localhost")},
                                         headers=headers, timeout=180)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"ZAP: {len(data.get('alerts',[]))} alerts found",
                    "has_finding": len(data.get("alerts", [])) > 0}

        elif op == "adversarial_sim":
            r = await token_client.post("http://127.0.0.1:8094/simulate",
                                         json={"threat_actor": params.get("threat_actor", "APT28"),
                                               "network_context": params.get("network_context", "enterprise"),
                                               "simulation_depth": "standard"},
                                         headers=headers, timeout=300)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Adversarial: {params.get('threat_actor','APT28')} - {len(data.get('steps',[]))} steps",
                    "has_finding": True}

        elif op == "nisaba_query":
            r = await token_client.post("http://127.0.0.1:8081/chat",
                                         json={"message": params.get("message", "Summarize the current session findings."),
                                               "temperature": 0.3, "max_tokens": 500},
                                         headers=headers, timeout=60)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Nisaba: {data.get('response','')[:120]}...",
                    "has_finding": False}

        elif op == "cve_lookup":
            r = await token_client.post("http://127.0.0.1:8093/cve/search",
                                         json={"query": params.get("query", ""), "limit": 10},
                                         headers=headers, timeout=30)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"CVE: {len(data.get('results',[]))} results for '{params.get('query','')}'",
                    "has_finding": len(data.get("results", [])) > 0}

        elif op == "compliance_report":
            r = await token_client.post("http://127.0.0.1:8086/compliance/generate",
                                         json={}, headers=headers, timeout=60)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Compliance report generated",
                    "has_finding": False}

        elif op == "suricata_check":
            r = await token_client.get("http://127.0.0.1:8085/alerts",
                                        headers=headers, timeout=30)
            data = r.json()
            alerts = data.get("alerts", [])
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Suricata: {len(alerts)} active alerts",
                    "has_finding": len(alerts) > 0}

        elif op == "log_analysis":
            r = await token_client.post("http://127.0.0.1:8083/analyze/logs",
                                         json={"log_text": params.get("log_text", ""),
                                               "log_type": params.get("log_type", "syslog")},
                                         headers=headers, timeout=60)
            data = r.json()
            return {"status": "success", "operation": op, "result": data,
                    "summary": f"Log analysis: {data.get('summary', 'complete')}",
                    "has_finding": False}

        else:
            return {"status": "skipped", "operation": op,
                    "summary": f"Unknown operation: {op}", "has_finding": False}

    except Exception as e:
        return {"status": "error", "operation": op,
                "summary": f"Error: {str(e)}", "has_finding": False, "error": str(e)}

@app.post("/playbooks/{pid}/run")
async def run_playbook(pid: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM playbooks WHERE id=%s", (pid,))
    pb = cur.fetchone()
    if not pb:
        conn.close()
        raise HTTPException(status_code=404, detail="Playbook not found")

    steps = pb["steps"] if isinstance(pb["steps"], list) else json.loads(pb["steps"])

    # Create run record
    cur2 = conn.cursor()
    cur2.execute(
        "INSERT INTO playbook_runs (playbook_id, status) VALUES (%s, 'running') RETURNING id",
        (pid,)
    )
    run_id = cur2.fetchone()[0]
    cur2.execute("UPDATE playbooks SET run_count=run_count+1, last_run=NOW() WHERE id=%s", (pid,))
    conn.commit()
    conn.close()

    # Execute steps
    step_results = []
    prev_result = {"status": "success", "has_finding": False}

    async with httpx.AsyncClient() as client:
        for step in steps:
            should_run = check_condition(step.get("condition", "always"), prev_result)
            if not should_run:
                result = {"status": "skipped", "operation": step["operation"],
                          "summary": f"Skipped: condition '{step['condition']}' not met",
                          "has_finding": False}
            else:
                result = await execute_step(step, prev_result, client)

            result["step_id"] = step["id"]
            result["step_name"] = step["name"]
            step_results.append(result)
            prev_result = result

    # Update run record
    conn = get_conn()
    cur = conn.cursor()
    all_success = all(r["status"] in ("success", "skipped") for r in step_results)
    final_status = "completed" if all_success else "completed_with_errors"
    cur.execute(
        "UPDATE playbook_runs SET status=%s, completed_at=NOW(), step_results=%s WHERE id=%s",
        (final_status, json.dumps(step_results, default=str), run_id)
    )
    conn.commit()
    conn.close()

    return {
        "run_id": run_id,
        "playbook_id": pid,
        "status": final_status,
        "steps_total": len(steps),
        "steps_success": sum(1 for r in step_results if r["status"] == "success"),
        "step_results": step_results
    }

@app.get("/playbooks/{pid}/runs")
def get_runs(pid: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM playbook_runs WHERE playbook_id=%s ORDER BY started_at DESC LIMIT 20", (pid,))
    rows = cur.fetchall()
    conn.close()
    return {"runs": [dict(r) for r in rows]}

@app.get("/runs/{run_id}")
def get_run(run_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM playbook_runs WHERE id=%s", (run_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return dict(row)

if __name__ == "__main__":
    uvicorn.run("playbook_api:app", host="127.0.0.1", port=8096, reload=False)
