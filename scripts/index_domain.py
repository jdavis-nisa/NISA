#!/usr/bin/env python3.11
"""Queue GraphRAG indexing for a knowledge domain"""
import subprocess, os, sys, time

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"
LOG_BASE = os.path.expanduser("~/NISA/logs")

def index_domain(domain):
    path = os.path.join(SSD_BASE, domain)
    log = os.path.join(LOG_BASE, f"graphrag_{domain}.log")
    settings = os.path.join(path, "settings.yaml")
    if not os.path.exists(settings):
        print(f"ERROR: No settings.yaml for {domain}")
        return None
    p = subprocess.Popen(
        ["python3.11", "-m", "graphrag", "index", "--root", path],
        stdout=open(log, "w"),
        stderr=subprocess.STDOUT
    )
    print(f"Indexing {domain} - PID {p.pid} - log: graphrag_{domain}.log")
    return p

if __name__ == "__main__":
    domains = sys.argv[1:] if len(sys.argv) > 1 else []
    if not domains:
        print("Usage: python3.11 index_domain.py domain1 domain2 ...")
        sys.exit(1)
    for domain in domains:
        index_domain(domain)
        time.sleep(2)
