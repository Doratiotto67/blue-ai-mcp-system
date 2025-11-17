# INSTALAÇÃO E CONFIGURAÇÃO — Blue AI Multi‑Agent MCP System

## 1. Resumo do Projeto
- Objetivo: sistema multi‑agente baseado em MCP que orquestra arquitetura, design, geração de código, auditoria e pesquisa de stack com memória de aprendizado.
- Tecnologias: `Python 3.12`, `Starlette`, `Uvicorn`, `FastMCP/MCP`, `httpx`, `pydantic`, `Docker`/`Docker Compose`, integração LLM via `OpenRouter` (GLM/Qwen/DeepSeek) e Gemini.
- Requisitos mínimos:
  - CPU: 2 cores (recomendado 4+)
  - RAM: 4 GB (recomendado 8 GB)
  - Disco: 5 GB livres
  - SO: Windows 10/11, macOS 13+, ou Linux x86_64
  - Rede: acesso à internet para OpenRouter/Gemini (opcional para modo stub)

## 2. Pré‑requisitos
- Software
  - `Docker` ≥ 24 e `Docker Compose` v2
  - `Git` ≥ 2.40
  - `PowerShell 7+` (Windows) ou `bash` (Linux/macOS)
  - Opcional: `Python 3.12` local para rodar utilitários
- Dependências do sistema
  - Certificados e acesso de rede para baixar imagens Docker e acessar APIs LLM
- Configurações ambientais obrigatórias
  - Arquivo `.env` na raiz baseado em `.env.example` com:
    - `OPENROUTER_API_KEY` (sua chave, não commit)
    - `GEMINI_API_KEY` (opcional)
    - `LOG_LEVEL` (`INFO` por padrão)
  - Portas expostas: `9080..9086` mapeadas para `8080` interno de cada agente

## 3. Instalação Passo a Passo
- Clonar e preparar ambiente
  - `git clone <url-do-repo>`
  - `cd D:\PROJETOS\AGENTES AII` (Windows) ou `cd blue-ai-mcp-system`
  - Copiar `.env`: `cp .env.example .env` e editar chaves
- Instalação automática (Windows)
  - `pwsh scripts\setup-env.ps1`
  - `pwsh scripts\install.ps1`
- Instalação manual
  - `docker-compose build`
  - `docker-compose up -d`
- Verificação
  - `pwsh scripts\verify-install.ps1`
  - Ou via HTTP: `curl http://localhost:9080/health`

### Quickstart (EN)
- Clone and prepare
  - `git clone <repository>`
  - `cd blue-ai-mcp-system`
  - `cp .env.example .env` and set keys
- Build and start
  - `docker-compose build`
  - `docker-compose up -d`
- Verify
  - `curl http://localhost:9080/health`

## 4. Configuração
- Arquivos importantes
  - `.env` chaves e log level
  - `docker-compose.yml` serviços, portas e healthchecks
  - `config/*.json` integrações com IDEs (Claude, Cursor, VS Code)
  - `trae-mcp-config.json` e `mcp-configuration*.json` para clientes MCP
- Variáveis de ambiente
  - `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `LOG_LEVEL`
  - `MEMORY_AGENT_URL` (interno por Compose)
- Personalizações
  - Escalonamento: ajustar `deploy.replicas` no Compose
  - Limites: `deploy.resources.limits.memory`
  - Portas: editar mapeamentos `908x:8080`

## 5. Testes
- Teste de fumaça e carga
  - `python scripts/test_runner.py --host http://localhost:9080 --concurrency 50 --iterations 200`
  - Relatório salvo em `logs/test-runner-report.json`
- Verificação de instalação
  - `pwsh scripts/verify-install.ps1` (checa health de todos os serviços)
- Solução de problemas comuns
  - Containers não iniciam: `docker-compose logs -f orchestrator`
  - MCP não conecta: valide portas e `config/*`
  - Chaves ausentes: edite `.env` e reinicie `docker-compose`

---

# Operações de Repositório e Versionamento

## GitHub / Repositório
- Inicializar repositório local
  - `git init -b main`
  - `git branch -M main`
  - `git add .` (não faça commit de segredos)
- Conectar ao GitHub
  - Crie um repositório vazio no GitHub
  - `git remote add origin https://github.com/<org>/<repo>.git`
  - Para versionar: crie tags semânticas (`v0.1.0`, `v0.2.0`)

## Versionamento (SemVer)
- Padrão: `MAJOR.MINOR.PATCH`
  - Breaking changes → `MAJOR`
  - Funcionalidades compatíveis → `MINOR`
  - Correções/ajustes → `PATCH`
- Scripts auxiliares
  - `pwsh scripts/version.ps1 -Bump minor` atualiza arquivo `VERSION` e prepara tag

---

# Scripts Auxiliares
- `scripts/setup-env.ps1`: prepara `.env` e valida chaves
- `scripts/install.ps1`: build e subida via Docker Compose
- `scripts/verify-install.ps1`: checagens de saúde e smoke test
- `scripts/clean.ps1`: desligar e limpar volumes/imagens
- `scripts/version.ps1`: aumentar versão semântica e preparar tag

## Execução rápida
- `pwsh scripts\setup-env.ps1`
- `pwsh scripts\install.ps1`
- `pwsh scripts\verify-install.ps1`

---

# Notas de Segurança
- Nunca commit de chaves reais em `.env`
- Use usuários não‑root (já configurado nas imagens base)
- Healthchecks ativos em `orchestrator` e `memory-agent`

# Manutenção
- Logs em `./logs/`
- Atualize este documento quando novas versões forem lançadas