# NISA Build Checklist — Version 7.1
Last Updated: April 7, 2026
Current Status: Phase 3 in progress - knowledge graph + tool expansion

WEEK 1 — Foundation COMPLETE
[x] macOS setup, Xcode, Homebrew, Python 3.11, Git, Node, CMake
[x] VS Code with extensions
[x] GitHub account - jdavis-nisa
[x] SSH key, NISA repository created
[x] NISA folder structure
[x] NISABA_SOUL.md committed
[x] README.md committed
[x] Python dependencies installed

WEEK 2 — AI Layer COMPLETE
[x] LM Studio with developer mode
[x] Qwen 3 32B MLX 4BIT (18.45GB)
[x] DeepSeek R1 Distill 32B (18.78GB)
[x] RedSage 8B DPO (4.80GB)
[x] Phi-4 14B (9.05GB)
[x] Gemma 3 27B (16.87GB, vision capable)
[x] Nisaba system prompt applied
[x] DEVLOG.md established
[x] LM Studio local server on localhost:1234
[x] test_api.py confirmed
[x] SECURITY/AIBOM.md created

WEEK 3 — Docker and Infrastructure COMPLETE
[x] Docker Desktop v4.67.0
[x] docker-compose.yml - PostgreSQL + ChromaDB + Redis
[x] All 3 containers running and healthy
[x] Neo4j Desktop installed and running
[x] .env file created, .gitignore protecting secrets

WEEK 4 — Voice Pipeline COMPLETE (TTS bookmarked)
[x] Whisper.cpp 1.8.4
[x] Whisper base.en and medium.en
[x] Piper TTS 1.4.2
[x] en_GB-alba-medium (Nisaba voice)
[x] voice_pipeline.py - STT confirmed working
[x] TTS voice output - WORKING (afplay + markdown stripping)

WEEKS 5-6 — Intelligence Core COMPLETE
[x] nlu_api.py - FastAPI router port 8081
[x] Intelligent routing - security/reasoning/general/MoA
[x] moa_pipeline.py - Mixture of Agents
[x] memory.py - ChromaDB persistent memory (164+ entries)
[x] audit_trail.py - HMAC-SHA256 cryptographic logging
[x] NLU API integrates memory + MoA + audit trail
[x] Arize Phoenix observability - LLM tracing on every request

PHASE 2 — Cybersecurity Platform COMPLETE
[x] Nmap container (nisa_nmap - Nmap 7.98 aarch64)
[x] OWASP ZAP container (nisa_zap - healthy, port 8090)
[x] security_api.py - FastAPI port 8082
[x] JIT token system - UUID tokens, 60s expiry, one-time use
[x] Nmap scan endpoint - structured JSON confirmed
[x] ZAP web scan endpoint - spider + passive scan + alerts
[x] RedSage wired into all security scan analysis
[x] forensics_api.py - FastAPI port 8083
    [x] Log analysis - 13 suspicious event types
    [x] IOC extraction - IPv4, domains, hashes, URLs, CVEs
    [x] File hash verification - SHA256 + MD5
    [x] Timeline reconstruction
    [x] RedSage analysis on every finding
[x] PyRIT 0.12.0 - adversarial red team - 4/4 defended (100%)
[x] OWASP LLM Top 10 evaluation - 50 cases, 81% score
[x] Garak 0.14.1 - CLI integration working
    [x] REST generator config established
    [x] DAN probe baseline: DC-2, 9% defense score (false positive heavy)
    [x] HTML report generation confirmed
[x] Compliance PDF generator - ReportLab, pulls from audit_log2
[x] Arize Phoenix - LLM observability on port 6006
[x] Tagged v0.2.0

RED TEAM SUITE COMPLETE
[x] red_team_api.py - FastAPI port 8084
[x] red_team_sessions table in PostgreSQL
[x] PyRIT attack runner - multi-turn adversarial sequences
[x] OWASP attack runner - full 50-case suite
[x] Garak attack runner - DAN + encoding probes
[x] Live session polling - turn-by-turn results
[x] Session history - all runs stored in PostgreSQL
[x] Regression history endpoint - by version

REACT WEB UI COMPLETE - 6 TABS
[x] Vite + React, Tailwind CSS, recharts, react-markdown
[x] Dark navy theme, gold accents, subtle grid background
[x] Rajdhani + JetBrains Mono + Outfit font stack
[x] Chat - markdown rendering, syntax highlighting, copy button
[x] Security - Nmap + ZAP scan panels with RedSage analysis
[x] Forensics - log analysis, IOC extractor, file hash
[x] Memory - ChromaDB explorer with semantic search
[x] Red Team - launch panel, live feed, history, regression chart
[x] Compliance - audit log table + PDF generation
[x] 5 API status dots in header
[x] CORS fixed on all APIs

