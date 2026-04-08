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
import uuid
import tempfile
import hashlib
from datetime import datetime
from openai import OpenAI

app = FastAPI(title="NISA Remediation API", version="0.1.0")

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

class ApplyPatchRequest(BaseModel):
    session_id: str
    remediation_id: str
    target_file: str
    backup: bool = True

@app.post("/apply")
def apply_patch(req: ApplyPatchRequest):
    """Apply a tested patch to a target file - requires session authorization"""
    if req.session_id not in _sessions:
        raise HTTPException(status_code=403, detail="Invalid session")

    session = _sessions[req.session_id]
    remediation = next((r for r in session["remediations"] if r["remediation_id"] == req.remediation_id), None)

    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation not found")

    if not remediation["sandbox_passed"]:
        raise HTTPException(status_code=400, detail="Cannot apply patch that failed sandbox testing")

    if not os.path.exists(req.target_file):
        raise HTTPException(status_code=404, detail=f"Target file not found: {req.target_file}")

    try:
        # Backup original file
        backup_path = None
        if req.backup:
            backup_path = req.target_file + f".backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            with open(req.target_file, "r") as f:
                original = f.read()
            with open(backup_path, "w") as f:
                f.write(original)

        # Apply patch
        patch_code = remediation["patch_code"]
        with open(req.target_file, "w") as f:
            f.write(patch_code)

        return {
            "status": "applied",
            "target_file": req.target_file,
            "backup_path": backup_path,
            "remediation_id": req.remediation_id,
            "applied_by": session["authorized_by"],
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Patch applied to {req.target_file}. Backup saved to {backup_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/{session_id}/{remediation_id}")
def generate_report(session_id: str, remediation_id: str):
    """Generate a professional PDF remediation report"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from fastapi.responses import FileResponse
    import tempfile

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = _sessions[session_id]
    remediation = next((r for r in session["remediations"] if r["remediation_id"] == remediation_id), None)
    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation not found")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()

    doc = SimpleDocTemplate(tmp.name, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()
    gold = colors.HexColor("#C9A84C")
    dark = colors.HexColor("#0D1117")
    danger = colors.HexColor("#FF4444")
    success = colors.HexColor("#00FF88")

    title_style = ParagraphStyle("title", fontSize=24, fontName="Helvetica-Bold",
                                  textColor=gold, alignment=TA_CENTER, spaceAfter=4)
    subtitle_style = ParagraphStyle("subtitle", fontSize=11, fontName="Helvetica",
                                     textColor=colors.HexColor("#8B9BAA"), alignment=TA_CENTER, spaceAfter=4)
    section_style = ParagraphStyle("section", fontSize=12, fontName="Helvetica-Bold",
                                    textColor=gold, spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                                 textColor=colors.HexColor("#2D3A4A"), spaceAfter=6, leading=16)
    code_style = ParagraphStyle("code", fontSize=8, fontName="Courier",
                                 textColor=colors.HexColor("#2D3A4A"),
                                 backColor=colors.HexColor("#F5F5F5"),
                                 spaceAfter=6, leading=12, leftIndent=12)

    story = []

    story.append(Spacer(1, 12))
    story.append(Paragraph("NISA", title_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Network Intelligence Security Assistant", subtitle_style))
    story.append(Paragraph("Vulnerability Remediation Report", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=gold, spaceAfter=16))

    sev_color = {"CRITICAL": danger, "HIGH": colors.HexColor("#FF6B35"),
                 "MEDIUM": colors.HexColor("#FFA500"), "LOW": colors.HexColor("#00AAFF")}

    meta = [
        ["Report ID:", remediation["remediation_id"]],
        ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Target:", remediation["target"]],
        ["Authorized By:", remediation["authorized_by"]],
        ["Severity:", remediation["severity"]],
        ["CVSS Score:", str(remediation["cvss_score"])],
        ["Sandbox Status:", "PASSED" if remediation["sandbox_passed"] else "FAILED"],
        ["Status:", remediation["status"]],
    ]

    t = Table(meta, colWidths=[2*inch, 4.5*inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#2D3A4A")),
        ("TEXTCOLOR", (1,0), (1,-1), colors.HexColor("#2D3A4A")),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.HexColor("#F8F9FA"), colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#DEE2E6")),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Vulnerability Description", section_style))
    story.append(Paragraph(remediation["vulnerability"], body_style))
    story.append(Paragraph(f"<b>Affected Component:</b> {remediation['affected_component']}", body_style))

    story.append(Paragraph("Analysis", section_style))
    story.append(Paragraph(remediation.get("explanation", ""), body_style))

    if remediation.get("patch_code"):
        story.append(Paragraph("Patch Code", section_style))
        code_lines = remediation["patch_code"].replace("\\n", "\n").split("\n")
        for line in code_lines[:50]:
            story.append(Paragraph(line.replace(" ", "&nbsp;") or "&nbsp;", code_style))

    if remediation.get("implementation_steps"):
        story.append(Paragraph("Implementation Steps", section_style))
        for i, step in enumerate(remediation["implementation_steps"]):
            story.append(Paragraph(f"{i+1}. {step}", body_style))

    if remediation.get("references"):
        story.append(Paragraph("References", section_style))
        for ref in remediation["references"]:
            story.append(Paragraph(f"• {ref}", body_style))

    sandbox_color = success if remediation["sandbox_passed"] else danger
    story.append(Paragraph("Sandbox Test Results", section_style))
    story.append(Paragraph(
        f"Status: {'PASSED' if remediation['sandbox_passed'] else 'FAILED'}",
        ParagraphStyle("sandbox", fontSize=10, fontName="Helvetica-Bold",
                       textColor=sandbox_color, spaceAfter=6)
    ))
    if remediation.get("sandbox_output"):
        story.append(Paragraph(remediation["sandbox_output"][:500], code_style))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#DEE2E6"), spaceBefore=16))
    story.append(Paragraph(
        "This report was automatically generated by NISA - Network Intelligence Security Assistant. "
        "All patches are tested in an isolated sandbox environment before presentation. "
        f"Authorized by {remediation['authorized_by']} on {remediation['timestamp'][:10]}.",
        ParagraphStyle("footer", fontSize=8, fontName="Helvetica",
                       textColor=colors.HexColor("#8B9BAA"), alignment=TA_CENTER)
    ))

    doc.build(story)

    return FileResponse(
        tmp.name,
        media_type="application/pdf",
        filename=f"NISA_Remediation_{remediation_id}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8086)
