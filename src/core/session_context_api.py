import os
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any
import uvicorn
from datetime import datetime

app = FastAPI(title="NISA Session Context API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:5176","http://127.0.0.1:5173","http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store - resets on service restart
session_entries = []

class ContextEntry(BaseModel):
    tab: str
    operation: str
    summary: str
    detail: Optional[Any] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "session_context_api", "entries": len(session_entries)}

@app.post("/context/add")
async def add_context(entry: ContextEntry):
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tab": entry.tab,
        "operation": entry.operation,
        "summary": entry.summary,
        "detail": entry.detail
    }
    session_entries.append(record)
    return {"status": "ok", "total_entries": len(session_entries)}

@app.get("/context/all")
def get_all_context():
    return {"entries": session_entries}

@app.get("/context/latest")
def get_latest(limit: int = 5):
    return {"entries": session_entries[-limit:]}

@app.get("/context/summary")
def get_summary():
    if not session_entries:
        return {"summary": None}
    lines = []
    for e in session_entries:
        lines.append(f"[{e['timestamp']}] {e['tab']} — {e['operation']}: {e['summary']}")
    return {"summary": "\n".join(lines)}

@app.delete("/context/clear")
def clear_context():
    session_entries.clear()
    return {"status": "cleared"}

if __name__ == "__main__":
    uvicorn.run("session_context_api:app", host="127.0.0.1", port=8095, reload=False)
