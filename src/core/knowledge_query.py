#!/usr/bin/env python3.11
"""
NISA Knowledge Query Module
Queries GraphRAG knowledge graphs and returns context for NLU API
"""
import subprocess
import os
import re

SSD_BASE = "/Volumes/Share Drive/NISA/knowledge"

DOMAIN_KEYWORDS = {
    "security": [
        "vulnerability", "exploit", "attack", "malware", "threat", "cve",
        "owasp", "injection", "xss", "sql", "firewall", "encryption",
        "penetration", "pentest", "forensic", "ioc", "siem", "ids", "ips",
        "zero day", "ransomware", "phishing", "social engineering", "cipher",
        "authentication", "authorization", "privilege", "escalation"
    ],
    "radar_ew": [
        "radar system", "radar signal", "radar waveform", "radar cross section",
        "phased array", "phased-array", "beamforming", "beam steering",
        "electronic warfare", "electronic attack", "electronic protection",
        "electronic support", "ew system", "ew threat",
        "fmcw", "frequency modulated continuous wave",
        "pulse compression", "matched filter radar",
        "doppler radar", "doppler shift", "doppler frequency",
        "radar antenna", "antenna gain", "radar range equation",
        "low probability of intercept", "lpi radar", "lpi waveform",
        "noise jamming", "barrage jamming", "deception jamming",
        "range gate pull", "velocity gate pull", "radar jamming",
        "radar warning receiver", "rwr", "threat library",
        "synthetic aperture radar", "sar imaging",
        "moving target indicator", "mti filter",
        "constant false alarm", "cfar detector",
        "space-time adaptive", "stap processing",
        "aesa radar", "active electronically scanned",
        "radar clutter", "ground clutter", "sea clutter",
        "polyphase code", "frank code", "chirp waveform",
        "frequency hopping radar", "pulse repetition",
        "target detection radar", "target tracking radar",
        "anti-radiation missile", "harm missile",
        "signal intelligence", "sigint", "direction finding radar"
    ],
    "nisaba_soul": [
        "nisaba", "your personality", "who are you", "your values",
        "your purpose", "your identity", "your history", "your character"
    ],
    "nisa_docs": [
        "nisa", "your capabilities", "what can you do", "your architecture",
        "your models", "your apis", "your features", "how were you built"
    ],
    "general": []
}

def detect_domain(query: str) -> str:
    """Detect which knowledge domain is most relevant for a query"""
    query_lower = query.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[domain] = score
    if not scores:
        return None
    return max(scores, key=scores.get)

def query_knowledge_graph(query: str, domain: str = None) -> str:
    """Query a GraphRAG knowledge domain and return the response"""
    if domain is None:
        domain = detect_domain(query)
    if domain is None:
        return None

    domain_path = os.path.join(SSD_BASE, domain)
    settings_path = os.path.join(domain_path, "settings.yaml")
    output_path = os.path.join(domain_path, "output")

    if not os.path.exists(settings_path):
        return None
    if not os.path.exists(output_path):
        return None

    try:
        result = subprocess.run(
            ["python3.11", "-m", "graphrag", "query",
             "-r", domain_path,
             "-m", "local",
             query],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout.strip()
        if not output:
            return None

        # Clean up GraphRAG citation markers for cleaner integration
        clean = re.sub(r"\[Data:.*?\]", "", output)
        clean = re.sub(r"\s+", " ", clean).strip()

        if len(clean) < 50:
            return None

        return f"[Knowledge Graph - {domain}]\n{clean}"

    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None

def get_knowledge_context(query: str) -> str:
    """Get relevant knowledge context for a query - returns None if no relevant domain"""
    return query_knowledge_graph(query)