SESSION TOOLING COMPLETE
[x] scripts/start_nisa.sh - one command startup (7 services)
[x] logs/ directory for all API logs

PHASE 3 — Knowledge Graph, Automation, and Tool Expansion NEXT

Knowledge Graph and RAG
[x] Mount Samsung T9 2TB external SSD - /Volumes/Share Drive
[x] Create 18 knowledge domains on SSD
[x] Install GraphRAG 3.0.8
[x] Configure GraphRAG for LM Studio (security, radar_ew, general, nisaba_soul, nisa_docs)
[x] Security domain indexed and querying confirmed
[x] Write knowledge/watcher.py - auto-ingestion every 5 minutes
[x] Copy NISA docs to nisa_docs domain
[ ] Wire GraphRAG into NLU API - Nisaba queries knowledge graph
[ ] Populate security knowledge library (CVEs, NIST, OWASP docs)
[ ] Populate radar_ew library (IEEE papers, dad's research)
[ ] Populate nisaba_soul library
[ ] Build music library on SSD
[ ] Implement multi-hop forensic search
[ ] Configure Arize Phoenix semantic drift monitoring
[ ] Install AnythingLLM - self-hosted RAG interface
[ ] Build task scheduler and learning engine

Security Tool Expansion
[x] Install tshark 4.6.4 (Wireshark CLI)
[x] Install Burp Suite Community Edition
[x] Install Suricata 8.0.4
[ ] Add tshark pcap analysis to forensics_api.py
[ ] Deploy Suricata IDS container - live network threat detection
[ ] Wire Suricata alerts into NISA UI
[ ] Deploy Kali Linux container
[ ] Install Metasploit in Kali container - BOOKMARKED (Rosetta issue)
[ ] Add UI voice activation button - microphone toggle in Chat tab

Cryptography Upgrade
[ ] Research CRYSTALS-Dilithium and FALCON post-quantum signing
[ ] Replace HMAC-SHA256 audit trail with quantum-resistant algorithm
[ ] Document quantum-resistant cryptography in AIBOM
[ ] Update compliance PDF to reflect new signing algorithm

Fine-tuning and Mobile
[ ] Begin fine-tuning dataset collection
[ ] Fine-tune Phi-4 14B on security domain via MLX-LM LoRA
[ ] React Native mobile app
[ ] Full NISA demo video for portfolio
[ ] Tag v0.3.0

PHASE 4 — Radar and Electronic Warfare
[ ] Radar knowledge graph (IEEE papers, technical standards)
[ ] Signal processing sandbox (NumPy, SciPy, radarsimpy)
[ ] GNU Octave - brew install octave
[ ] Waveform analysis and ambiguity function visualization
[ ] EW threat modeling framework
[ ] Fine-tune Phi-4 14B on radar corpus
[ ] Tag v0.4.0

BOOKMARKED ITEMS
- Kali Linux container - deferred
- audit_log table - use audit_log2 only
- Garak DAN false positive rate - needs custom detector

INFRASTRUCTURE PORTS
Service         Port    Status
LM Studio       1234    Manual (open app)
NLU API         8081    Auto (start_nisa.sh)
Security API    8082    Auto (start_nisa.sh)
Forensics API   8083    Auto (start_nisa.sh)
Red Team API    8084    Auto (start_nisa.sh)
PostgreSQL      5432    Auto (Docker)
ChromaDB        8000    Auto (Docker)
Redis           6379    Auto (Docker)
Neo4j           7687    Manual (Neo4j Desktop)
OWASP ZAP       8090    Auto (Docker)
Phoenix         6006    Auto (start_nisa.sh)
Vite UI         5173    Manual (npm run dev)

WHAT NISA CAN DO RIGHT NOW
Capability                          Status
Intelligent model routing (5)       WORKING
Mixture of Agents reasoning         WORKING
Persistent memory (164+ entries)    WORKING
Cryptographic audit trail           WORKING
Voice STT                           WORKING
Voice TTS                           WORKING
Nmap network scanning               WORKING
OWASP ZAP web scanning              WORKING
JIT security permissions            WORKING
PyRIT adversarial red team          WORKING - 100% defended
OWASP LLM Top 10 evaluation         WORKING - 81% score
Garak vulnerability scanning        WORKING - CLI integrated
RedSage security analysis           WORKING - all scans
Forensics log analysis              WORKING - CRITICAL detection
IOC extraction                      WORKING
File hash verification              WORKING
Arize Phoenix observability         WORKING
Memory Explorer UI                  WORKING - semantic search
Red Team Operations UI              WORKING - live feed + regression
Compliance PDF reports              WORKING
React Web UI (6 tabs)               WORKING
One command startup (7 services)    WORKING

NISA Build Checklist v6.0
github.com/jdavis-nisa/NISA
Built by Josh Davis - Huntsville, Alabama - 2026
