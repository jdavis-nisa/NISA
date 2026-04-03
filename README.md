# NISA — Network Intelligence Security Assistant

A locally-hosted, privacy-sovereign personal AI platform built on 
Apple Silicon. NISA integrates a multi-model AI brain, voice interface, 
structured knowledge graph, cybersecurity toolkit, and radar/electronic 
warfare analysis capability into a single unified system.

All computation runs on-device. No data leaves the machine.

---

## Architecture

- **Hardware:** MacBook Pro M3 Max 48GB — 400 GB/s unified memory
- **Models:** Qwen 3 32B · Qwen 2.5 Coder 32B · DeepSeek R1 32B · 
  RedSage 8B · Phi-4 14B · Gemma 3 27B
- **Inference:** MLX accelerated via Apple Silicon
- **Orchestration:** LangGraph multi-agent pipeline
- **Memory:** ChromaDB (vector) + Neo4j (knowledge graph)
- **Voice:** Whisper.cpp (STT) + Piper TTS
- **Security:** Docker-isolated tools · Zero trust · AES-256

---

## Capability Domains

| Domain | Description |
|---|---|
| Personal AI Assistant | Voice interface, daily briefings, task management |
| Cybersecurity Platform | Network analysis, threat modeling, forensics |
| Knowledge Graph | Persistent cross-domain memory and connections |
| Radar / EW | Signal processing, waveform analysis, simulation |
| News Intelligence | Daily synthesis across 5 curated domains |
| Learning System | Certification tracking, spaced repetition |

---

## Development Roadmap

- **Phase 1** (Months 1–3) — Voice assistant, NLU API, web UI
- **Phase 2** (Months 4–6) — Cybersecurity platform integration
- **Phase 3** (Months 7–12) — Knowledge graph and full automation
- **Phase 4** (Year 2) — Radar and electronic warfare module

---

## Tech Stack

Python · FastAPI · LangGraph · LangChain · ChromaDB · Neo4j · 
PostgreSQL · Docker · React · React Native · Whisper.cpp · Piper TTS · 
MLX-LM · GraphRAG · LM Studio · Ollama

---

## Status

![Phase 1 - In Progress](https://img.shields.io/badge/Phase%201-In%20Progress-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Models](https://img.shields.io/badge/Models-Apache%202.0-orange)

---

*NISA — Network Intelligence Security Assistant*  
*Named for Nisaba, Sumerian Goddess of Wisdom*  
*Built by Josh Davis · Huntsville, Alabama · 2026*