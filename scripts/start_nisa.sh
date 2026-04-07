#!/bin/bash
# NISA Session Start Script
# Starts all services required for a full NISA session
# Usage: bash ~/NISA/scripts/start_nisa.sh

set -e

NISA_DIR="$HOME/NISA"
cd "$NISA_DIR"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║           NISA — SYSTEM STARTUP          ║"
echo "║  Network Intelligence Security Assistant  ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Step 1: Docker ───────────────────────────────────────────────
echo "[ 1/6 ] Starting Docker containers..."
docker compose -f "$NISA_DIR/docker/docker-compose.yml" up -d 2>/dev/null
docker compose -f "$NISA_DIR/docker/security/docker-compose.security.yml" up -d 2>/dev/null || docker compose -f "$NISA_DIR/docker/security/docker-compose.security.yml" up -d 2>/dev/null
sleep 2

# Verify containers
CONTAINERS=$(docker ps --filter "name=nisa_" --format "{{.Names}}" | wc -l | tr -d ' ')
echo "       $CONTAINERS containers running"

# ── Step 2: Kill stale ports ─────────────────────────────────────
echo "[ 2/6 ] Clearing ports..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
lsof -ti:8082 | xargs kill -9 2>/dev/null || true
lsof -ti:8083 | xargs kill -9 2>/dev/null || true
lsof -ti:6006 | xargs kill -9 2>/dev/null || true
sleep 1
echo "       Ports 8081, 8082, 8083, 6006 cleared"

# ── Step 3: NLU API ──────────────────────────────────────────────
echo "[ 3/6 ] Starting NLU API (port 8081)..."
python3.11 "$NISA_DIR/src/core/nlu_api.py" > "$NISA_DIR/logs/nlu_api.log" 2>&1 &
NLU_PID=$!
sleep 2
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "       NLU API online - PID $NLU_PID"
else
    echo "       NLU API failed to start - check logs/nlu_api.log"
fi

# ── Step 4: Security API ─────────────────────────────────────────
echo "[ 4/6 ] Starting Security API (port 8082)..."
python3.11 "$NISA_DIR/src/security/security_api.py" > "$NISA_DIR/logs/security_api.log" 2>&1 &
SEC_PID=$!
sleep 1
if curl -s http://localhost:8082/health > /dev/null 2>&1; then
    echo "       Security API online - PID $SEC_PID"
else
    echo "       Security API failed to start - check logs/security_api.log"
fi

# ── Step 5: Forensics API ────────────────────────────────────────
echo "[ 5/6 ] Starting Forensics API (port 8083)..."
python3.11 "$NISA_DIR/src/security/forensics_api.py" > "$NISA_DIR/logs/forensics_api.log" 2>&1 &
FOR_PID=$!
sleep 1
if curl -s http://localhost:8083/health > /dev/null 2>&1; then
    echo "       Forensics API online - PID $FOR_PID"
else
    echo "       Forensics API failed to start - check logs/forensics_api.log"
fi

# ── Step 6: Phoenix ──────────────────────────────────────────────
echo "[ 6/6 ] Starting Arize Phoenix (port 6006)..."
python3.11 -m phoenix.server.main serve > "$NISA_DIR/logs/phoenix.log" 2>&1 &
PHX_PID=$!
sleep 5
if curl -s http://localhost:6006 > /dev/null 2>&1; then
    echo "       Phoenix online - PID $PHX_PID"
else
    echo "       Phoenix failed to start - check logs/phoenix.log"
fi

# ── Summary ──────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║              NISA ONLINE                 ║"
echo "╠══════════════════════════════════════════╣"
echo "║  NLU API      http://localhost:8081      ║"
echo "║  Security API http://localhost:8082      ║"
echo "║  Forensics    http://localhost:8083      ║"
echo "║  Phoenix      http://localhost:6006      ║"
echo "║  UI           http://localhost:5173      ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Start UI:                               ║"
echo "║  cd ~/NISA/nisa-ui && npm run dev        ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Manual starts:                          ║"
echo "║  - LM Studio (open app, start server)    ║"
echo "║  - Neo4j Desktop (click Start)           ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Logs: ~/NISA/logs/"
echo ""
