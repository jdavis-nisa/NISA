from fastapi import HTTPException, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import re
import hashlib
import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
import json
from datetime import datetime
from openai import OpenAI

app = FastAPI(title="NISA Forensics API", version="0.1.0")

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
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RedSage Client ───────────────────────────────────────────────
llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

def redsage_analyze(context: str, data: str) -> str:
    """Route forensic analysis through RedSage 8B specialist"""
    try:
        completion = llm.chat.completions.create(
            model="redsage-qwen3-8b-dpo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are RedSage, a cybersecurity and digital forensics specialist. "
                        "Analyze the provided forensic data concisely. "
                        "Identify threats, anomalies, attack patterns, and recommended actions. "
                        "Be direct and technical. Keep response under 250 words."
                    )
                },
                {
                    "role": "user",
                    "content": f"{context}\n\nData:\n{data}"
                }
            ],
            max_tokens=400,
            temperature=0.2
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"RedSage analysis unavailable: {str(e)}"

# ── IOC Patterns ─────────────────────────────────────────────────
PATTERNS = {
    "ipv4": re.compile(
        r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
    ),
    "domain": re.compile(
        r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)"
        r"+(?:com|net|org|io|gov|mil|edu|xyz|info|biz|co)\b"
    ),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "email": re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
    "url": re.compile(r"https?://[^\s]+"),
    "cve": re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE),
}

# ── Suspicious patterns for log analysis ─────────────────────────
SUSPICIOUS = [
    (re.compile(r"failed password", re.IGNORECASE), "AUTH_FAILURE", "high"),
    (re.compile(r"invalid user", re.IGNORECASE), "INVALID_USER", "high"),
    (re.compile(r"authentication failure", re.IGNORECASE), "AUTH_FAILURE", "high"),
    (re.compile(r"sudo:.+COMMAND", re.IGNORECASE), "SUDO_EXEC", "medium"),
    (re.compile(r"segfault|segmentation fault", re.IGNORECASE), "CRASH", "medium"),
    (re.compile(r"oom.killer|out of memory", re.IGNORECASE), "OOM", "medium"),
    (re.compile(r"connection refused", re.IGNORECASE), "CONN_REFUSED", "low"),
    (re.compile(r"denied|permission denied", re.IGNORECASE), "ACCESS_DENIED", "medium"),
    (re.compile(r"sql.?injection|xss|cross.site", re.IGNORECASE), "WEB_ATTACK", "critical"),
    (re.compile(r"wget|curl.+http|base64.+decode", re.IGNORECASE), "DOWNLOAD_ATTEMPT", "high"),
    (re.compile(r"/etc/passwd|/etc/shadow", re.IGNORECASE), "SENSITIVE_FILE", "critical"),
    (re.compile(r"nc -|netcat|ncat", re.IGNORECASE), "NETCAT_USE", "critical"),
    (re.compile(r"chmod.+777|chmod.+\+x", re.IGNORECASE), "PERM_CHANGE", "medium"),
]

# ── Models ───────────────────────────────────────────────────────
class LogAnalysisRequest(BaseModel):
    log_text: str
    log_type: Optional[str] = "generic"

class IOCRequest(BaseModel):
    text: str

class HashRequest(BaseModel):
    file_path: str
    expected_hash: Optional[str] = None

class TimelineRequest(BaseModel):
    events: List[dict]

class ForensicsResponse(BaseModel):
    findings: list
    iocs: dict
    timeline: list
    risk_level: str
    summary: str
    analysis: str

# ── Endpoints ────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Forensics API v0.1.0"}

@app.post("/analyze/logs")
def analyze_logs(req: LogAnalysisRequest):
    """Parse log text, extract IOCs, detect suspicious patterns"""
    lines = req.log_text.strip().split("\n")
    findings = []
    timeline = []

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # Check suspicious patterns
        for pattern, event_type, severity in SUSPICIOUS:
            if pattern.search(line):
                findings.append({
                    "line": i + 1,
                    "type": event_type,
                    "severity": severity,
                    "content": line.strip()[:200],
                })
                timeline.append({
                    "line": i + 1,
                    "event": event_type,
                    "severity": severity,
                    "content": line.strip()[:100],
                })
                break

    # Extract IOCs from full text
    iocs = extract_iocs(req.log_text)

    # Determine overall risk
    severities = [f["severity"] for f in findings]
    if "critical" in severities:
        risk_level = "CRITICAL"
    elif "high" in severities:
        risk_level = "HIGH"
    elif "medium" in severities:
        risk_level = "MEDIUM"
    elif "low" in severities:
        risk_level = "LOW"
    else:
        risk_level = "CLEAN"

    summary = (
        f"Analyzed {len(lines)} log lines. "
        f"Found {len(findings)} suspicious events. "
        f"Risk level: {risk_level}. "
        f"IOCs: {sum(len(v) for v in iocs.values())} total."
    )

    # RedSage analysis
    analysis_data = f"Findings: {findings[:10]}\nIOCs: {iocs}\nRisk: {risk_level}"
    analysis = redsage_analyze(
        f"Log forensics analysis ({req.log_type} logs, {len(lines)} lines)",
        analysis_data
    )

    return ForensicsResponse(
        findings=findings,
        iocs=iocs,
        timeline=sorted(timeline, key=lambda x: x["line"]),
        risk_level=risk_level,
        summary=summary,
        analysis=analysis
    )

