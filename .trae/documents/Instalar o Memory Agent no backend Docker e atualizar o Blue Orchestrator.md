## Estado Atual
- `agents/memory/app.py` e `agents/memory/models.py` implementam o Memory Agent com FastMCP, endpoints `/health` e `/mcp/tools/call`.
- `docker-compose.yml` já possui serviço `memory-agent` com `docker/Dockerfile.memory` e healthcheck.
- `agents/orchestrator/server.py` referencia o Memory Agent via URL interna Docker (`http://memory-agent:8080/...`).
- Divergência: `docker/Dockerfile.memory` usa `python:3.11-slim` enquanto os demais agentes usam `blue-ai-base:latest` (`docker/Dockerfile.base`).

## Objetivo
- Padronizar e “instalar” o Memory Agent no backend Docker (mesma base, rede, observabilidade e variáveis) e garantir integração robusta no orquestrador.
- Atualizar o prompt do Blue Orchestrator para refletir o uso de memória operacional e diretrizes de saída, segurança e qualidade.

## Mudanças Planejadas (sem executar ainda)

### 1) Padronizar a imagem do Memory Agent
- Arquivo: `docker/Dockerfile.memory`
- Alterar `FROM` para `blue-ai-base:latest` (mesma base dos demais agentes).
- Remover instalações duplicadas já cobertas por `requirements-base.txt` e manter apenas requisitos específicos do memory (`agents/memory/requirements.txt`).
- Garantir `USER mcpuser`, `EXPOSE 8080` e `HEALTHCHECK` em `/health`.

### 2) Ajustar docker-compose para integração forte
- Arquivo: `docker-compose.yml`
- Garantir serviço `memory-agent` com:
  - `build: docker/Dockerfile.memory` e `context: .`
  - `container_name: memory-agent`
  - `ports: [ "9086:8080" ]` (externo opcional)
  - `environment:` incluir `OPENROUTER_API_KEY` via `.env`, `LOG_LEVEL`, e variáveis específicas de memória (se houver)
  - `volumes:` `./logs:/app/logs`
  - `healthcheck:` `GET http://localhost:8080/health`
- Em `orchestrator`:
  - Adicionar `depends_on: memory-agent` com `condition: service_healthy`
  - Exportar `MEMORY_AGENT_URL=http://memory-agent:8080`

### 3) Robustez de cliente no orquestrador
- Arquivo: `agents/orchestrator/server.py`
- Tornar a URL do Memory Agent configurável via env (`MEMORY_AGENT_URL`) com fallback para `http://memory-agent:8080`.
- Adicionar retries/backoff ao cliente de memória (usando utilitário já existente de `llm_router` ou wrapper HTTP comum).
- Normalizar endpoints: `/mcp` para sessão e `/mcp/tools/call` para ferramentas.

### 4) Dependências e base
- Arquivo: `docker/Dockerfile.base` e `agents/common/requirements-base.txt`
- Validar que bibliotecas necessárias ao Memory Agent (Starlette, Uvicorn, FastMCP, Pydantic) estão cobertas na base; se não, mover para `requirements-base.txt` e manter específicos em `agents/memory/requirements.txt`.

### 5) Testes e validação em contêiner
- Scripts: `scripts/test_memory_integration.py`
- Adicionar modo “docker” para validar via `http://localhost:9086` e via rede interna (`http://memory-agent:8080`).
- Critérios de sucesso: health OK, `store_experience`, `lessons_for_task`, `memory_stats`, `deduplicate_experiences`, `prune_stale_memories`, `consolidate_lessons` → respostas 2xx e payloads válidos.

### 6) Observabilidade e segurança
- Logs montados em volume; sem credenciais hardcoded.
- `.env` e `.env.example` atualizados apenas se necessário (sem inserir segredos no repo).
- Manter `LOG_LEVEL` e métricas (se expostas) uniformes.

### 7) Atualizar Prompt do Blue Orchestrator
- Arquivo: `docs/agents/blue-orchestrator-prompt.md`
- Substituir por versão revisada com:
  - Identidade: “Blue Orchestrator – Orquestração MCP com Memória Operacional”.
  - Pipeline determinístico: Architect → Stack Research → Designer → Coder → Auditor, com fases explícitas.
  - Integração de memória: antes de cada fase, aplicar `lessons_for_task`; após cada decisão, registrar `store_experience` e `remember_decision`; rotina de manutenção (`deduplicate_experiences`, `prune_stale_memories`, `consolidate_lessons`).
  - Saída formal: JSON final com `architecture`, `imports`, `ui_design`, `code`, `tests`, `review`, `metrics`, `status`.
  - Regras de segurança e qualidade: sem segredos, acessibilidade, performance, retries, version pinning.
  - Critérios de “partial_success” com plano de remediação.

## Critérios de Aceite
- `memory-agent` builda a partir de `blue-ai-base:latest` e sobe saudável no compose.
- `orchestrator` inicia após `memory-agent` saudável e acessa ferramentas de memória com retries.
- Teste de integração passa contra endpoints principais de memória.
- Prompt do orquestrador atualizado com as diretrizes acima.

## Passos de Execução (após aprovação)
1. Editar `docker/Dockerfile.memory` para usar `blue-ai-base:latest` e ajustar CMD/HEALTHCHECK.
2. Atualizar `docker-compose.yml` com `depends_on` e `MEMORY_AGENT_URL` no `orchestrator`.
3. Tornar `MEMORY_AGENT_URL` configurável em `agents/orchestrator/server.py` com fallback e retries.
4. Verificar/mover dependências para `requirements-base.txt` quando apropriado.
5. Rodar `docker compose build` e `docker compose up -d`.
6. Executar `scripts/test_memory_integration.py` contra `localhost:9086` e rede interna.
7. Atualizar `docs/agents/blue-orchestrator-prompt.md` com o novo conteúdo.

## Conteúdo Proposto do Novo Prompt (resumo)
- Nome: Blue Orchestrator (MCP)
- Missão: Entregar features ponta-a-ponta com qualidade, segurança e previsibilidade.
- Pipeline: Architect → Stack Research → Designer → Coder → Auditor.
- Memória Operacional:
  - Antes de cada fase: `lessons_for_task(task_spec)`
  - Após decisões: `store_experience(...)`, `remember_decision(...)`
  - Manutenção: `deduplicate_experiences`, `prune_stale_memories`, `consolidate_lessons`
- Saída JSON final: `{ architecture, imports, ui_design, code, tests, review, metrics, status }`.
- Estados: `success | partial_success | failed` + plano de remediação para `partial_success`.
- Regras: segurança (OWASP), acessibilidade, performance (LCP/TBT), versionamento, retries/backoff.

Confirma executar o plano e aplicar as mudanças?