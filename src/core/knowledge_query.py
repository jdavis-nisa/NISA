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
        "owasp", "injection", "xss", "sql injection", "firewall", "encryption",
        "penetration testing", "pentest", "forensic", "ioc", "siem", "ids", "ips",
        "zero day", "ransomware", "phishing", "social engineering", "cipher",
        "authentication", "authorization", "privilege escalation", "reverse shell",
        "payload", "metasploit", "burp suite", "nmap scan", "network scan",
        "intrusion detection", "security audit", "threat hunting", "red team",
        "blue team", "incident response", "malware analysis", "rootkit",
        "buffer overflow", "memory corruption", "code execution"
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
        "signal intelligence", "sigint", "direction finding radar",
        "electronic countermeasure", "ecm", "eccm"
    ],
    "nisaba_soul": [
        "nisaba", "your personality", "who are you", "your values",
        "your purpose", "your identity", "your history", "your character",
        "your name", "what are you", "tell me about yourself"
    ],
    "nisa_docs": [
        "nisa", "your capabilities", "what can you do", "your architecture",
        "your models", "your apis", "your features", "how were you built",
        "nisa platform", "nisa system", "nisa version"
    ],
    "health": [
        "medical", "health", "anatomy", "physiology", "diagnosis", "treatment",
        "medication", "symptom", "disease", "injury", "trauma", "combat medicine",
        "first aid", "emergency medicine", "triage", "wound care", "hemorrhage",
        "tourniquet", "iv access", "airway management", "tccc", "tactical casualty",
        "nurse practitioner", "clinical", "patient care", "drug dosage",
        "pharmacology", "nutrition", "exercise physiology", "mental health",
        "ptsd", "traumatic brain injury", "tbi"
    ],
    "creative_writing": [
        "novel", "story", "narrative", "character", "plot", "fiction",
        "creative writing", "prose", "scene", "dialogue", "point of view",
        "world building", "character development", "story arc", "manuscript",
        "elijah freeman", "beyond the veil", "soul blueprint", "bury the living",
        "jack raines", "sierra", "writing craft", "show dont tell",
        "literary device", "metaphor", "symbolism", "theme", "motif"
    ],
    "social_dynamics": [
        "communication", "relationship", "social dynamics", "body language",
        "negotiation", "conflict resolution", "leadership", "influence",
        "persuasion", "emotional intelligence", "interpersonal", "networking",
        "team dynamics", "organizational behavior", "workplace", "management",
        "collaboration", "feedback", "difficult conversation", "assertiveness"
    ],
    "spiritual_advanced": [
        "consciousness", "astral projection", "out of body experience", "obe",
        "remote viewing", "gateway experience", "monroe institute", "hemi-sync",
        "lucid dreaming", "altered states", "meditation advanced", "kundalini",
        "akashic records", "higher self", "soul travel", "binaural beats",
        "theta state", "delta state", "third eye", "pineal gland",
        "manifestation", "law of attraction", "synchronicity", "collective consciousness"
    ],
    "mathematics_advanced": [
        "linear algebra", "matrix multiplication", "eigenvalue", "eigenvector",
        "calculus", "differential equations", "partial differential", "fourier transform",
        "laplace transform", "z transform", "probability theory", "statistics",
        "bayesian", "optimization", "convex optimization", "numerical methods",
        "signal processing math", "spectral analysis", "stochastic process",
        "information theory", "entropy", "mutual information"
    ],
    "physics_advanced": [
        "electromagnetism", "maxwell equations", "wave propagation",
        "antenna theory", "rf propagation", "microwave", "electromagnetic",
        "quantum mechanics", "wave function", "schrodinger", "relativity",
        "thermodynamics", "fluid dynamics", "optics", "photonics",
        "plasma physics", "semiconductor physics", "solid state physics"
    ],
    "quantum_advanced": [
        "quantum computing", "qubit", "quantum entanglement", "quantum cryptography",
        "quantum key distribution", "qkd", "post-quantum", "lattice cryptography",
        "quantum algorithm", "shor algorithm", "grover algorithm",
        "quantum error correction", "quantum decoherence", "quantum supremacy",
        "quantum annealing", "topological qubit"
    ],
    "music": [
        "music theory", "chord progression", "melody", "harmony", "rhythm",
        "hip hop", "rap", "lyrics", "rhyme scheme", "flow", "cadence",
        "beat making", "production", "mixing", "mastering", "recording",
        "internal rhyme", "multisyllabic", "wordplay", "bars", "verse",
        "hook", "bridge", "song structure", "jazz theory", "blues scale"
    ],
    "gardening": [
        "gardening", "plants", "soil", "compost", "fertilizer", "pruning",
        "irrigation", "garden bed", "vegetable garden", "herb garden",
        "permaculture", "companion planting", "pest control organic",
        "seed starting", "transplanting", "crop rotation", "raised bed"
    ],
    "philosophy": [
        "philosophy", "ethics", "epistemology", "ontology", "metaphysics",
        "logic", "reasoning", "argument", "consciousness philosophy",
        "free will", "determinism", "moral philosophy", "existentialism",
        "stoicism", "phenomenology", "philosophy of mind"
    ],
    "psychology": [
        "psychology", "cognitive", "behavioral", "therapy", "trauma",
        "attachment theory", "cognitive bias", "motivation", "habit formation",
        "neuroplasticity", "mindset", "resilience", "stress response",
        "emotional regulation", "self awareness", "introspection"
    ],
    "spirituality": [
        "prayer", "faith", "biblical", "scripture", "meditation", "mindfulness",
        "spiritual growth", "divine", "sacred", "ceremony", "ritual",
        "indigenous wisdom", "comanche", "navajo", "shamanism", "healing"
    ],
    "history": [
        "history", "historical", "world war", "military history", "ancient",
        "civilization", "empire", "revolution", "war strategy", "tactics",
        "battle", "historical figure", "timeline", "era", "period"
    ],
    "programming": [
        "programming", "coding", "software development", "algorithm",
        "data structure", "object oriented", "functional programming",
        "design pattern", "api design", "database design", "system design",
        "debugging", "testing", "version control", "devops", "deployment"
    ],
    "technology": [
        "artificial intelligence", "machine learning", "deep learning",
        "neural network", "large language model", "transformer", "gpu",
        "cloud computing", "distributed systems", "microservices",
        "kubernetes", "docker", "networking", "protocol", "internet of things"
    ],
    "physics": [
        "physics", "mechanics", "newton", "force", "energy", "momentum",
        "gravity", "magnetism", "electricity", "circuit", "wave", "frequency",
        "wavelength", "speed of light", "nuclear", "atomic"
    ],
    "mathematics": [
        "algebra", "geometry", "trigonometry", "arithmetic", "number theory",
        "proof", "theorem", "equation", "formula", "integral", "derivative",
        "function", "graph theory", "combinatorics", "set theory"
    ],
    "writing_craft": [
        "writing craft", "storytelling", "narrative structure", "story beats",
        "hero journey", "three act structure", "pacing", "tension",
        "exposition", "climax", "resolution", "voice", "style", "tone",
        "grammar", "editing", "revision", "beta reader"
    ],
    "poetry": [
        "poetry", "poem", "verse", "stanza", "meter", "iambic pentameter",
        "sonnet", "haiku", "free verse", "rhyme", "alliteration", "assonance",
        "imagery", "figurative language", "spoken word", "slam poetry"
    ],
    "resume_career": [
        "resume", "career", "job application", "cover letter", "interview",
        "salary negotiation", "linkedin", "portfolio", "certification",
        "professional development", "career change", "networking professional",
        "job search", "defense contractor", "clearance", "redstone arsenal",
        "leidos", "boeing", "saic", "northrop grumman", "booz allen"
    ],
    "research": [
        "research", "paper", "academic", "study", "methodology", "literature review",
        "citation", "peer reviewed", "arxiv", "ieee", "scientific method",
        "hypothesis", "experiment", "data analysis", "findings"
    ],
    "quantum_technology": [
        "quantum sensor", "quantum radar", "quantum communication",
        "quantum internet", "quantum repeater", "quantum memory",
        "quantum dot", "nitrogen vacancy", "quantum metrology"
    ],
    "certifications": [
        "certification", "comptia", "security plus", "cissp", "ceh",
        "oscp", "aws certification", "azure certification", "ccna",
        "exam prep", "study guide", "practice test"
    ],
    "logic_puzzles": [
        "logic puzzle", "riddle", "brain teaser", "problem solving",
        "lateral thinking", "deductive reasoning", "inductive reasoning",
        "game theory", "strategy puzzle", "chess", "cryptogram"
    ],
    "survival": [
        "survival", "bushcraft", "wilderness", "emergency preparedness",
        "bug out", "foraging", "shelter building", "fire making",
        "water purification", "navigation", "first aid wilderness"
    ],
    "finances": [
        "finance", "budget", "investment", "stock market", "cryptocurrency",
        "tax", "retirement", "savings", "debt", "credit", "real estate",
        "passive income", "financial planning", "portfolio management"
    ],
    "paradoxes": [
        "paradox", "contradiction", "impossible", "zeno", "fermi paradox",
        "bootstrap paradox", "grandfather paradox", "time travel paradox",
        "liar paradox", "russell paradox"
    ],
    "social_dynamics": [
        "communication", "relationship", "social dynamics", "body language",
        "negotiation", "conflict resolution", "leadership", "influence"
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

        clean = re.sub(r"\[Data:.*?\]", "", output)
        clean = re.sub(r"\s+", " ", clean).strip()

        if len(clean) < 50:
            return None

        return f"[Knowledge Graph - {domain}]\n{clean}"

    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def get_knowledge_context(query: str) -> str:
    """Get relevant knowledge context for a query"""
    return query_knowledge_graph(query)
