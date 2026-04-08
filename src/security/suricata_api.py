from fastapi import HTTPException, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess
import json
import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
import time
import threading
from datetime import datetime
from openai import OpenAI

app = FastAPI(title="NISA Suricata IDS API", version="0.1.0")

# ── API Key Authentication ────────────────────────────────────────
NISA_API_KEY = os.environ.get("NISA_API_KEY", "")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/waveform_types"):
        return await call_next(request)
    if NISA_API_KEY:
        key = request.headers.get("X-NISA-API-Key", "")
        if key != NISA_API_KEY:
            return JSONResponse(status_code=403, content={"error": "Invalid or missing API key"})
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
ALERT_LOG = "/tmp/nisa_suricata_alerts.json"
SURICATA_LOG_DIR = "/tmp/nisa_suricata"
_alerts = []
_suricata_pid = None

def redsage_analyze(alerts: list) -> str:
    try:
        completion = llm.chat.completions.create(
            model="redsage-qwen3-8b-dpo",
            messages=[
                {"role": "system", "content": "You are RedSage, a network security specialist. Analyze these IDS alerts concisely. Identify attack patterns, severity, and recommended actions. Under 200 words."},
                {"role": "user", "content": f"Suricata IDS Alerts: {json.dumps(alerts[:10])}"}
            ],
            max_tokens=300,
            temperature=0.2
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"RedSage unavailable: {str(e)}"

def parse_eve_log(log_path: str) -> list:
    alerts = []
    if not os.path.exists(log_path):
        return alerts
    try:
        with open(log_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event.get("event_type") == "alert":
                        alerts.append({
                            "timestamp": event.get("timestamp"),
                            "src_ip": event.get("src_ip"),
                            "dest_ip": event.get("dest_ip"),
                            "proto": event.get("proto"),
                            "severity": event.get("alert", {}).get("severity"),
                            "signature": event.get("alert", {}).get("signature"),
                            "category": event.get("alert", {}).get("category"),
                            "action": event.get("alert", {}).get("action"),
                        })
                except Exception:
                    continue
    except Exception:
        pass
    return alerts

@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Suricata IDS API v0.1.0"}

@app.post("/start")
def start_suricata(interface: str = "en0"):
    global _suricata_pid
    os.makedirs(SURICATA_LOG_DIR, exist_ok=True)
    eve_log = os.path.join(SURICATA_LOG_DIR, "eve.json")
    if os.path.exists(eve_log):
        os.remove(eve_log)
    try:
        proc = subprocess.Popen([
            "sudo", "suricata",
            "-c", "/opt/homebrew/etc/suricata/suricata.yaml",
            "-i", interface,
            "-l", SURICATA_LOG_DIR,
            "--set", "outputs.1.eve-log.filename=eve.json"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _suricata_pid = proc.pid
        return {"status": "started", "pid": _suricata_pid, "interface": interface, "log_dir": SURICATA_LOG_DIR}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stop")
def stop_suricata():
    global _suricata_pid
    try:
        subprocess.run(["sudo", "pkill", "-f", "suricata"], capture_output=True)
        _suricata_pid = None
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
def get_alerts(limit: int = 50, analyze: bool = False):
    eve_log = os.path.join(SURICATA_LOG_DIR, "eve.json")
    alerts = parse_eve_log(eve_log)
    alerts = alerts[-limit:]
    result = {
        "total": len(alerts),
        "alerts": alerts,
        "log_path": eve_log,
    }
    if analyze and alerts:
        result["analysis"] = redsage_analyze(alerts)
    elif analyze:
        result["analysis"] = "No alerts to analyze."
    return result

@app.get("/status")
def get_status():
    running = False
    if _suricata_pid:
        try:
            os.kill(_suricata_pid, 0)
            running = True
        except OSError:
            running = False
    eve_log = os.path.join(SURICATA_LOG_DIR, "eve.json")
    alerts = parse_eve_log(eve_log)
    return {
        "running": running,
        "pid": _suricata_pid,
        "total_alerts": len(alerts),
        "log_dir": SURICATA_LOG_DIR,
        "rules_loaded": 49494
    }

@app.post("/test")
def test_detection():
    eve_log = os.path.join(SURICATA_LOG_DIR, "eve.json")
    os.makedirs(SURICATA_LOG_DIR, exist_ok=True)
    test_alert = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "alert",
        "src_ip": "192.168.1.100",
        "dest_ip": "10.0.0.1",
        "proto": "TCP",
        "alert": {
            "severity": 1,
            "signature": "ET SCAN Nmap SYN Scan",
            "category": "Attempted Information Leak",
            "action": "allowed"
        }
    }
    with open(eve_log, "a") as f:
        f.write(json.dumps(test_alert) + "\n")
    return {"status": "test alert written", "alert": test_alert}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8085)
