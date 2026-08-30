# 🚀 MultiVision AI — Beginner's Quick Start Guide

Welcome to **MultiVision AI**! This guide is designed for beginners and friends getting started with MultiVision AI for the first time.

---

## 📌 What is MultiVision AI?
MultiVision AI is a unified multimodal workspace that lets you chat, analyze images, query PDFs, listen to audio, generate videos, and interact with dozens of AI models (Gemini, Claude, GPT, Groq, Ollama, and more) with intelligent **Free-First routing**.

---

## ⚙️ 1. Prerequisites Checklist

Before you start, make sure you have:
1. **Python (v3.11, v3.12, or v3.13)**
   - Download: [python.org/downloads](https://www.python.org/downloads/)
   - ⚠️ *Important (Windows)*: Check the box **"Add Python to PATH"** during installation.
2. **Git**
   - Download: [git-scm.com/downloads](https://git-scm.com/downloads)

*(Optional tools for extra power)*:
- **[Ollama](https://ollama.com/)** (if you want 100% free, offline AI models running on your local machine)
- **[Node.js](https://nodejs.org/)** (if you want to use the built-in browser automation tools)

---

## 🏃 2. How to Run on Your Computer

### 🪟 Windows (Easiest - 1 Click)

1. Open **PowerShell** or **Command Prompt**.
2. Clone the repository and run the launcher:
```powershell
git clone https://github.com/bhanuatla521-svg/multivision-ai.git
cd multivision-ai
powershell -ExecutionPolicy Bypass -File .\launch-windows.ps1
```
> The launcher will automatically configure your virtual environment, install required packages, set up the database, and start the app on `http://127.0.0.1:7000`.

---

### 🍎 macOS / 🐧 Linux

1. Open **Terminal**.
2. Clone and start:
```bash
git clone https://github.com/bhanuatla521-svg/multivision-ai.git
cd multivision-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py
python -m uvicorn app:app --host 127.0.0.1 --port 7000
```
*(On macOS, you can also simply run `./start-macos.sh`)*

---

### 🐳 Docker (Alternative for all platforms)

If you have Docker Desktop installed:
```bash
git clone https://github.com/bhanuatla521-svg/multivision-ai.git
cd multivision-ai
docker compose up -d --build
```

---

## 🔑 3. Logging in & Adding API Keys

1. Open your web browser and go to: **[http://localhost:7000](http://localhost:7000)** (or `http://localhost:7860` on Mac).
2. During the first launch, the terminal prints an initial admin password (username: `admin`).
3. **Using Free Models**:
   - MultiVision works out-of-the-box with free-tier providers and local models.
   - To connect your own API keys (e.g. OpenAI, Anthropic, Gemini, Groq, OpenRouter), click **Settings ⚙️ → API Keys**.
   - If you run **Ollama** locally, MultiVision automatically discovers your local models!

---

## 🧭 Dashboard Quick Links

| Feature | URL | Description |
|---|---|---|
| 💬 **Chat Workspace** | `http://localhost:7000/` | Unified multimodal chat and agent assistant |
| 🧠 **Model Control Center** | `http://localhost:7000/ai-models` | Compare 50+ AI models, specs, benchmarks, and pricing |
| ⚡ **AI Operations** | `http://localhost:7000/ai-operations` | Live system health, provider latency & uptime metrics |
| 💰 **Cost Control** | `http://localhost:7000/ai-cost` | Track API token spend, budgets, and prevent accidental cost |

---

## ❓ Troubleshooting

- **Port already in use?**
  Run on a different port:
  ```powershell
  .\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 7001
  ```
- **Missing packages?**
  Run:
  ```powershell
  pip install -r requirements.txt
  ```
