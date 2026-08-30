@echo off
title MultiVision AI — Multimodal Control Center
echo ============================================================
echo   MultiVision AI — Model Intelligence & Multimodal Workspace
echo ============================================================
echo.

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Copying .env.example to .env ...
        copy .env.example .env
    )
)

if exist "venv\Scripts\python.exe" (
    echo [INFO] Starting MultiVision server on http://127.0.0.1:7000 ...
    echo.
    echo Open your browser to:
    echo   - Control Center: http://127.0.0.1:7000/ai-models
    echo   - Operations:     http://127.0.0.1:7000/ai-operations
    echo   - Cost Control:   http://127.0.0.1:7000/ai-cost
    echo   - Chat Workspace: http://127.0.0.1:7000/
    echo.
    .\venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 7000
) else (
    echo [INFO] Virtual environment not found, launching with system python ...
    python -m uvicorn app:app --host 127.0.0.1 --port 7000
)

pause
