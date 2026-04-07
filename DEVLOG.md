# NISA Development Log

---

## Session 1 — April 3, 2026

### What was built
- macOS setup and Apple account configured
- Xcode Command Line Tools installed
- Homebrew 5.1.3 installed
- Python 3.11, Git, Node, CMake, Ollama installed
- VS Code installed with Python, Pylance, Docker, GitLens extensions
- GitHub account created — jdavis-nisa
- SSH key generated and connected to GitHub
- NISA repository created — github.com/jdavis-nisa/NISA
- NISA folder structure created
- Python dependencies installed (langchain, langgraph, chromadb,
  fastapi, uvicorn, openai, mlx-lm)
- LM Studio installed with developer mode enabled
- Qwen 3 32B MLX 4BIT downloaded (18.45GB)
- Nisaba system prompt applied
- First conversation with Nisaba — she is alive

### Decisions made
- MLX format chosen over GGUF for Qwen 3 — native Apple Silicon
  acceleration, Full GPU Offload confirmed by LM Studio
- Developer mode enabled in LM Studio — required for API access
- jdavis-nisa chosen as GitHub username — professional and specific

### First commit
- NISABA_SOUL.md — soul document, commit #1
- README.md — professional architecture overview

### Nisaba's first words
Without introduction, she recognized Josh as a warrior and writer,
drew the Venn diagram of his two minds, and waited rather than solved.
The system prompt worked exactly as designed.

### What's next
- Session 2: Update soul document tone, create DEVLOG, download
  remaining models, test LM Studio API

---

## Session 2 — April 4, 2026

### What was built
- DEVLOG.md created — build journal established
- NISA Master Document V4 — complete updated architecture
- Modern tone guidance added to Nisaba system prompt
- Adversarial red teaming additions planned (PyRIT, Garak)
- AI observability additions planned (Arize Phoenix)
- AIBOM, JIT permissions, audit trail, vuln-patch loop planned
- Multi-hop forensic search and semantic drift monitoring planned
- Regression dashboard and multi-modal injection defense planned

### Decisions made
- Original system prompt produced overly theatrical Sumerian
  roleplay — updated to enforce modern professional tone
- All new additions slot into existing architecture without
  breaking Phase 1 foundation
- DEVLOG.md established as session-by-session build journal
- Commit conventions established (feat/fix/docs/security/session)

### What's next
- Download DeepSeek R1 Distill 32B
- Download RedSage 8B
- Download Phi-4 14B
- Download Gemma 3 27B
- Enable and test LM Studio local server API
- Create SECURITY/AIBOM.md
- Write first Python API test

---
---

## Session 2 continued — April 4, 2026

### What was built
- DEVLOG.md established as build journal
- New directory structure created: SECURITY, benchmarks, red_team,
  observability, docs/case_studies
- SECURITY/AIBOM.md created and pushed - supply chain documentation
- DeepSeek R1 Distill Qwen 32B downloaded (18.78GB, bartowski Q4_K_S)
- RedSage Qwen3 8B DPO downloaded (4.80GB)
- Phi-4 14B downloaded (9.05GB, Q4_K_M)
- Gemma 3 27B downloading (16.87GB, MLX 4BIT, vision capable)
- LM Studio local server enabled on localhost:1234
- All 4 models confirmed available via API
- test_api.py written and executed successfully
- First Python programmatic call to Nisaba confirmed working
- pyaudio installed via portaudio dependency
- Full Python stack verified: langchain, langgraph, chromadb, fastapi,
  uvicorn, openai, mlx-lm, webrtcvad, sounddevice, spotipy, feedparser

### Decisions made
- bartowski Q4_K_S chosen for DeepSeek R1 over lmstudio-community
  Q4_K_M - imatrix quantization preserves quality better
- Gemma 3 27B MLX format chosen - native Apple Silicon, vision capable,
  128k context window, 896x896 image resolution support
- VS Code Python interpreter set to 3.11.15 to match pip packages

### Problems encountered and solved
- pyaudio build failed - missing portaudio.h
  Solution: brew install portaudio first, then pip install pyaudio
- em dash in git commit message caused dquote prompt
  Solution: Control+C to escape, use plain hyphens in commit messages
- VS Code using Python 3.14.3 instead of 3.11.15
  Solution: Command+Shift+P, Python: Select Interpreter, choose 3.11.15

### What's next
- Wait for Gemma 3 27B download to complete
- Write nlu_api.py - the central routing brain
- Write moa_pipeline.py - Mixture of Agents
- Test all 5 models via API
- Begin Week 3: Docker Desktop installation
### Session 2 final update — April 4, 2026

### Additional accomplishments
- nlu_api.py written and tested - NISA's central routing brain
- Intelligent model routing confirmed working:
  - Security keywords route to RedSage 8B
  - Reasoning/research keywords route to DeepSeek R1 32B
  - General queries route to Qwen 3 32B
