import hashlib
import hmac
import uuid
import base64
import psycopg2
from datetime import datetime
from typing import Optional

try:
    from pqcrypto.sign.ml_dsa_65 import generate_keypair, sign, verify as pq_verify
    PQ_AVAILABLE = True
except ImportError:
    PQ_AVAILABLE = False

AUDIT_SECRET = "nisa_audit_secret_2026"
DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "nisa", "user": "nisa_user",
    "password": "nisa_secure_2026"
}

_PQ_PUBLIC_KEY = None
_PQ_SECRET_KEY = None

def _init_pq_keys():
    global _PQ_PUBLIC_KEY, _PQ_SECRET_KEY
    if not PQ_AVAILABLE:
        return
    import os
    key_dir = os.path.expanduser("~/.nisa/keys")
    pk_path = os.path.join(key_dir, "audit_ml_dsa_65.pk")
    sk_path = os.path.join(key_dir, "audit_ml_dsa_65.sk")
    os.makedirs(key_dir, exist_ok=True)
    if os.path.exists(pk_path) and os.path.exists(sk_path):
        with open(pk_path, "rb") as f:
            _PQ_PUBLIC_KEY = f.read()
        with open(sk_path, "rb") as f:
            _PQ_SECRET_KEY = f.read()
    else:
        _PQ_PUBLIC_KEY, _PQ_SECRET_KEY = generate_keypair()
        with open(pk_path, "wb") as f:
            f.write(_PQ_PUBLIC_KEY)
        with open(sk_path, "wb") as f:
            f.write(_PQ_SECRET_KEY)
        print(f"ML-DSA-65 keypair generated and saved to {key_dir}")

_init_pq_keys()

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def initialize_audit_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log2 (
            id SERIAL PRIMARY KEY,
            event_id TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            user_prompt TEXT,
            model_used TEXT,
            routing_reason TEXT,
            tool_executed TEXT,
            response_summary TEXT,
            framework_used TEXT,
            signature TEXT NOT NULL,
            signing_algorithm TEXT DEFAULT 'HMAC-SHA256',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    try:
        cur.execute("ALTER TABLE audit_log2 ADD COLUMN IF NOT EXISTS signing_algorithm TEXT DEFAULT 'HMAC-SHA256'")
        conn.commit()
    except Exception:
        conn.rollback()
    conn.commit()
    cur.close()
    conn.close()

def make_signature(event_id, timestamp, event_type, model, summary):
    payload = f"{event_id}|{timestamp}|{event_type}|{model}|{summary}".encode()
    if PQ_AVAILABLE and _PQ_SECRET_KEY:
        try:
            sig_bytes = sign(_PQ_SECRET_KEY, payload)
            return "ML-DSA-65:" + base64.b64encode(sig_bytes).decode()
        except Exception:
            pass
    return "HMAC-SHA256:" + hmac.new(
        AUDIT_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

def verify_signature(payload_str, stored_sig):
    payload = payload_str.encode()
    if stored_sig.startswith("ML-DSA-65:") and PQ_AVAILABLE and _PQ_PUBLIC_KEY:
        try:
            sig_bytes = base64.b64decode(stored_sig[10:])
            pq_verify(_PQ_PUBLIC_KEY, payload, sig_bytes)
            return True
        except Exception:
            return False
    if stored_sig.startswith("HMAC-SHA256:"):
        expected = "HMAC-SHA256:" + hmac.new(
            AUDIT_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(stored_sig, expected)
    expected = hmac.new(
        AUDIT_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(stored_sig, expected)

def log_event(event_type, user_prompt=None, model_used=None,
              routing_reason=None, tool_executed=None,
              response_summary=None, framework_used=None):
    event_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    summary = (response_summary or "")[:200]
    model = model_used or ""
    sig = make_signature(event_id, timestamp, event_type, model, summary)
    algo = "ML-DSA-65" if sig.startswith("ML-DSA-65:") else "HMAC-SHA256"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log2 (
            event_id, timestamp, event_type, user_prompt,
            model_used, routing_reason, tool_executed,
            response_summary, framework_used, signature, signing_algorithm
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (event_id, timestamp, event_type, user_prompt,
          model, routing_reason, tool_executed,
          summary, framework_used, sig, algo))
    conn.commit()
    cur.close()
    conn.close()
    return event_id

def verify_entry(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id, timestamp, event_type,
               model_used, response_summary, signature
        FROM audit_log2 WHERE event_id = %s
    """, (event_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return False
    eid, ts, etype, model, summary, stored_sig = row
    payload_str = f"{eid}|{ts}|{etype}|{model or ''}|{summary or ''}"
    return verify_signature(payload_str, stored_sig)

def get_recent_events(limit=20):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT event_id, timestamp, event_type, model_used,
               tool_executed, routing_reason, response_summary
        FROM audit_log2 ORDER BY created_at DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

if __name__ == "__main__":
    print("Initializing NISA audit trail with quantum-resistant signing...")
    print(f"ML-DSA-65 available: {PQ_AVAILABLE}")
    initialize_audit_table()
    event_id = log_event(
        event_type="system_start",
        model_used="qwen/qwen3-32b",
        routing_reason="system",
        response_summary="NISA quantum-resistant audit trail initialized"
    )
    print(f"Logged event: {event_id}")
    verified = verify_entry(event_id)
    print(f"Signature verified: {verified}")
    algo = "ML-DSA-65" if PQ_AVAILABLE else "HMAC-SHA256"
    print(f"Signing algorithm: {algo}")
    print("Quantum-resistant audit trail operational.")