@app.post("/extract/iocs")
def extract_ioc_endpoint(req: IOCRequest):
    """Extract all IOCs from arbitrary text"""
    iocs = extract_iocs(req.text)
    total = sum(len(v) for v in iocs.values())
    analysis = redsage_analyze(
        "IOC extraction from text",
        f"Extracted IOCs: {iocs}"
    )
    return {
        "iocs": iocs,
        "total": total,
        "analysis": analysis
    }

@app.post("/hash/file")
def hash_file(req: HashRequest):
    """Compute SHA256 hash of a file and optionally verify"""
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")

    try:
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with open(req.file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
                md5.update(chunk)

        sha256_hex = sha256.hexdigest()
        md5_hex = md5.hexdigest()
        file_size = os.path.getsize(req.file_path)

        verified = None
        if req.expected_hash:
            verified = req.expected_hash.lower() == sha256_hex.lower()

        return {
            "file": req.file_path,
            "sha256": sha256_hex,
            "md5": md5_hex,
            "size_bytes": file_size,
            "verified": verified,
            "status": "MATCH" if verified else ("MISMATCH" if verified is False else "NOT_CHECKED")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/timeline")
def build_timeline(req: TimelineRequest):
    """Sort and reconstruct event timeline"""
    events = req.events
    try:
        sorted_events = sorted(
            events,
            key=lambda x: x.get("timestamp", x.get("line", 0))
        )
    except Exception:
        sorted_events = events

    analysis = redsage_analyze(
        "Event timeline reconstruction",
        f"Events: {sorted_events[:20]}"
    )
    return {
        "timeline": sorted_events,
        "event_count": len(sorted_events),
        "analysis": analysis
    }

# ── Helper ───────────────────────────────────────────────────────
def extract_iocs(text: str) -> dict:
    results = {}
    for ioc_type, pattern in PATTERNS.items():
        matches = list(set(pattern.findall(text)))
        if matches:
            results[ioc_type] = matches[:50]
    return results

import subprocess as _subprocess

class PcapRequest(BaseModel):
    pcap_path: str
    max_packets: Optional[int] = 1000

@app.post("/analyze/pcap")
def analyze_pcap(req: PcapRequest):
    """Analyze a pcap file with tshark - extract connections, IOCs, anomalies"""
    if not os.path.exists(req.pcap_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.pcap_path}")

    try:
        # Get packet summary
        result = _subprocess.run([
            "tshark", "-r", req.pcap_path,
            "-T", "fields",
            "-e", "frame.number",
            "-e", "frame.time_relative",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "udp.srcport",
            "-e", "udp.dstport",
            "-e", "_ws.col.Protocol",
            "-e", "_ws.col.Info",
            "-c", str(req.max_packets)
        ], capture_output=True, text=True, timeout=60)

        packets = []
        connections = {}
        src_ips = set()
        dst_ips = set()

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 4:
                src_ip = parts[2] if len(parts) > 2 else ""
                dst_ip = parts[3] if len(parts) > 3 else ""
                protocol = parts[8] if len(parts) > 8 else ""
                info = parts[9] if len(parts) > 9 else ""

                if src_ip:
                    src_ips.add(src_ip)
                if dst_ip:
                    dst_ips.add(dst_ip)

                conn_key = f"{src_ip}->{dst_ip}"
                if conn_key not in connections:
                    connections[conn_key] = {"count": 0, "protocol": protocol}
                connections[conn_key]["count"] += 1

                packets.append({
                    "frame": parts[0],
                    "time": parts[1] if len(parts) > 1 else "",
                    "src": src_ip,
                    "dst": dst_ip,
                    "protocol": protocol,
                    "info": info[:100]
                })

        # Get protocol stats
        proto_result = _subprocess.run([
            "tshark", "-r", req.pcap_path, "-q", "-z", "io,phs"
        ], capture_output=True, text=True, timeout=30)

        # Extract IOCs
        all_text = " ".join([p.get("info", "") for p in packets])
        all_text += " " + " ".join(src_ips) + " " + " ".join(dst_ips)
        iocs = extract_iocs(all_text)

        # Find suspicious connections (high packet count, unusual ports)
        suspicious = []
        for conn, data in connections.items():
            if data["count"] > 50:
                suspicious.append({
                    "connection": conn,
                    "packet_count": data["count"],
                    "protocol": data["protocol"],
                    "reason": "HIGH_VOLUME"
                })

        total_packets = len(packets)
        unique_src = len(src_ips)
        unique_dst = len(dst_ips)
        summary = (
            f"Analyzed {total_packets} packets. "
            f"{unique_src} source IPs, {unique_dst} destination IPs. "
            f"{len(suspicious)} suspicious connections detected."
        )

        analysis_data = f"Packets: {total_packets}, Connections: {len(connections)}, Suspicious: {suspicious[:5]}, IOCs: {iocs}"
        analysis = redsage_analyze("Network pcap forensic analysis", analysis_data)

        return {
            "pcap_path": req.pcap_path,
            "total_packets": total_packets,
            "unique_src_ips": list(src_ips)[:20],
            "unique_dst_ips": list(dst_ips)[:20],
            "top_connections": sorted(
                connections.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10],
            "suspicious": suspicious,
            "iocs": iocs,
            "summary": summary,
            "analysis": analysis,
            "protocol_stats": proto_result.stdout[:1000]
        }

    except _subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="tshark analysis timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8083)
