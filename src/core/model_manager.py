#!/usr/bin/env python3.11
"""
NISA Model Manager
Automated LM Studio model loading/unloading with memory management.
Ensures correct context lengths and handles model swapping on M3/M5.
"""
import os
import json
import time
import httpx
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/NISA/.env"))
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="NISA Model Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:5176","http://127.0.0.1:5173","http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NISA_API_KEY = os.environ.get("NISA_API_KEY", "")
LM_STUDIO = "http://localhost:1234"

@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/models/status") or request.method == "OPTIONS":
        return await call_next(request)
    if NISA_API_KEY:
        key = request.headers.get("X-NISA-API-Key", "")
        if key != NISA_API_KEY:
            return JSONResponse(status_code=403, content={"error": "Invalid or missing API key"})
    return await call_next(request)

# ── Model Configuration ───────────────────────────────────────────
# Priority: higher = more important to keep loaded
# context_length: what to load it with
# size_gb: approximate memory usage
MODEL_CONFIG = {
    "qwen/qwen3-32b": {
        "priority": 100,
        "context_length": 32768,
        "size_gb": 22,
        "role": "primary",
        "always_load": True,
    },
    "redsage-qwen3-8b-dpo": {
        "priority": 90,
        "context_length": 8192,
        "size_gb": 5,
        "role": "security",
        "always_load": True,
    },
    "microsoft/phi-4": {
        "priority": 70,
        "context_length": 16384,
        "size_gb": 10,
        "role": "coding",
        "always_load": False,
    },
    "deepseek-r1-distill-qwen-32b": {
        "priority": 60,
        "context_length": 32768,
        "size_gb": 17,
        "role": "reasoning",
        "always_load": False,
    },
    "google/gemma-3-27b": {
        "priority": 50,
        "context_length": 8192,
        "size_gb": 18,
        "role": "vision",
        "always_load": False,
    },
}

# Track last used time per model
last_used = {}
TOTAL_MEMORY_GB = 44  # conservative estimate for M3/M5 48GB

# ── LM Studio API ─────────────────────────────────────────────────
def get_loaded_models():
    try:
        r = httpx.get(f"{LM_STUDIO}/api/v1/models", timeout=5)
        models = r.json().get("models", [])
        loaded = {}
        for m in models:
            instances = m.get("loaded_instances", [])
            if instances:
                loaded[m["key"]] = instances[0]["id"]
        return loaded
    except Exception as e:
        return {}

def get_memory_used_gb():
    loaded = get_loaded_models()
    total = 0
    for key in loaded:
        cfg = MODEL_CONFIG.get(key, {})
        total += cfg.get("size_gb", 5)
    return total

def load_model(model_key: str) -> dict:
    cfg = MODEL_CONFIG.get(model_key, {})
    ctx = cfg.get("context_length", 8192)
    try:
        r = httpx.post(
            f"{LM_STUDIO}/api/v1/models/load",
            json={"model": model_key, "context_length": ctx},
            timeout=120
        )
        result = r.json()
        if "instance_id" in result:
            last_used[model_key] = time.time()
            return {"status": "loaded", "model": model_key, "context_length": ctx, "load_time": result.get("load_time_seconds")}
        else:
            return {"status": "error", "model": model_key, "error": result.get("error", {}).get("message", "Unknown")}
    except Exception as e:
        return {"status": "error", "model": model_key, "error": str(e)}

def unload_model(instance_id: str) -> dict:
    try:
        r = httpx.post(
            f"{LM_STUDIO}/api/v1/models/unload",
            json={"instance_id": instance_id},
            timeout=30
        )
        return {"status": "unloaded", "instance_id": instance_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def ensure_model_loaded(model_key: str) -> dict:
    loaded = get_loaded_models()

    # Already loaded
    if model_key in loaded:
        last_used[model_key] = time.time()
        return {"status": "already_loaded", "model": model_key}

    # Check memory
    cfg = MODEL_CONFIG.get(model_key, {})
    needed_gb = cfg.get("size_gb", 5)
    used_gb = get_memory_used_gb()
    available_gb = TOTAL_MEMORY_GB - used_gb

    # Free memory if needed by ejecting lowest priority non-always-load models
    if available_gb < needed_gb:
        loaded_now = get_loaded_models()
        # Sort loaded models by priority (lowest first = eject first)
        # Never eject always_load models
        candidates = []
        for key, iid in loaded_now.items():
            mcfg = MODEL_CONFIG.get(key, {})
            if not mcfg.get("always_load", False):
                candidates.append((mcfg.get("priority", 0), key, iid))
        candidates.sort()  # lowest priority first

        freed = 0
        for priority, key, iid in candidates:
            if freed >= (needed_gb - available_gb):
                break
            print(f"[ModelManager] Ejecting {key} to free memory")
            unload_model(iid)
            freed += MODEL_CONFIG.get(key, {}).get("size_gb", 5)
            time.sleep(2)

    # Load the model
    print(f"[ModelManager] Loading {model_key} (context: {cfg.get('context_length', 8192)})")
    return load_model(model_key)

# ── Startup: ensure always_load models are loaded ─────────────────
def startup_load():
    print("[ModelManager] Checking always_load models...")
    loaded = get_loaded_models()
    for key, cfg in MODEL_CONFIG.items():
        if cfg.get("always_load") and key not in loaded:
            print(f"[ModelManager] Auto-loading {key}...")
            result = ensure_model_loaded(key)
            print(f"[ModelManager] {key}: {result['status']}")
            time.sleep(3)

# ── Endpoints ─────────────────────────────────────────────────────
@app.get("/health")
def health():
    loaded = get_loaded_models()
    return {
        "status": "ok",
        "service": "model_manager",
        "loaded_models": list(loaded.keys()),
        "memory_used_gb": get_memory_used_gb()
    }

@app.get("/models/status")
def models_status():
    loaded = get_loaded_models()
    status = {}
    for key, cfg in MODEL_CONFIG.items():
        status[key] = {
            "loaded": key in loaded,
            "role": cfg["role"],
            "context_length": cfg["context_length"],
            "size_gb": cfg["size_gb"],
            "always_load": cfg["always_load"],
            "last_used": last_used.get(key),
        }
    return {"models": status, "memory_used_gb": get_memory_used_gb(), "total_memory_gb": TOTAL_MEMORY_GB}

class EnsureRequest(BaseModel):
    model_key: str

@app.post("/models/ensure")
def ensure_model(req: EnsureRequest):
    result = ensure_model_loaded(req.model_key)
    return result

@app.post("/models/unload")
def unload(req: EnsureRequest):
    loaded = get_loaded_models()
    if req.model_key not in loaded:
        return {"status": "not_loaded", "model": req.model_key}
    instance_id = loaded[req.model_key]
    return unload_model(instance_id)

@app.post("/models/startup")
def run_startup():
    startup_load()
    return {"status": "startup_complete", "loaded": list(get_loaded_models().keys())}

@app.get("/models/loaded")
def get_loaded():
    loaded = get_loaded_models()
    return {"loaded": list(loaded.keys()), "count": len(loaded)}

if __name__ == "__main__":
    print("[ModelManager] Starting up...")
    startup_load()
    uvicorn.run("model_manager:app", host="127.0.0.1", port=8100, reload=False)
