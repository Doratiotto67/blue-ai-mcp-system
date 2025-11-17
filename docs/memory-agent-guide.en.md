# Memory Agent - Complete Guide

## Overview

The Memory Agent is the long-term memory component of the Blue AI system. It stores error/learning experiences and provides learned lessons to avoid repeating problems.

## Architecture

### Main Components

1. **Models (`models.py`)**
   - `Experience`: Stores error/fix experiences
   - `Lesson`: Extracted learned lessons
   - `LessonsBundle`: Set of organized lessons
   - `MemoryStats`: System statistics

2. **Memory Store (`app.py`)**
   - In-memory storage (replaceable by Postgres/pgvector)
   - Automatic deduplication of experiences
   - Pruning of old memories
   - Consolidation of similar lessons

3. **Integration**
   - Integrated with the Orchestrator via MCP
   - Uses Qwen3-235B for text processing
   - Smart query caching

## Features

### 1. Storing Experiences

```python
experience = {
    "project_id": "blue-ai-agents",
    "module": "auth_api",
    "stack": "python+fastapi+postgres+react",
    "severity": "critical",
    "error_type": "security",
    "summary": "Login endpoint exposed timing side-channel",
    "root_cause": "Incorrect password comparison using '=='",
    "fix_applied": "Use secrets.compare_digest and generic error messages",
    "bad_snippet": "if user.password == input_password:",
    "good_snippet": "if secrets.compare_digest(user.password_hash, hash(input_password)):",
    "tags": ["security", "timing-attack", "auth"],
    "affected_components": ["auth_api", "user_db"]
}
```

### 2. Retrieving Learned Lessons

```python
lessons = await memory_agent.lessons_for_task(
    spec="API de auth com JWT + 2FA",
    stack="python+fastapi+postgres+react",
    limit=10
)
```

Returns:
- **High-level rules**: Architectural rules
- **Code smells to avoid**: Bad code patterns
- **Security pitfalls**: Security traps
- **Performance tips**: Performance tips

### 3. Automatic Deduplication

The system identifies duplicate or very similar experiences:
- Calculates content hash
- Compares text similarity (Jaccard)
- Keeps the most recent/severe experience
- Automatically removes duplicates

### 4. Memory Pruning

Removes old, low-severity experiences:
- **Critical/High**: Kept forever
- **Medium**: Removed after 90 days
- **Low**: Removed after 90 days
- Configurable via parameter

### 5. Lesson Consolidation

Groups similar lessons into meta-rules:
- Identifies repetitive patterns
- Generates consolidated rules
- Calculates confidence based on frequency
- Reduces knowledge noise

## LLM Integration

### Specialized Model

The Memory Agent uses **Qwen3-235B** to:
- Process text from experiences
- Generate structured lessons
- Consolidate similar patterns
- Extract practical rules

### Smart Fallback

If Qwen3 fails, it falls back to:
1. **GLM-4.5-Air**: For structuring
2. **DeepSeek-V3.1**: For critical analysis

## MCP API

## HTTP Endpoints
- `GET /health` — agent status
- `POST /tools/call` — execute tools directly via HTTP
- `POST /mcp/tools/call` — MCP-compatible alias
- `POST /mcp` — execute tool via payload `{ tool_name, arguments }`

### Call Format
- `POST /tools/call` or `/mcp/tools/call`
  - Body: `{ "tool_name": "memory_stats", "arguments": {} }`
- `POST /mcp`
  - Body: `{ "tool_name": "memory_stats", "arguments": {} }`

Note: for `store_experience` use `{ "tool_name": "store_experience", "arguments": { ...exp... } }` and for `remember_decision` use `{ "tool_name": "remember_decision", "arguments": { ...decision... } }`.

### Main Tools

#### `store_experience(exp: Experience) -> str`
Stores a new experience.

#### `lessons_for_task(spec, stack, limit) -> LessonsBundle`
Retrieves relevant lessons for a task.

#### `memory_stats() -> MemoryStats`
Returns system statistics.

#### `deduplicate_experiences() -> DeduplicationResult`
Removes duplicate experiences.

#### `prune_stale_memories(cutoff_days) -> PruningResult`
Removes old experiences.

#### `consolidate_lessons() -> List[ConsolidatedLesson]`
Groups similar lessons.

## Uso no Orchestrator

### Pipeline com Memória

1. **Pré-passo**: Buscar lições aprendidas
2. **Arquitetura**: Aplicar lições de design
3. **Design**: Aplicar lições de UX
4. **Código**: Aplicar lições de implementação
5. **Review**: Validar contra lições de segurança
6. **Pós-passo**: Armazenar novas experiências

