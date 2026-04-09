#!/usr/bin/env python3.11
"""
NISA Metasploit API - Port 8089
Interfaces with Metasploit Framework inside Kali Linux Docker container
"""
import os
import json
import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))

app = FastAPI(title="NISA Metasploit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")
KALI_CONTAINER = "kali_nisa"

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health",) or request.method == "OPTIONS":
        return await call_next(request)
    if NISA_API_KEY:
        key = request.headers.get("X-NISA-API-Key", "")
        if key != NISA_API_KEY:
            return JSONResponse(status_code=403, content={"error": "Invalid or missing API key"})
    return await call_next(request)

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20

class ModuleInfoRequest(BaseModel):
    module_path: str

class ExploitRequest(BaseModel):
    module_path: str
    options: dict = {}
    dry_run: bool = True

def run_msf_command(commands: list, timeout: int = 30) -> dict:
    rc_script = "\n".join(commands) + "\nexit\n"
    cmd = [
        "docker", "exec", "-i", KALI_CONTAINER,
        "msfconsole", "-q", "-x", ";".join(commands + ["exit"])
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1}

def run_msfrpc_search(query: str, limit: int = 20) -> list:
    cmd = [
        "docker", "exec", KALI_CONTAINER,
        "msfconsole", "-q", "-x",
        f"search {query};exit"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        modules = []
        lines = result.stdout.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Match lines like: 0   exploit/windows/smb/ms17_010_eternalblue  2017-03-14  average  Yes  Description
            parts = line.split()
            if len(parts) < 4:
                continue
            # First token should be a number index
            if not parts[0].isdigit():
                continue
            # Second token should contain a /
            if "/" not in parts[1]:
                continue
            # Skip sub-target lines (indented with backslash)
            if "\\" in parts[1] or parts[1].startswith("_"):
                continue
            name = parts[1]
            date = parts[2] if len(parts) > 2 else ""
            rank = parts[3] if len(parts) > 3 else ""
            desc = " ".join(parts[5:]) if len(parts) > 5 else ""
            modules.append({
                "name": name,
                "disclosure_date": date,
                "rank": rank,
                "description": desc,
            })
            if len(modules) >= limit:
                break
        return modules
    except Exception as e:
        return []

@app.get("/health")
def health():
    try:
        result = subprocess.run(
            ["docker", "exec", KALI_CONTAINER, "msfconsole", "--version"],
            capture_output=True, text=True, timeout=10
        )
        msf_version = result.stdout.strip() if result.returncode == 0 else "unknown"
        return {
            "status": "online",
            "service": "metasploit_api",
            "port": 8089,
            "container": KALI_CONTAINER,
            "metasploit": msf_version
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

@app.post("/search")
def search_modules(req: SearchRequest):
    try:
        modules = run_msfrpc_search(req.query, req.limit)
        return {
            "query": req.query,
            "count": len(modules),
            "modules": modules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/info")
def module_info(req: ModuleInfoRequest):
    try:
        cmd = [
            "docker", "exec", KALI_CONTAINER,
            "msfconsole", "-q", "-x",
            f"use {req.module_path};info;exit"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "module": req.module_path,
            "info": result.stdout,
            "returncode": result.returncode
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/modules/categories")
def get_categories():
    return {
        "categories": [
            {"id": "exploit", "description": "Exploit modules - attack known vulnerabilities"},
            {"id": "auxiliary", "description": "Auxiliary modules - scanners, fuzzers, brute-forcers"},
            {"id": "post", "description": "Post-exploitation modules"},
            {"id": "payload", "description": "Payloads for delivery after exploitation"},
            {"id": "encoder", "description": "Encoders for payload obfuscation"},
            {"id": "nop", "description": "NOP generators"},
        ]
    }

@app.post("/search/cve")
def search_by_cve(req: SearchRequest):
    try:
        cve = req.query.upper().replace(" ", "-")
        if not cve.startswith("CVE"):
            cve = f"CVE-{cve}"
        modules = run_msfrpc_search(cve, req.limit)
        return {
            "cve": cve,
            "count": len(modules),
            "modules": modules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_stats():
    try:
        cmd = [
            "docker", "exec", KALI_CONTAINER,
            "msfconsole", "-q", "-x",
            "search type:exploit;exit"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        exploit_count = result.stdout.count("\nexploit/")
        return {
            "container": KALI_CONTAINER,
            "exploit_modules": exploit_count,
            "framework_version": "6.4.124-dev",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting NISA Metasploit API on port 8089...")
    uvicorn.run(app, host="127.0.0.1", port=8089, log_level="warning")
