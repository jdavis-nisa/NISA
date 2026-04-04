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