### Exemplo de Uso

```python
# No build_feature do Orchestrator
lessons = await agents.call_agent(
    agents.memory_url,
    "lessons_for_task",
    {"spec": spec, "stack": stack}
)

# Enriquece contexto com lições
enriched_context = f"{context}\n\n{lessons_text}"

# Aplica em todos os agentes
arch_result = await agents.call_agent(
    agents.architect_url,
    "propose_architecture",
    {"spec": spec, "context": enriched_context, "lessons": lessons}
)
```

## Métricas e Monitoramento

### Estatísticas Disponíveis

- **Total experiences**: Número total de experiências
- **By severity**: Distribuição por severidade
- **By error type**: Distribuição por tipo de erro
- **Memory hit rate**: % de tasks que usaram memória
- **Lesson reuse rate**: Média de reuso de lições
- **Cache performance**: Eficiência do cache

### Métricas de Qualidade

- **Deduplication rate**: % de duplicatas removidas
- **Consolidation effectiveness**: Redução de ruído
- **Relevance score**: Qualidade das lições recuperadas

## Configuração

### Variáveis de Ambiente

```bash
OPENROUTER_API_KEY=your-key-here
LOG_LEVEL=INFO
```

### Docker Compose

```yaml
memory-agent:
  build:
    context: .
    dockerfile: docker/Dockerfile.memory
  ports:
    - "9086:8080"
  environment:
    OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
  volumes:
    - ./logs:/app/logs
```

## Melhores Práticas

### 1. Armazenamento

- Seja específico na descrição do problema
- Inclua exemplos de código (bom e ruim)
- Use tags relevantes para categorização
- Defina severidade corretamente

### 2. Consultas

- Seja específico na spec da tarefa
- Informe o stack tecnológico completo
- Use limites para controlar resultados
- Filtre por severidade quando relevante

### 3. Manutenção

- Execute deduplicação semanalmente
- Faça pruning de memórias mensalmente
- Monitore estatísticas de uso
- Revise lições consolidadas periodicamente

## Evolução Futura

### Short Term (1-2 meses)

- Migração para Postgres + pgvector
- Implementação de embeddings semânticos
- Interface web para gestão visual
- API REST adicional

### Medium Term (3-6 meses)

- Integração com sistemas externos
- Exportação/importação de conhecimento
- Análise de tendências
- Recomendações proativas

### Long Term (6+ meses)

- Aprendizado contínuo com ML
- Classificação automática de severidade
- Detecção de padrões emergentes
- Sistema de recomendação inteligente

## Troubleshooting

### Problemas Comuns

1. **Memory Agent not responding**
   - Check if the container is running
   - Confirm port 9086 is accessible
   - Test health check: `curl localhost:9086/health`

2. **Lessons are not retrieved**
   - Check if experiences are stored
   - Confirm if spec and stack are correct
   - Test with different filters

3. **Deduplication not working**
   - Check similarity threshold
   - Confirm experience format
   - Review error logs

### Debug

```bash
# View container logs
docker logs memory-agent

# Test health check
curl http://localhost:9086/health

# View statistics
curl -X POST http://localhost:9086/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "memory_stats", "arguments": {}}'

# Via orchestrator
curl -X POST http://localhost:9080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_memory_stats", "arguments": {}}'
```

## Exemplo Completo

```python
# 1. Store security experience
experience = {
    "project_id": "my-app",
    "module": "auth",
    "stack": "python+fastapi+postgres",
    "severity": "critical",
    "error_type": "security",
    "summary": "SQL injection in user login",
    "root_cause": "Direct string concatenation",
    "fix_applied": "Use parameterized queries",
    "tags": ["security", "sql", "injection"]
}

# 2. Retrieve lessons for new feature
lessons = await memory_agent.lessons_for_task(
    spec="Create admin dashboard with user management",
    stack="python+fastapi+postgres+react"
)

# 3. Apply lessons in development
for rule in lessons.get("high_level_rules", []):
    print(f"Rule: {rule['rule']}")
    print(f"Why: {rule['rationale']}")

# 4. Store architectural decision
decision = {
    "project_id": "my-app",
    "module": "admin",
    "decision_type": "architecture",
    "decision": "Use RBAC for permissions",
    "rationale": "Granular control and auditability"
}
```

This guide covers all aspects of the Memory Agent. For additional questions, consult the logs or the development team.