from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import hashlib
import hmac
import time
import uuid

app = FastAPI(title="NISA Security API", version="0.1.0")

# ── JIT Token Store ──────────────────────────────────────────────
# Just-in-Time permissions — tokens expire in 60 seconds
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
    del active_tokens[token]  # one-time use
    return True

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

# ── Endpoints ────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Security API v0.1.0"}

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

    # Safety check — only allow local/private targets
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
            capture_output=True,
            text=True,
            timeout=120
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

        return ScanResponse(
            target=req.target,
            results=output,
            ports=ports,
            summary=summary
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Scan timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    uvicorn.run(app, host="0.0.0.0", port=8082)
