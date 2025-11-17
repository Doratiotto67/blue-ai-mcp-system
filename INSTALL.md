# Installation and Configuration — Blue AI Multi-Agent MCP System

## 1. Project Summary
- Objective: A multi-agent system based on MCP that orchestrates architecture, design, code generation, auditing, and stack research with a learning memory.
- Technologies: `Python 3.12`, `Starlette`, `Uvicorn`, `FastMCP/MCP`, `httpx`, `pydantic`, `Docker`/`Docker Compose`, LLM integration via `OpenRouter` (GLM/Qwen/DeepSeek).
- Minimum Requirements:
  - CPU: 2 cores (4+ recommended)
  - RAM: 4 GB (8 GB recommended)
  - Disk: 5 GB free space
  - OS: Windows 10/11, macOS 13+, or Linux x86_64
  - Network: Internet access for OpenRouter (optional for stub mode)

## 2. Prerequisites
- Software
  - `Docker` ≥ 24 and `Docker Compose` v2
  - `Git` ≥ 2.40
  - `PowerShell 7+` (Windows) or `bash` (Linux/macOS)
  - Optional: Local `Python 3.12` to run utilities
- System Dependencies
  - Certificates and network access to download Docker images and access LLM APIs
- Mandatory Environment Settings
  - `.env` file in the root directory, based on `.env.example`, with:
    - `OPENROUTER_API_KEY` (your key, do not commit)
    - `GEMINI_API_KEY` (optional)
    - `LOG_LEVEL` (defaults to `INFO`)
  - Exposed Ports: `9080..9086` mapped to the internal `8080` port of each agent

## 3. Step-by-Step Installation
- Clone and Prepare Environment
  - `git clone <repo-url>`
  - `cd D:\PROJETOS\AGENTES AII` (Windows) or `cd blue-ai-mcp-system`
  - Copy `.env`: `cp .env.example .env` and edit keys
- Automated Installation (Windows)
  - `pwsh scripts\setup-env.ps1`
  - `pwsh scripts\install.ps1`
- Manual Installation
  - `docker-compose build`
  - `docker-compose up -d`
- Verification
  - `pwsh scripts\verify-install.ps1`
  - Or via HTTP: `curl http://localhost:9080/health`



## 4. Configuration
- Important Files
  - `.env`: API keys and log level
  - `docker-compose.yml`: services, ports, and healthchecks
  - `config/*.json`: IDE integrations (Claude, Cursor, VS Code)
  - `trae-mcp-config.json` and `mcp-configuration*.json` for MCP clients
- Environment Variables
  - `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `LOG_LEVEL`
  - `MEMORY_AGENT_URL` (internal via Compose)
- Customizations
  - Scaling: adjust `deploy.replicas` in Compose
  - Limits: `deploy.resources.limits.memory`
  - Ports: edit `908x:8080` mappings

## 5. Tests
- Smoke and Load Testing
  - `python scripts/test_runner.py --host http://localhost:9080 --concurrency 50 --iterations 200`
  - Report saved in `logs/test-runner-report.json`
- Installation Verification
  - `pwsh scripts/verify-install.ps1` (checks the health of all services)
- Common Troubleshooting
  - Containers not starting: `docker-compose logs -f orchestrator`
  - MCP not connecting: validate ports and `config/*`
  - Missing keys: edit `.env` and restart `docker-compose`

---

# Repository and Versioning Operations

## GitHub / Repository
- Initialize Local Repository
  - `git init -b main`
  - `git branch -M main`
  - `git add .` (do not commit secrets)
- Connect to GitHub
  - Create an empty repository on GitHub
  - `git remote add origin https://github.com/<org>/<repo>.git`
  - For versioning: create semantic tags (`v0.1.0`, `v0.2.0`)

## Versioning (SemVer)
- Standard: `MAJOR.MINOR.PATCH`
  - Breaking changes → `MAJOR`
  - Compatible features → `MINOR`
  - Fixes/adjustments → `PATCH`
- Helper Scripts
  - `pwsh scripts/version.ps1 -Bump minor` updates the `VERSION` file and prepares a tag

---

# Helper Scripts
- `scripts/setup-env.ps1`: prepares `.env` and validates keys
- `scripts/install.ps1`: builds and starts via Docker Compose
- `scripts/verify-install.ps1`: health checks and smoke test
- `scripts/clean.ps1`: shuts down and cleans up volumes/images
- `scripts/version.ps1`: bumps the semantic version and prepares a tag

## Quick Execution
- `pwsh scripts\setup-env.ps1`
- `pwsh scripts\install.ps1`
- `pwsh scripts\verify-install.ps1`

---

# Security Notes
- Never commit real keys in `.env`
- Use non-root users (already configured in the base images)
- Active healthchecks on `orchestrator` and `memory-agent`

# Maintenance
- Logs are in `./logs/`
- Update this document when new versions are released