#!/usr/bin/env bash
# MultiVision AI — 1-Click Startup Launcher for Linux and macOS

echo "============================================================"
echo "  MultiVision AI — Model Intelligence & Multimodal Workspace"
echo "============================================================"
echo ""

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[INFO] Copying .env.example to .env ..."
        cp .env.example .env
    fi
fi

if [ -f "venv/bin/python" ]; then
    echo "[INFO] Starting MultiVision server on http://127.0.0.1:7000 ..."
    echo ""
    echo "Open your browser to:"
    echo "  - Control Center: http://127.0.0.1:7000/ai-models"
    echo "  - Operations:     http://127.0.0.1:7000/ai-operations"
    echo "  - Cost Control:   http://127.0.0.1:7000/ai-cost"
    echo "  - Chat Workspace: http://127.0.0.1:7000/"
    echo ""
    ./venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 7000
else
    echo "[INFO] Launching with system python3 ..."
    python3 -m uvicorn app:app --host 127.0.0.1 --port 7000
fi
