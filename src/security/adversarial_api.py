#!/usr/bin/env python3.11
"""
NISA Adversarial Simulation Engine - Port 8094
AI-powered red team / blue team kill chain generator
Pure analysis - no packets sent, no exploits executed
"""
import os
import json
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
PRIMARY_MODEL = "qwen/qwen3-32b"

app = FastAPI(title="NISA Adversarial Simulation Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.method == "OPTIONS" or request.url.path in ["/health", "/threat_actors"]:
        return await call_next(request)
    key = request.headers.get("X-NISA-API-Key", "")
    if NISA_API_KEY and key != NISA_API_KEY:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=403, content={"detail": "Invalid API key"})
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Adversarial Simulation Engine v0.1.0"}

@app.get("/threat_actors")
def get_threat_actors():
    return {"actors": [
        {"id": "apt28", "name": "APT28 (Fancy Bear)", "origin": "Russia", "targets": "Government, Military, Defense", "color": "#ff2244"},
        {"id": "apt29", "name": "APT29 (Cozy Bear)", "origin": "Russia", "targets": "Government, Think Tanks", "color": "#ff4466"},
        {"id": "lazarus", "name": "Lazarus Group", "origin": "North Korea", "targets": "Financial, Defense, Crypto", "color": "#ff6600"},
        {"id": "apt41", "name": "APT41 (Double Dragon)", "origin": "China", "targets": "Healthcare, Telecom, Defense", "color": "#ffaa00"},
        {"id": "fin7", "name": "FIN7 (Carbanak)", "origin": "Eastern Europe", "targets": "Financial, Retail, Hospitality", "color": "#c9a84c"},
        {"id": "ransomware", "name": "Generic Ransomware", "origin": "Various", "targets": "All sectors", "color": "#ff4444"},
        {"id": "insider", "name": "Malicious Insider", "origin": "Internal", "targets": "Privileged access systems", "color": "#aa44ff"},
        {"id": "custom", "name": "Custom Threat Actor", "origin": "User defined", "targets": "User defined", "color": "#44aaff"},
    ]}

class SimRequest(BaseModel):
    target_description: str
    threat_actor: str = "apt28"
    network_context: Optional[str] = None
    open_ports: Optional[list] = None
    simulation_depth: str = "standard"

def call_nisaba(prompt: str) -> str:
    try:
        response = httpx.post(
            LM_STUDIO_URL,
            json={
                "model": PRIMARY_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a senior cybersecurity analyst and red team expert with deep knowledge of MITRE ATT&CK framework, threat actor TTPs, and defensive security operations. Provide detailed, accurate, actionable analysis. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 3500,
                "extra_body": {"num_ctx": 32768}
            },
            timeout=300
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")

@app.post("/simulate")
def run_simulation(req: SimRequest):
    """Generate adversarial kill chain with red/blue team analysis"""
    
    actor_profiles = {
        "apt28": "APT28 (Fancy Bear) - Russian GRU unit, known for spear phishing, credential harvesting, use of tools like X-Agent, Mimikatz, and custom malware. Targets government and defense sectors.",
        "apt29": "APT29 (Cozy Bear) - Russian SVR unit, stealthy long-term access, supply chain attacks, uses WellMess and other custom tools.",
        "lazarus": "Lazarus Group - North Korean state actor, financially motivated, uses custom malware, targets SWIFT systems and cryptocurrency.",
        "apt41": "APT41 - Chinese state-sponsored, dual espionage/financial motivation, exploits public-facing applications, supply chain attacks.",
        "fin7": "FIN7/Carbanak - Financially motivated, spear phishing with malicious documents, point-of-sale malware, extensive use of Cobalt Strike.",
        "ransomware": "Generic ransomware operator - opportunistic, exploits known vulnerabilities, uses commodity tools, double extortion tactics.",
        "insider": "Malicious insider - privileged access abuse, data exfiltration, sabotage, typically bypasses perimeter controls.",
        "custom": "Custom threat actor as described by the user."
    }
    
    actor_profile = actor_profiles.get(req.threat_actor, actor_profiles["custom"])
    
    ports_context = ""
    if req.open_ports:
        ports_context = f"\nOpen ports discovered: {json.dumps(req.open_ports)}"
    
    network_context = req.network_context or ""
    
    prompt = f"""You are performing a threat modeling exercise for a security team. This is a planning and analysis exercise only - no actual attacks will be executed.

TARGET ENVIRONMENT:
{req.target_description}
{network_context}
{ports_context}

THREAT ACTOR PROFILE:
{actor_profile}

Generate a detailed adversarial simulation with a realistic kill chain. For each step provide both the red team attack action AND the blue team detection/response.

Respond ONLY with this exact JSON structure:
{{
  "simulation_title": "brief title",
  "threat_actor": "{req.threat_actor}",
  "target_summary": "one sentence summary",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "executive_summary": "2-3 sentence executive summary for CISO",
  "kill_chain": [
    {{
      "step": 1,
      "phase": "MITRE tactic name",
      "tactic_id": "TA00XX",
      "technique": "technique name",
      "technique_id": "TXXXX",
      "red_team": {{
        "action": "what the attacker does",
        "tools": ["tool1", "tool2"],
        "commands": "example command or indicator",
        "indicators": "IOCs that would be generated"
      }},
      "blue_team": {{
        "detection": "how to detect this",
        "log_source": "Windows Event Log|Sysmon|Network|Firewall|EDR",
        "detection_query": "example SIEM query or Suricata rule",
        "response": "immediate response action",
        "gap": "detection gap if any"
      }},
      "severity": "CRITICAL|HIGH|MEDIUM|LOW"
    }}
  ],
  "defensive_gaps": ["gap1", "gap2"],
  "immediate_recommendations": ["rec1", "rec2", "rec3"],
  "mitre_coverage": {{
    "detected": 0,
    "partial": 0,
    "blind": 0
  }}
}}

Generate 6-8 kill chain steps covering the full attack lifecycle from initial access to impact/exfiltration."""

    raw = call_nisaba(prompt)
    
    # Clean JSON response
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()
    
    try:
        result = json.loads(raw)
        # Calculate coverage stats
        steps = result.get("kill_chain", [])
        detected = sum(1 for s in steps if not s.get("blue_team", {}).get("gap"))
        blind = sum(1 for s in steps if s.get("blue_team", {}).get("gap"))
        result["mitre_coverage"] = {
            "detected": detected,
            "partial": 0,
            "blind": blind,
            "total": len(steps)
        }
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Model returned invalid JSON: {str(e)}. Raw: {raw[:200]}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8094, log_level="info")
