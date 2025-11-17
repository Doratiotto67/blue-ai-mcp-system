# Guia de Configuração — Blue AI Agents + MCP + Docker (PT‑BR / EN)

## PT‑BR — Visão Geral
- Objetivo: configurar MCP no Trae, orquestrar serviços via Docker, instalar os agentes Blue AI e validar com testes automatizados.
- Público: DevOps/Engenheiros responsáveis por setup, operação e qualidade.

## PT‑BR — 1) MCP no Trae
- Pré‑requisitos:
  - Trae IDE instalado e acesso a Settings → MCP.
  - Containers dos agentes expostos em `localhost:9080–9085` com MCP HTTP em `/mcp`.
- Configuração manual (um servidor por vez):
```
{
  "mcpServers": {
    "blue-orchestrator": {
      "type": "http",
      "url": "http://localhost:9080/mcp",
      "autoConnect": true,
      "retry": { "maxAttempts": 3, "initialDelayMs": 1000, "maxDelayMs": 10000 }
    }
  },
  "mcpGlobal": { "timeout": 30000, "logLevel": "info" }
}
```
- Repita para os demais agentes trocando a porta: `9081..9085`.
- Variáveis de ambiente (opcional):
```
# .env
OPENROUTER_API_KEY=...
# GOOGLE_API_KEY=...   # opcional; desnecessário se Gemini não for usado
BACKEND_API_URL=https://api.seudominio.com
BACKEND_AUTH_TOKEN=...
```
- Validação rápida (PowerShell):
```
Invoke-RestMethod -Uri "http://localhost:9080/health" -Method Get
Invoke-RestMethod -Uri "http://localhost:9080/mcp/session" -Method Post
```
- Troubleshooting:
  - SSE 404: use `type: "http"` e `url: "http://localhost:PORT/mcp"` (não SSE).
  - Apenas um servidor por vez no modal Manual.

## PT‑BR — 2) Backend Docker
- Dockerfile (exemplo FastAPI):
```
# Dockerfile.backend
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV PORT=8080
CMD ["python","-m","src.main"]
```
- docker-compose.yml (exemplo com rede e mapeamentos):
```
services:
  orchestrator:
    image: agentesaii-orchestrator:latest
    ports: ["9080:8080"]
    environment:
      PORT: 8080
    restart: unless-stopped

  architect-agent:
    image: agentesaii-architect-agent:latest
    ports: ["9081:8080"]
    restart: unless-stopped

  designer-agent:
    image: agentesaii-designer-agent:latest
    ports: ["9082:8080"]
    restart: unless-stopped

  coder-agent:
    image: agentesaii-coder-agent:latest
    ports: ["9083:8080"]
    restart: unless-stopped

  auditor-agent:
    image: agentesaii-auditor-agent:latest
    ports: ["9084:8080"]
    restart: unless-stopped

  stack-research-agent:
    image: agentesaii-stack-research-agent:latest
    ports: ["9085:8080"]
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      MCP_ORCHESTRATOR_URL: http://orchestrator:8080/mcp
      MCP_ARCHITECT_URL: http://architect-agent:8080/mcp
      MCP_DESIGNER_URL: http://designer-agent:8080/mcp
      MCP_CODER_URL: http://coder-agent:8080/mcp
      MCP_AUDITOR_URL: http://auditor-agent:8080/mcp
      MCP_STACK_URL: http://stack-research-agent:8080/mcp
    depends_on:
      - orchestrator
      - architect-agent
      - designer-agent
      - coder-agent
      - auditor-agent
      - stack-research-agent
    restart: unless-stopped
```
- Comandos:
```
docker-compose build
docker-compose up -d
docker-compose ps
```

## PT‑BR — 3) Instalação Blue AI Agentes
- Componentes: Orchestrator, Architect, Designer, Coder, Auditor, Stack Research.
- Endpoints: `GET /health`, `POST /mcp/session`, `POST /mcp/tools/call`.
- Fallback sem Gemini: desabilite `GOOGLE_API_KEY` e evite tools que dependem de Gemini.
- Ordem sugerida: subir todos os agentes, validar health, conectar no Trae.

## PT‑BR — 4) Publicação no GitHub
- Criar repositório, adicionar `README.md` com instruções de setup e uso.
- Adicionar `LICENSE` (MIT/GPL/Apache).
- `gitignore` para `env`, builds, caches.

## PT‑BR — 5) Testes
- Testes de conectividade MCP:
```
Invoke-RestMethod -Uri "http://localhost:9080/mcp/session" -Method Post
Invoke-RestMethod -Uri "http://localhost:9081/health" -Method Get
```
- Integração: chamar `propose_architecture` via orchestrator:
```
Invoke-RestMethod -Uri "http://localhost:9080/mcp/tools/call" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"tool_name":"propose_architecture","arguments":{"spec":"Auth 2FA"}}'
```
- Resultados esperados: `200 OK`, JSON com conteúdo e sem `high` no auditor.

---

## EN — Overview
- Goal: configure MCP in Trae, orchestrate services via Docker, install Blue AI agents, and validate with automated tests.

## EN — 1) MCP in Trae
- Prereqs: Trae IDE, agents exposed at `localhost:9080–9085`, MCP HTTP at `/mcp`.
- Manual config (one server at a time):
```
{
  "mcpServers": {
    "blue-orchestrator": {
      "type": "http",
      "url": "http://localhost:9080/mcp",
      "autoConnect": true,
      "retry": { "maxAttempts": 3, "initialDelayMs": 1000, "maxDelayMs": 10000 }
    }
  },
  "mcpGlobal": { "timeout": 30000, "logLevel": "info" }
}
```
- Repeat for other agents with ports `9081..9085`.
- Env sample:
```
OPENROUTER_API_KEY=...
# GOOGLE_API_KEY=...  # optional if Gemini is not used
BACKEND_API_URL=https://api.yourdomain.com
BACKEND_AUTH_TOKEN=...
```
- Validation:
```
curl -s http://localhost:9080/health
curl -s -X POST http://localhost:9080/mcp/session
```
- Troubleshooting: if SSE 404, ensure `type:"http"` and the URL includes `/mcp`.

## EN — 2) Backend Docker
- Dockerfile example (FastAPI): see PT‑BR section.
- docker-compose: include agents + backend, map `9080:8080` etc., use internal URLs like `http://orchestrator:8080/mcp`.
- Commands:
```
docker-compose build && docker-compose up -d && docker-compose ps
```

## EN — 3) Blue AI Agents Installation
- Components and endpoints as above; optional Gemini disabled.
- Bring up agents, validate health, connect Trae manually.

## EN — 4) GitHub Publication
- Create repo, add README with setup and usage, add LICENSE.

## EN — 5) Testing
- MCP connectivity and inter-agent calls; expect structured JSON and `200 OK` responses.

## Notas Finais / Final Notes
- Segurança: nunca logar segredos; mascarar dados sensíveis.
- Qualidade: aplicar retries/backoff; registrar métricas.
- Operação: adicionar healthchecks nos serviços e alertas de 4xx/5xx.