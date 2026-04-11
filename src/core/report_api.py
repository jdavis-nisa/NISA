
import os
import json
import base64
import hashlib
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import psycopg2
from dilithium_py.ml_dsa import ML_DSA_65

app = FastAPI(title="NISA Unified Report API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generate or load ML-DSA-65 keypair at startup
KEY_PATH = os.path.expanduser("~/NISA/keys/report_mldsa65.json")
os.makedirs(os.path.dirname(KEY_PATH), exist_ok=True)

if os.path.exists(KEY_PATH):
    with open(KEY_PATH, "r") as f:
        keys = json.load(f)
    PUBLIC_KEY = bytes.fromhex(keys["public_key"])
    SECRET_KEY = bytes.fromhex(keys["secret_key"])
    print(f"ML-DSA-65 keypair loaded from {KEY_PATH}")
else:
    PUBLIC_KEY, SECRET_KEY = ML_DSA_65.keygen()
    with open(KEY_PATH, "w") as f:
        json.dump({"public_key": PUBLIC_KEY.hex(), "secret_key": SECRET_KEY.hex()}, f)
    print(f"ML-DSA-65 keypair generated and saved to {KEY_PATH}")

DB = dict(host="localhost", port=5432, dbname="nisa", user="nisa_user", password="nisa_secure_2026")

def get_db():
    return psycopg2.connect(**DB)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS report_queue (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            tab_name VARCHAR(100) NOT NULL,
            operation_type VARCHAR(100) NOT NULL,
            summary TEXT NOT NULL,
            detail TEXT,
            severity VARCHAR(20) DEFAULT 'INFO',
            added_at TIMESTAMP DEFAULT NOW(),
            position INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS report_builds (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(64) NOT NULL,
            title VARCHAR(255) NOT NULL,
            classification VARCHAR(50) DEFAULT 'UNCLASSIFIED',
            sections JSONB NOT NULL,
            generated_at TIMESTAMP DEFAULT NOW(),
            mldsa_signature TEXT,
            public_key_hex TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

class ReportSection(BaseModel):
    tab_name: str
    operation_type: str
    summary: str
    detail: Optional[str] = ""
    severity: Optional[str] = "INFO"
    session_id: Optional[str] = "default"

class ReportBuildRequest(BaseModel):
    session_id: str
    title: str
    classification: Optional[str] = "UNCLASSIFIED"
    section_ids: Optional[List[int]] = None

class VerifyRequest(BaseModel):
    report_id: int

@app.get("/health")
def health():
    return {"status": "online", "service": "NISA Unified Report API", "port": 8101, "crypto": "ML-DSA-65 NIST FIPS 204"}

@app.post("/report/queue")
def add_to_queue(section: ReportSection):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(position), 0) + 1 FROM report_queue WHERE session_id = %s", (section.session_id,))
    position = cur.fetchone()[0]
    cur.execute(
        """INSERT INTO report_queue (session_id, tab_name, operation_type, summary, detail, severity, position)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (section.session_id, section.tab_name, section.operation_type,
         section.summary, section.detail, section.severity, position)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "added", "id": new_id, "position": position}

@app.get("/report/queue/{session_id}")
def get_queue(session_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, tab_name, operation_type, summary, detail, severity, added_at, position
           FROM report_queue WHERE session_id = %s ORDER BY position ASC""",
        (session_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"sections": [
        {"id": r[0], "tab_name": r[1], "operation_type": r[2], "summary": r[3],
         "detail": r[4], "severity": r[5], "added_at": str(r[6]), "position": r[7]}
        for r in rows
    ]}

@app.delete("/report/queue/{section_id}")
def remove_from_queue(section_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM report_queue WHERE id = %s", (section_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "removed", "id": section_id}

@app.delete("/report/queue/session/{session_id}")
def clear_queue(session_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM report_queue WHERE session_id = %s", (session_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "cleared", "session_id": session_id}

@app.post("/report/reorder")
def reorder_sections(session_id: str, ordered_ids: List[int]):
    conn = get_db()
    cur = conn.cursor()
    for position, section_id in enumerate(ordered_ids):
        cur.execute(
            "UPDATE report_queue SET position = %s WHERE id = %s AND session_id = %s",
            (position, section_id, session_id)
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"status": "reordered"}

@app.post("/report/build")
def build_report(req: ReportBuildRequest):
    conn = get_db()
    cur = conn.cursor()
    if req.section_ids:
        cur.execute(
            """SELECT id, tab_name, operation_type, summary, detail, severity, added_at
               FROM report_queue WHERE session_id = %s AND id = ANY(%s) ORDER BY position ASC""",
            (req.session_id, req.section_ids)
        )
    else:
        cur.execute(
            """SELECT id, tab_name, operation_type, summary, detail, severity, added_at
               FROM report_queue WHERE session_id = %s ORDER BY position ASC""",
            (req.session_id,)
        )
    rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=400, detail="No sections in queue for this session")

    sections = [
        {"id": r[0], "tab_name": r[1], "operation_type": r[2],
         "summary": r[3], "detail": r[4], "severity": r[5], "timestamp": str(r[6])}
        for r in rows
    ]

    generated_at = datetime.utcnow().isoformat()
    report_payload = json.dumps({
        "title": req.title,
        "classification": req.classification,
        "session_id": req.session_id,
        "generated_at": generated_at,
        "sections": sections
    }, sort_keys=True).encode()

    # ML-DSA-65 post-quantum signature (NIST FIPS 204)
    signature = ML_DSA_65.sign(SECRET_KEY, report_payload)
    signature_b64 = base64.b64encode(signature).decode()
    public_key_hex = PUBLIC_KEY.hex()

    cur.execute(
        """INSERT INTO report_builds (session_id, title, classification, sections, generated_at, mldsa_signature, public_key_hex)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (req.session_id, req.title, req.classification,
         json.dumps(sections), generated_at, signature_b64, public_key_hex)
    )
    report_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "report_id": report_id,
        "title": req.title,
        "classification": req.classification,
        "session_id": req.session_id,
        "generated_at": generated_at,
        "sections": sections,
        "section_count": len(sections),
        "mldsa_signature": signature_b64,
        "mldsa_signature_bytes": len(signature),
        "public_key_hex": public_key_hex[:32] + "...",
        "crypto": "ML-DSA-65 NIST FIPS 204"
    }

@app.post("/report/verify")
def verify_report(req: VerifyRequest):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT title, classification, session_id, sections, generated_at, mldsa_signature, public_key_hex FROM report_builds WHERE id = %s",
        (req.report_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    title, classification, session_id, sections, generated_at, sig_b64, pk_hex = row
    report_payload = json.dumps({
        "title": title,
        "classification": classification,
        "session_id": session_id,
        "generated_at": str(generated_at),
        "sections": sections
    }, sort_keys=True).encode()

    signature = base64.b64decode(sig_b64)
    public_key = bytes.fromhex(pk_hex)
    valid = ML_DSA_65.verify(public_key, report_payload, signature)

    return {
        "report_id": req.report_id,
        "valid": valid,
        "status": "VERIFIED" if valid else "TAMPERED",
        "crypto": "ML-DSA-65 NIST FIPS 204",
        "signature_bytes": len(signature)
    }

@app.get("/report/pubkey")
def get_pubkey():
    return {"public_key_hex": PUBLIC_KEY.hex(), "crypto": "ML-DSA-65 NIST FIPS 204", "key_path": KEY_PATH}

if __name__ == "__main__":
    uvicorn.run("report_api:app", host="127.0.0.1", port=8101, reload=False)
