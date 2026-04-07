#!/usr/bin/env python3.11
"""
NISA Knowledge Watcher
Monitors SSD knowledge folders for new documents and auto-indexes them with GraphRAG
Run: python3.11 ~/NISA/knowledge/watcher.py
"""
import os
import sys
import time
import subprocess
import hashlib
import json
from datetime import datetime

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"
NISA_DIR = "/Users/joshuadavis/NISA"
STATE_FILE = f"{NISA_DIR}/knowledge/watcher_state.json"
LOG_FILE = f"{NISA_DIR}/logs/watcher.log"

INDEXED_DOMAINS = ["security", "radar_ew", "general", "nisaba_soul", "nisa_docs"]

SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf", ".docx", ".doc",
    ".py", ".js", ".json", ".yaml", ".csv"
}

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def file_hash(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(8192))
    return h.hexdigest()

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def scan_domain(domain: str, state: dict) -> list:
    domain_path = os.path.join(SSD_BASE, domain)
    if not os.path.exists(domain_path):
        return []
    new_files = []
    for root, dirs, files in os.walk(domain_path):
        dirs[:] = [d for d in dirs if d not in ["input", "output", "cache", "logs", "prompts"]]
        for fname in files:
            if fname.startswith("._") or fname.startswith("."):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            fpath = os.path.join(root, fname)
            try:
                fhash = file_hash(fpath)
                key = fpath
                if key not in state or state[key] != fhash:
                    new_files.append(fpath)
                    state[key] = fhash
            except Exception as e:
                log(f"Error scanning {fpath}: {e}")
    return new_files

def copy_to_input(files: list, domain: str):
    input_dir = os.path.join(SSD_BASE, domain, "input")
    os.makedirs(input_dir, exist_ok=True)
    copied = []
    for fpath in files:
        fname = os.path.basename(fpath)
        dest = os.path.join(input_dir, fname)
        try:
            with open(fpath, "rb") as src, open(dest, "wb") as dst:
                dst.write(src.read())
            copied.append(fname)
        except Exception as e:
            log(f"Error copying {fname}: {e}")
    return copied

def run_graphrag_index(domain: str) -> bool:
    domain_path = os.path.join(SSD_BASE, domain)
    graphrag_config = os.path.join(domain_path, "settings.yaml")
    if not os.path.exists(graphrag_config):
        log(f"No GraphRAG config for domain: {domain} - skipping indexing")
        return False
    log(f"Running GraphRAG indexing for domain: {domain}")
    try:
        result = subprocess.run(
            ["python3.11", "-m", "graphrag", "index", "--root", domain_path],
            capture_output=True, text=True, timeout=3600,
            cwd=domain_path
        )
        if "Pipeline complete" in result.stdout:
            log(f"GraphRAG indexing complete for {domain}")
            return True
        else:
            log(f"GraphRAG indexing issue for {domain}: {result.stdout[-500:]}")
            return False
    except Exception as e:
        log(f"GraphRAG indexing error for {domain}: {e}")
        return False

def watch(interval: int = 300):
    log("NISA Knowledge Watcher starting...")
    log(f"Monitoring: {SSD_BASE}")
    log(f"Indexed domains: {INDEXED_DOMAINS}")
    log(f"Check interval: {interval}s")
    state = load_state()
    while True:
        try:
            for domain in os.listdir(SSD_BASE):
                domain_path = os.path.join(SSD_BASE, domain)
                if not os.path.isdir(domain_path):
                    continue
                new_files = scan_domain(domain, state)
                if not new_files:
                    continue
                log(f"Found {len(new_files)} new/changed files in {domain}")
                for f in new_files:
                    log(f"  + {os.path.basename(f)}")
                if domain in INDEXED_DOMAINS:
                    copied = copy_to_input(new_files, domain)
                    if copied:
                        log(f"Copied {len(copied)} files to {domain}/input")
                        run_graphrag_index(domain)
                save_state(state)
        except Exception as e:
            log(f"Watcher error: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    watch(interval)
