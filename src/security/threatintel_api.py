#!/usr/bin/env python3.11
"""
NISA Threat Intelligence API - Port 8093
Serves threat intel from local knowledge library only - zero external calls
"""
import os
import json
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")
SSD_BASE = "/Volumes/Share Drive/NISA/knowledge/security"

app = FastAPI(title="NISA Threat Intel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in ["/health"]:
        return await call_next(request)
    key = request.headers.get("X-NISA-API-Key", "")
    if NISA_API_KEY and key != NISA_API_KEY:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": "Invalid API key"})
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Threat Intel API v0.1.0"}

def load_knowledge_file(filename: str) -> str:
    path = os.path.join(SSD_BASE, filename)
    if not os.path.exists(path):
        # Try finding any file matching pattern
        files = list(Path(SSD_BASE).glob(f"*{filename.split('_')[0]}*"))
        if files:
            path = str(files[0])
        else:
            return ""
    with open(path, "r", errors="replace") as f:
        return f.read()

def find_latest_file(prefix: str) -> str:
    files = list(Path(SSD_BASE).glob(f"{prefix}*.txt"))
    if not files:
        return ""
    files.sort(reverse=True)
    with open(files[0], "r", errors="replace") as f:
        return f.read()

@app.get("/cve/recent")
def get_recent_cves(severity: str = "CRITICAL", limit: int = 20):
    """Get CVEs from local NVD knowledge file"""
    content = find_latest_file("NIST_NVD_CVE")
    if not content:
        raise HTTPException(status_code=404, detail="NVD CVE knowledge file not found")
    
    cves = []
    lines = content.split("\n")
    current = {}
    for line in lines:
        line = line.strip()
        if line.startswith("CVE-") and len(line) < 25:
            if current.get("id"):
                cves.append(current)
            current = {"id": line, "severity": "UNKNOWN", "description": "", "published": "", "cvss": None}
        elif current and "description" in current:
            if line and not current["description"]:
                current["description"] = line[:300]
        if "CRITICAL" in line.upper():
            if current:
                current["severity"] = "CRITICAL"
        elif "HIGH" in line.upper() and current:
            if current.get("severity") == "UNKNOWN":
                current["severity"] = "HIGH"
    
    if current.get("id"):
        cves.append(current)
    
    if severity != "ALL":
        filtered = [c for c in cves if c.get("severity") == severity]
        if not filtered:
            filtered = cves
    else:
        filtered = cves

    return {"cves": filtered[:limit], "total": len(filtered), "severity": severity, "source": "local"}

@app.get("/cve/search")
def search_cve(q: str, limit: int = 20):
    """Search CVEs in local knowledge files"""
    content = find_latest_file("NIST_NVD_CVE")
    if not content:
        raise HTTPException(status_code=404, detail="NVD CVE knowledge file not found")
    
    q_lower = q.lower()
    results = []
    lines = content.split("\n")
    
    # Find lines containing the query and surrounding context
    for i, line in enumerate(lines):
        if q_lower in line.lower():
            cve_id = None
            # Look backwards for CVE ID
            for j in range(i, max(0, i-10), -1):
                match = re.search(r'CVE-\d{4}-\d+', lines[j])
                if match:
                    cve_id = match.group(0)
                    break
            if cve_id and not any(r["id"] == cve_id for r in results):
                context = " ".join(lines[max(0,i-1):i+3]).strip()[:300]
                results.append({
                    "id": cve_id,
                    "description": context,
                    "severity": "CRITICAL" if "critical" in context.lower() else "HIGH" if "high" in context.lower() else "MEDIUM",
                    "cvss": None,
                    "source": "local"
                })
            if len(results) >= limit:
                break
    
    return {"cves": results, "total": len(results), "query": q, "source": "local"}

@app.get("/mitre/tactics")
def get_mitre_tactics():
    """Return MITRE ATT&CK tactics from local knowledge"""
    tactics = [
        {"id": "TA0043", "name": "Reconnaissance", "techniques": 10, "color": "#ff4444"},
        {"id": "TA0042", "name": "Resource Development", "techniques": 8, "color": "#ff6600"},
        {"id": "TA0001", "name": "Initial Access", "techniques": 10, "color": "#ff8800"},
        {"id": "TA0002", "name": "Execution", "techniques": 14, "color": "#ffaa00"},
        {"id": "TA0003", "name": "Persistence", "techniques": 20, "color": "#c9a84c"},
        {"id": "TA0004", "name": "Privilege Escalation", "techniques": 14, "color": "#88cc00"},
        {"id": "TA0005", "name": "Defense Evasion", "techniques": 43, "color": "#44aa44"},
        {"id": "TA0006", "name": "Credential Access", "techniques": 17, "color": "#44aaaa"},
        {"id": "TA0007", "name": "Discovery", "techniques": 32, "color": "#4488ff"},
        {"id": "TA0008", "name": "Lateral Movement", "techniques": 9, "color": "#6644ff"},
        {"id": "TA0009", "name": "Collection", "techniques": 17, "color": "#8844ff"},
        {"id": "TA0011", "name": "Command and Control", "techniques": 17, "color": "#aa44ff"},
        {"id": "TA0010", "name": "Exfiltration", "techniques": 9, "color": "#ff44ff"},
        {"id": "TA0040", "name": "Impact", "techniques": 14, "color": "#ff4488"},
    ]
    return {"tactics": tactics, "total": len(tactics), "source": "local"}

@app.get("/mitre/search")
def search_mitre(q: str):
    """Search MITRE ATT&CK in local knowledge file"""
    content = find_latest_file("MITRE_ATTACK")
    if not content:
        return {"techniques": [], "query": q, "source": "local", "error": "MITRE ATT&CK knowledge file not found"}
    
    q_lower = q.lower()
    results = []
    lines = content.split("\n")
    
    for i, line in enumerate(lines):
        if q_lower in line.lower():
            technique_id = None
            match = re.search(r'T\d{4}(\.\d{3})?', line)
            if match:
                technique_id = match.group(0)
            context = " ".join(lines[max(0,i-1):i+2]).strip()[:250]
            if technique_id and not any(r.get("id") == technique_id for r in results):
                tactic = "Unknown"
                for tac in ["Initial Access", "Execution", "Persistence", "Privilege Escalation",
                           "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
                           "Collection", "Command and Control", "Exfiltration", "Impact"]:
                    if tac.lower() in context.lower():
                        tactic = tac
                        break
                results.append({
                    "id": technique_id,
                    "name": line.strip()[:80],
                    "tactic": tactic,
                    "description": context,
                    "source": "local"
                })
            if len(results) >= 15:
                break
    
    return {"techniques": results, "total": len(results), "query": q, "source": "local"}

@app.get("/intel/summary")
def get_intel_summary():
    """Get threat intel summary from local knowledge files"""
    nvd_content = find_latest_file("NIST_NVD_CVE")
    mitre_content = find_latest_file("MITRE_ATTACK")
    owasp_content = find_latest_file("OWASP")
    
    critical_count = len(re.findall(r"CRITICAL", nvd_content, re.IGNORECASE)) if nvd_content else 0
    cve_count = len(re.findall(r"CVE-\d{4}-\d+", nvd_content)) if nvd_content else 0
    technique_count = len(re.findall(r"T\d{4}", mitre_content)) if mitre_content else 0
    
    files = list(Path(SSD_BASE).glob("*.txt"))
    
    return {
        "cve_count": cve_count,
        "critical_mentions": critical_count,
        "mitre_techniques_indexed": technique_count,
        "knowledge_files": len(files),
        "source": "local",
        "nvd_file": "available" if nvd_content else "not found",
        "mitre_file": "available" if mitre_content else "not found",
        "owasp_file": "available" if owasp_content else "not found",
        "last_updated": "2026-04-07"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8093, log_level="info")