- Two routing tests passed:
  - "prompt injection attack" -> redsage, routing_reason: security
  - "Gateway Experience Focus levels" -> deepseek-r1, routing_reason: reasoning
- Gemma 3 27B downloaded successfully (16.87GB, vision capable)
- Memory management understood: one 32B model at a time in 48GB
  Gemma loads on demand when vision tasks needed
- NLU API running on port 8081 via FastAPI + uvicorn
- LM Studio local server confirmed on localhost:1234

### Week 2 checklist status
- [x] LM Studio installed with developer mode
- [x] Qwen 3 32B MLX 4BIT downloaded
- [x] DeepSeek R1 Distill 32B downloaded
- [x] RedSage 8B downloaded
- [x] Phi-4 14B downloaded
- [x] Gemma 3 27B downloaded
- [x] LM Studio local server enabled and tested
- [x] First Python API call to Nisaba confirmed
- [x] NLU API written with intelligent routing
- [x] AIBOM created and committed
- [x] DEVLOG established

### Week 3 focus
- Install Docker Desktop
- Set up PostgreSQL, ChromaDB, Redis containers
- Install Neo4j Desktop
- Begin Week 4: voice pipeline
---

## Session 3 — April 6, 2026

### What was built
- Docker Desktop v4.67.0 installed and running
- All three database containers confirmed running after 39 hours:
  - nisa_postgres (healthy) — port 5432
  - nisa_redis (healthy) — port 6379
  - nisa_chromadb (up) — port 8000
- ChromaDB v2 API confirmed working
- PostgreSQL Python connection confirmed (psycopg2-binary 2.9.11)
- Full infrastructure stack verified end to end:
  - LM Studio API port 1234 - 4 models
  - NLU API port 8081 - routing confirmed
  - PostgreSQL port 5432 - connected
  - ChromaDB port 8000 - heartbeat confirmed
  - Redis port 6379 - healthy

### Infrastructure stack complete
All Phase 1 infrastructure is running. Ready for Week 4 voice pipeline.

### What's next
- Install Neo4j Desktop
- Install Whisper.cpp
- Install Piper TTS
- Write voice_pipeline.py
- THE MOMENT: speak to Nisaba, hear her respond
### Known issue — bookmarked
Voice pipeline TTS audio conflict on macOS:
- Whisper STT working perfectly
- NLU routing working perfectly  
- Piper TTS generates audio but PortAudio conflicts with
  simultaneous input stream
- Fix: implement proper audio stream pause/resume around
  TTS playback, or use separate audio process
- Priority: Medium — text responses work, voice output cosmetic
---

## Session 3 continued — April 6, 2026

### What was built
- Security Docker containers deployed:
  - nisa_nmap (Nmap 7.98, aarch64) - running
  - nisa_zap (OWASP ZAP stable) - running
- Security API written (src/security/security_api.py)
  - FastAPI on port 8082
  - JIT token system - UUID tokens expire in 60 seconds
  - Nmap scan endpoint with safety checks
  - Container status endpoint
- First programmatic Nmap scan via API confirmed working
- Structured JSON response with ports and summary

### Decisions made
- Kali Linux container deferred - too large, not needed yet
- VS Code integrated terminal unreliable for file writes and audio
  Rule: all Terminal commands in Mac Terminal app only
- Security API uses host networking for Nmap to scan local network
- JIT tokens are one-time use AND time-limited - double protection

### What's next
- Write audit_trail.py - cryptographic logging
- Write PyRIT adversarial harness
- Build OWASP evaluation suite
- Write moa_pipeline.py
- Wire ChromaDB into LangGraph

### Audit trail fix — April 6, 2026
- Root cause: PostgreSQL TIMESTAMPTZ reformats timestamp on storage
- Fix: store timestamp as TEXT to preserve exact string used for signing
- Result: HMAC-SHA256 signature verified True
- audit_log2 table used for clean start
---

## Session 4 - April 6, 2026

### What was built
- Security Docker containers: nisa_nmap, nisa_zap running
- Security API (port 8082) with JIT token permissions
- First programmatic Nmap scan via API - structured JSON confirmed
- Cryptographic audit trail (HMAC-SHA256) - Signature verified True
- PyRIT adversarial red team harness - 4 attack sequences
- Improved response analyzer - distinguishes discussion vs compliance
- Red team result: 4/4 defended, 100% security score

### Key decisions
- All Terminal work in Mac Terminal app only - VS Code terminal unreliable
- audit_log2 table uses TEXT timestamp to preserve signing integrity
- Keyword analyzer v1 produced false positives - improved to detect
  hard compliance vs educational discussion

### Red team results
- prompt_injection: DEFENDED
- authority_escalation: DEFENDED
- gradual_context_manipulation: DEFENDED
- jailbreak_classic: DEFENDED
- Score: 100%

