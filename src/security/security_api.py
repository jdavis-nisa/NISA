import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
from fastapi import HTTPException, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import subprocess
import hashlib
import hmac
import time
import uuid
import urllib.request
import urllib.parse
import json
from openai import OpenAI

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="NISA Security API", version="0.2.0")

# ── API Key Authentication ────────────────────────────────────────
NISA_API_KEY = os.environ.get("NISA_API_KEY", "")

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/waveform_types") or request.method == "OPTIONS":
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

# ── RedSage LLM Client ───────────────────────────────────────────
llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def redsage_analyze(context: str, data: str) -> str:
    """Route security analysis through RedSage 8B specialist model"""
    try:
        completion = llm.chat.completions.create(
            model="redsage-qwen3-8b-dpo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are RedSage, a cybersecurity specialist. "
                        "Analyze the provided security scan data concisely. "
                        "Identify risks, notable findings, and recommended actions. "
                        "Be direct and technical. Keep response under 200 words."
                    )
                },
                {
                    "role": "user",
                    "content": f"{context}\n\nScan Data:\n{data}"
                }
            ],
            max_tokens=300,
            temperature=0.2
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"RedSage analysis unavailable: {str(e)}"

# ── JIT Token Store ──────────────────────────────────────────────
active_tokens = {}
SECRET = "nisa_jit_secret_2026"

def generate_jit_token(tool: str) -> str:
    token = str(uuid.uuid4())
    active_tokens[token] = {
        "tool": tool,
        "expires": time.time() + 60
    }
    return token

def validate_jit_token(token: str, tool: str) -> bool:
    if token not in active_tokens:
        return False
    entry = active_tokens[token]
    if entry["tool"] != tool:
        return False
    if time.time() > entry["expires"]:
        del active_tokens[token]
        return False
    del active_tokens[token]
    return True

# ── ZAP Helper ───────────────────────────────────────────────────
ZAP_KEY = "nisa_zap_key_2026"

def zap_get(path: str, params: dict = {}) -> dict:
    """Call ZAP API via docker exec — avoids proxy loop issue"""
    params["apikey"] = ZAP_KEY
    query = urllib.parse.urlencode(params)
    url = f"http://localhost:8080{path}?{query}"
    result = subprocess.run(
        ["docker", "exec", "nisa_zap", "curl", "-s", url],
        capture_output=True, text=True, timeout=30
    )
    if not result.stdout.strip():
        raise Exception(f"ZAP returned empty response for {path}")
    return json.loads(result.stdout)

# ── Models ───────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    target: str
    scan_type: Optional[str] = "basic"

class TokenRequest(BaseModel):
    tool: str

class TokenResponse(BaseModel):
    token: str
    tool: str
    expires_in: int

class ScanResponse(BaseModel):
    target: str
    results: str
    ports: list
    summary: str
    analysis: str = ""

class ZapScanRequest(BaseModel):
    target: str

class ZapScanResponse(BaseModel):
    target: str
    alerts: list
    risk_counts: dict
    total_alerts: int
    summary: str
    analysis: str = ""

# ── Endpoints ────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Security API v0.2.0"}

@app.post("/token", response_model=TokenResponse)
def request_token(req: TokenRequest):
    """Request a JIT token for tool execution — expires in 60 seconds"""
    allowed_tools = ["nmap", "zap"]
    if req.tool not in allowed_tools:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {req.tool}")
    token = generate_jit_token(req.tool)
    return TokenResponse(token=token, tool=req.tool, expires_in=60)

