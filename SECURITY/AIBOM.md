# AI Bill of Materials (AIBOM)
## NISA — Network Intelligence Security Assistant
**Last Updated:** April 4, 2026
**Maintainer:** Josh Davis

---

## Purpose

This document catalogs every AI model, framework, and tool used in
NISA. It serves as a supply chain security record demonstrating model
provenance, license compliance, and risk assessment for each component.

---

## AI Models

### Primary Inference Models

| Model | Version | Source | License | Quantization | Size | GPU Offload |
|---|---|---|---|---|---|---|
| Qwen 3 32B | MLX 4BIT | qwen/qwen3-32b via LM Studio | Apache 2.0 | MLX 4BIT | 18.45GB | Full |
| DeepSeek R1 Distill Qwen 32B | Q4_K_S | bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF | MIT | Q4_K_S imatrix | 18.78GB | Full |
| Qwen 2.5 Coder 32B | Q4_K_M | Qwen/Qwen2.5-Coder-32B-Instruct | Apache 2.0 | Q4_K_M | ~20GB | Full |
| RedSage 8B | Q4_K_M | RedSage-AI/RedSage | Apache 2.0 | Q4_K_M | ~5GB | Full |
| Phi-4 14B | Q4_K_M | microsoft/phi-4 | MIT | Q4_K_M | ~9GB | Full |
| Gemma 3 27B | Q4_K_M | google/gemma-3-27b-it | Gemma ToS | Q4_K_M | ~17GB | Full |

### Risk Assessment — Models

| Risk | Assessment | Mitigation |
|---|---|---|
| Supply chain tampering | Low — all models from verified HuggingFace publishers | SHA256 checksums verified by LM Studio on download |
| License violation | None — all Apache 2.0 or MIT | Documented above, no commercial restrictions for personal use |
| Data exfiltration | None | All inference local, no external API calls |
| Prompt injection | Medium — inherent to LLM architecture | JIT permissions, input sanitization, audit logging |
| Model poisoning | Low — using published quantizations | No fine-tuning from untrusted data sources |

---

## Core Frameworks

| Framework | Version | License | Purpose |
|---|---|---|---|
| LangGraph | Latest | MIT | Multi-agent orchestration |
| LangChain | Latest | MIT | LLM tooling and memory |
| ChromaDB | Latest | Apache 2.0 | Vector database |
| FastAPI | Latest | MIT | API framework |
| MLX-LM | Latest | MIT | Apple Silicon inference |
| Ollama | 0.20.0 | MIT | CLI model runner |
| LM Studio | 5.x | Proprietary (free) | Model management GUI |

## Inference Infrastructure

| Component | Version | License | Purpose |
|---|---|---|---|
| Python | 3.11.15 | PSF | Primary language |
| Docker Desktop | Latest | Apache 2.0 | Container isolation |
| macOS Sonoma | Latest | Proprietary | Host OS |
| Apple MLX | Latest | MIT | Metal GPU acceleration |

## Planned Components (Phase 2+)

| Component | License | Purpose |
|---|---|---|
| Neo4j Community | GPL v3 | Knowledge graph database |
| PostgreSQL | PostgreSQL License | Structured data storage |
| Redis | BSD | Caching layer |
| Arize Phoenix | Apache 2.0 | AI observability |
| PyRIT | MIT | Adversarial red teaming |
| Garak | Apache 2.0 | LLM vulnerability scanner |
| Whisper.cpp | MIT | Speech to text |
| Piper TTS | MIT | Text to speech |

---

## Quantization Methods

**Q4_K_M** — 4-bit quantization using K-quants with medium size.
Best balance of quality and size. Recommended for most use cases.

**Q4_K_S** — 4-bit quantization using K-quants with small size.
Bartowski imatrix variant — uses calibration dataset to preserve
the most important weights. Slightly smaller, similar quality.

**MLX 4BIT** — Apple's native 4-bit quantization for Apple Silicon.
Optimized for unified memory architecture. 20-30% faster than GGUF
on M-series chips. Preferred format when available.

---

## Compliance Notes

- All models run entirely on local hardware
- No data transmitted to external servers during inference
- No user data used for model training
- All weights are read-only after download
- Docker isolation prevents security tools from accessing
  personal data stores
- JIT permissions (Phase 2) will enforce least-privilege access
  for all tool executions

---

## Update Policy

This document is updated whenever:
- A new model is added to the stack
- A model is updated to a new version
- A new framework dependency is introduced
- A security assessment changes

*NISA AIBOM — Supply Chain Security Record*
*github.com/jdavis-nisa/NISA/SECURITY/AIBOM.md*
## Cryptographic Components

### Audit Trail Signing
| Algorithm | Standard | Key Size | Signature Size | Status |
|---|---|---|---|---|
| ML-DSA-65 | NIST FIPS 204 | PK: 1952B, SK: 4032B | 3309B | PRIMARY |
| HMAC-SHA256 | RFC 2104 | 256-bit | 256-bit | LEGACY FALLBACK |

ML-DSA-65 (CRYSTALS-Dilithium Level 2) is a post-quantum digital signature algorithm
standardized by NIST in FIPS 204 (August 2024). It provides security against both
classical and quantum computer attacks. Keys are generated locally and stored at
~/.nisa/keys/ - never transmitted or stored in the repository.