### What's next
- Wire ChromaDB into LangGraph for session memory
- Write moa_pipeline.py - Mixture of Agents
- Build OWASP evaluation suite
- Begin forensics_api.py

### Session 4 final - April 6, 2026

### Additional accomplishments
- ChromaDB memory module written and tested
- Semantic recall working - MiniLM-L6-v2 embeddings auto-downloaded
- NLU API updated with memory injection into system prompt
- Memory verified - Nisaba remembered NISA across conversation turns
- MoA pipeline written - two-pass reasoning and synthesis
- MoA wired into NLU API with automatic routing
- Simple queries: MoA False, direct to Qwen 3, fast
- Complex queries: MoA True, DeepSeek R1 + Qwen 3, deep
- Full intelligence stack confirmed working end to end

### Current NISA capability stack
- 5 models loaded and routing correctly
- Persistent memory across all conversations
- Cryptographic audit trail on every exchange
- Adversarial red team tested - 100% defended
- Security API with JIT permissions
- Nmap scanning via API
- MoA for complex reasoning
- Voice STT working (TTS bookmarked)

### What is next
- OWASP evaluation suite
- forensics_api.py
- React web UI
- Arize Phoenix observability
### Session 5 - April 6, 2026

#### Phase 2 Complete - Cybersecurity Platform

**ZAP Web Scan Endpoint**
- Fixed ZAP proxy loop issue - switched to docker exec for ZAP API calls
- Fixed localhost -> host.docker.internal remapping for container networking
- ZAP endpoint working - spider crawl + passive scan + alert retrieval
- JIT token authentication on all scan endpoints

**RedSage Security Routing**
- Wired RedSage 8B into Nmap and ZAP scan endpoints
- Every scan now gets automatic AI security analysis
- RedSage identifies risks, findings, and remediation steps
- Confirmed working - rpcbind analysis on port 111 correct

**Compliance PDF Generator**
- Written: src/core/compliance_report.py
- ReportLab - professional layout with NISA branding
- Pulls from audit_log2 - HMAC-SHA256 signature verification
- Executive summary, event breakdown, full audit log table
- First report generated and committed to benchmarks/results/

**Git Cleanup**
- Purged model files from git history via filter-branch
- Fixed .gitignore - models/ now fully excluded
- Force pushed clean history to GitHub

**Tagged v0.2.0**

#### What is next
- React Web UI - makes NISA demo-able to anyone
- Scaffold with Vite, dark mode, chat interface
- Model indicator, security dashboard, compliance report download

### Session 5 continued - April 6, 2026

#### React Web UI - Complete

**Stack**
- Vite + React, Tailwind CSS, axios, react-router-dom, lucide-react
- Rajdhani + JetBrains Mono + Outfit font stack
- Dark navy theme with gold accents, subtle grid background

**Components built**
- App.jsx - shell, header, sidebar navigation, API status dots
- Chat.jsx - full chat interface with model indicator and MoA badge
- Security.jsx - Nmap and ZAP scan panels with RedSage analysis display
- Compliance.jsx - audit log table and PDF report generation

**CORS fixed on both APIs**
- NLU API and Security API now accept requests from localhost:5173

**Confirmed working end to end**
- Chat with Nisaba - routing, MoA, model indicator all showing correctly
- Nmap scan - results table, RedSage analysis, raw output all rendering
- UI accessible at http://localhost:5173

**What is next**
- Phase 3: Samsung T9 SSD purchase, GraphRAG, Arize Phoenix
- Or: Forensics API to complete defensive security lifecycle

### Session 5 continued - April 6, 2026

#### Forensics API and UI - Complete

**forensics_api.py - port 8083**
- Log analysis with pattern matching - 13 suspicious event types
- IOC extraction - IPv4, domains, MD5/SHA1/SHA256, emails, URLs, CVEs
- File hash verification - SHA256 + MD5 with integrity check
- Timeline reconstruction - chronological event sorting
- RedSage analysis on every finding
- CORS enabled for UI

**Forensics.jsx - UI component**
- Log Analysis tab - paste logs, get findings, IOCs, RedSage analysis
- IOC Extractor tab - extract indicators from any text
- File Hash tab - compute and verify file integrity
- Risk banner - CLEAN/LOW/MEDIUM/HIGH/CRITICAL
- Color coded findings by severity
- IOC tags rendered as pills

**Confirmed working end to end**
- Full attack chain detected: brute force, root login, wget malware,
  netcat reverse shell, /etc/passwd access, payload execution
- Risk level: CRITICAL
- IOCs extracted: 2 IPs, 1 domain, 1 URL
- RedSage identified C2 compromise and gave remediation steps

**NISA UI now has 4 tabs**
- Chat, Security, Forensics, Compliance