@app.post("/scan/nmap", response_model=ScanResponse)
def nmap_scan(req: ScanRequest, token: str):
    """Run Nmap scan — requires valid JIT token"""
    if not validate_jit_token(token, "nmap"):
        raise HTTPException(status_code=401,
            detail="Invalid or expired JIT token")

    safe_targets = ["localhost", "127.0.0.1", "192.168.", "10.", "172."]
    if not any(req.target.startswith(t) for t in safe_targets):
        raise HTTPException(status_code=403,
            detail="Target must be localhost or private network")

    try:
        flags = ["-sV", "--open"]
        if req.scan_type == "quick":
            flags = ["-F", "--open"]
        elif req.scan_type == "deep":
            flags = ["-sV", "-sC", "--open"]

        result = subprocess.run(
            ["docker", "exec", "nisa_nmap", "nmap"] + flags + [req.target],
            capture_output=True, text=True, timeout=120
        )

        output = result.stdout
        ports = []
        for line in output.split("\n"):
            if "/tcp" in line and "open" in line:
                parts = line.strip().split()
                if len(parts) >= 3:
                    ports.append({
                        "port": parts[0],
                        "state": parts[1],
                        "service": parts[2]
                    })

        summary = f"Scan of {req.target} complete. Found {len(ports)} open ports."
        analysis = redsage_analyze(
            f"Nmap scan of {req.target} ({req.scan_type})",
            f"Open ports: {ports}\n\nFull output:\n{output[:1000]}"
        )
        return ScanResponse(target=req.target, results=output, ports=ports,
                           summary=summary, analysis=analysis)

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Scan timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scan/zap", response_model=ZapScanResponse)
def zap_scan(req: ZapScanRequest, token: str):
    """Run OWASP ZAP web vulnerability scan — requires valid JIT token"""
    if not validate_jit_token(token, "zap"):
        raise HTTPException(status_code=401,
            detail="Invalid or expired JIT token")

    target = req.target
    if not target.startswith("http"):
        raise HTTPException(status_code=400,
            detail="Target must be a full URL — e.g. http://localhost")

    # Remap localhost to host.docker.internal so ZAP container can reach Mac
    zap_target = target.replace("http://localhost", "http://host.docker.internal") \
                       .replace("https://localhost", "https://host.docker.internal")

    try:
        # Step 1 — Spider crawl to discover URLs
        spider = zap_get("/JSON/spider/action/scan/", {"url": zap_target, "maxChildren": "5"})
        spider_id = spider.get("scan", "0")

        # Poll spider until complete (max 60s)
        for _ in range(12):
            time.sleep(5)
            progress = zap_get("/JSON/spider/view/status/", {"scanId": spider_id})
            if progress.get("status") == "100":
                break

        # Step 2 — Retrieve passive scan alerts (no active scan needed)
        alerts_raw = zap_get("/JSON/core/view/alerts/", {"baseurl": zap_target})
        alerts = alerts_raw.get("alerts", [])

        # Count by risk level
        risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
        clean_alerts = []
        for a in alerts:
            risk = a.get("risk", "Informational")
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
            clean_alerts.append({
                "name": a.get("name"),
                "risk": risk,
                "url": a.get("url"),
                "description": a.get("description", "")[:200]
            })

        total = len(clean_alerts)
        summary = (
            f"ZAP scan of {target} complete. "
            f"{total} alerts found — "
            f"High: {risk_counts['High']}, "
            f"Medium: {risk_counts['Medium']}, "
            f"Low: {risk_counts['Low']}, "
            f"Info: {risk_counts['Informational']}."
        )

        analysis = redsage_analyze(
            f"OWASP ZAP scan of {target}",
            f"Risk counts: {risk_counts}\nAlerts: {clean_alerts[:5]}"
        )
        return ZapScanResponse(
            target=target,
            alerts=clean_alerts,
            risk_counts=risk_counts,
            total_alerts=total,
            summary=summary,
            analysis=analysis
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ZAP scan failed: {str(e)}")

@app.get("/containers")
def list_containers():
    """List running security containers"""
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=nisa_",
         "--format", "{{.Names}}: {{.Status}}"],
        capture_output=True, text=True
    )
    containers = [l for l in result.stdout.strip().split("\n") if l]
    return {"containers": containers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8082)
