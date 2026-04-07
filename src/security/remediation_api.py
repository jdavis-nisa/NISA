from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess
import json
import os
import uuid
import tempfile
import hashlib
from datetime import datetime
from openai import OpenAI

app = FastAPI(title="NISA Remediation API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

llm = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
_sessions = {}

class AuthRequest(BaseModel):
    target: str
    scope: str
    authorized_by: str
    authorization_date: str
    engagement_type: str = "vulnerability_assessment"

class RemediationRequest(BaseModel):
    session_id: str
    vulnerability: str
    affected_component: str
    language: str = "python"
    auto_apply: bool = False

class SandboxRequest(BaseModel):
    code: str
    test_code: str
    language: str = "python"
    timeout: int = 10

def generate_auth_token(target: str, authorized_by: str) -> str:
    payload = f"{target}|{authorized_by}|{datetime.utcnow().date()}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16].upper()

def run_in_sandbox(code: str, test_code: str, language: str = "python", timeout: int = 10) -> dict:
    """Run code in isolated subprocess sandbox"""
    with tempfile.TemporaryDirectory() as tmpdir:
        if language in ["python", "py"]:
            code_file = os.path.join(tmpdir, "patch.py")
            test_file = os.path.join(tmpdir, "test_patch.py")
            
            with open(code_file, "w") as f:
                f.write(code)
            
            full_test = f"""
import sys
sys.path.insert(0, '{tmpdir}')
{code}

# Test cases
{test_code}

print("SANDBOX_PASS: All tests passed")
"""
            with open(test_file, "w") as f:
                f.write(full_test)
            
            try:
                result = subprocess.run(
                    ["python3.11", test_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                    env={"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": tmpdir}
                )
                passed = "SANDBOX_PASS" in result.stdout
                return {
                    "passed": passed,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:500] if result.stderr else "",
                    "returncode": result.returncode,
                    "language": language
                }
            except subprocess.TimeoutExpired:
                return {"passed": False, "stdout": "", "stderr": "Sandbox timeout", "returncode": -1, "language": language}
        
        elif language in ["bash", "sh"]:
            script_file = os.path.join(tmpdir, "patch.sh")
            with open(script_file, "w") as f:
                f.write(code + "\n" + test_code)
            try:
                result = subprocess.run(
                    ["bash", script_file],
                    capture_output=True, text=True, timeout=timeout, cwd=tmpdir,
                    env={"PATH": "/opt/homebrew/bin:/usr/bin:/bin", "HOME": tmpdir}
                )
                return {
                    "passed": result.returncode == 0,
                    "stdout": result.stdout[:2000],
                    "stderr": result.stderr[:500],
                    "returncode": result.returncode,
                    "language": language
                }
            except subprocess.TimeoutExpired:
                return {"passed": False, "stdout": "", "stderr": "Timeout", "returncode": -1, "language": language}
        
        return {"passed": False, "stdout": "", "stderr": f"Unsupported language: {language}", "returncode": -1, "language": language}

def generate_patch(vulnerability: str, component: str, language: str) -> dict:
    """Use Nisaba to generate a patch for the vulnerability"""
    try:
        completion = llm.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[
                {"role": "system", "content": """You are Nisaba, an expert security engineer. 
When given a vulnerability description, you must respond with ONLY a JSON object containing:
{
  "patch_code": "the actual fix code",
  "test_code": "test cases that verify the fix works",
  "explanation": "what the vulnerability is and how the patch fixes it",
  "cvss_score": "estimated CVSS score 0-10",
  "severity": "CRITICAL/HIGH/MEDIUM/LOW",
  "implementation_steps": ["step 1", "step 2", "step 3"],
  "references": ["CVE or reference if applicable"]
}
Return ONLY valid JSON, no markdown, no explanation outside the JSON."""},
                {"role": "user", "content": f"Vulnerability: {vulnerability}\nAffected Component: {component}\nLanguage: {language}\n\nGenerate a patch with tests."}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        response = completion.choices[0].message.content.strip()
        # Clean JSON
        if "```" in response:
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        
        return json.loads(response)
    except Exception as e:
        return {
            "patch_code": "",
            "test_code": "",
            "explanation": f"Patch generation failed: {str(e)}",
            "cvss_score": "unknown",
            "severity": "UNKNOWN",
            "implementation_steps": [],
            "references": []
        }

@app.get("/health")
def health():
    return {"status": "online", "system": "NISA Remediation API v0.1.0"}

@app.post("/authorize")
def authorize_engagement(req: AuthRequest):
    """Create authorized remediation session"""
    session_id = str(uuid.uuid4())
    token = generate_auth_token(req.target, req.authorized_by)
    
    _sessions[session_id] = {
        "session_id": session_id,
        "token": token,
        "target": req.target,
        "scope": req.scope,
        "authorized_by": req.authorized_by,
        "authorization_date": req.authorization_date,
        "engagement_type": req.engagement_type,
        "created_at": datetime.utcnow().isoformat(),
        "remediations": []
    }
    
    return {
        "session_id": session_id,
        "authorization_token": token,
        "target": req.target,
        "status": "authorized",
        "message": f"Remediation session authorized for {req.target} by {req.authorized_by}"
    }

@app.post("/remediate")
def remediate(req: RemediationRequest):
    """Generate and test a patch for a vulnerability"""
    if req.session_id not in _sessions:
        raise HTTPException(status_code=403, detail="Invalid session - authorization required")
    
    session = _sessions[req.session_id]
    remediation_id = str(uuid.uuid4())[:8].upper()
    
    # Generate patch
    patch_data = generate_patch(req.vulnerability, req.affected_component, req.language)
    
    # Run sandbox tests
    sandbox_result = {"passed": False, "stdout": "", "stderr": "No test code generated"}
    if patch_data.get("patch_code") and patch_data.get("test_code"):
        sandbox_result = run_in_sandbox(
            patch_data["patch_code"],
            patch_data["test_code"],
            req.language
        )
    
    remediation = {
        "remediation_id": remediation_id,
        "session_id": req.session_id,
        "target": session["target"],
        "vulnerability": req.vulnerability,
        "affected_component": req.affected_component,
        "severity": patch_data.get("severity", "UNKNOWN"),
        "cvss_score": patch_data.get("cvss_score", "unknown"),
        "patch_code": patch_data.get("patch_code", ""),
        "test_code": patch_data.get("test_code", ""),
        "explanation": patch_data.get("explanation", ""),
        "implementation_steps": patch_data.get("implementation_steps", []),
        "references": patch_data.get("references", []),
        "sandbox_passed": sandbox_result["passed"],
        "sandbox_output": sandbox_result["stdout"],
        "sandbox_error": sandbox_result["stderr"],
        "timestamp": datetime.utcnow().isoformat(),
        "authorized_by": session["authorized_by"],
        "status": "TESTED_PASSED" if sandbox_result["passed"] else "TESTED_FAILED"
    }
    
    session["remediations"].append(remediation)
    return remediation

@app.post("/sandbox")
def sandbox_test(req: SandboxRequest):
    """Run arbitrary code in sandbox for testing"""
    result = run_in_sandbox(req.code, req.test_code, req.language, req.timeout)
    return result

@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _sessions[session_id]

@app.get("/sessions")
def list_sessions():
    return {"sessions": list(_sessions.values())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8086)
