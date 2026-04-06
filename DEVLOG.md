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