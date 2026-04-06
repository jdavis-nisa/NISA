import hashlib
import hmac
import uuid
import psycopg2
from datetime import datetime
from typing import Optional

AUDIT_SECRET = "nisa_audit_secret_2026"
DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "database": "nisa", "user": "nisa_user",
    "password": "nisa_secure_2026"
}

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
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def make_signature(event_id, timestamp, event_type, model, summary):
    payload = f"{event_id}|{timestamp}|{event_type}|{model}|{summary}"
    return hmac.new(
        AUDIT_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def log_event(event_type, user_prompt=None, model_used=None,
              routing_reason=None, tool_executed=None,
              response_summary=None, framework_used=None):
    event_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    summary = (response_summary or "")[:200]
    model = model_used or ""
    sig = make_signature(event_id, timestamp, event_type, model, summary)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log2 (
            event_id, timestamp, event_type, user_prompt,
            model_used, routing_reason, tool_executed,
            response_summary, framework_used, signature
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (event_id, timestamp, event_type, user_prompt,
          model, routing_reason, tool_executed,
          summary, framework_used, sig))
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
    expected = make_signature(eid, ts, etype, model or "", summary or "")
    return hmac.compare_digest(stored_sig, expected)

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
    print("Initializing NISA audit trail...")
    initialize_audit_table()
    event_id = log_event(
        event_type="system_start",
        model_used="qwen/qwen3-32b",
        routing_reason="system",
        response_summary="NISA audit trail initialized"
    )
    print(f"Logged event: {event_id}")
    verified = verify_entry(event_id)
    print(f"Signature verified: {verified}")
    events = get_recent_events(5)
    print(f"Recent events in log: {len(events)}")
    print("Audit trail operational.")
