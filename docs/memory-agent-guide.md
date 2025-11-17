# Memory Agent - Guia Completo

## Overview

O Memory Agent é o componente de memória de longo prazo do sistema Blue AI. Ele armazena experiências de erro/aprendizado e fornece lições aprendidas para evitar repetição de problemas.

## Arquitetura

### Componentes Principais

1. **Models (`models.py`)**
   - `Experience`: Armazena experiências de erro/correção
   - `Lesson`: Lições aprendidas extraídas
   - `LessonsBundle`: Conjunto de lições organizadas
   - `MemoryStats`: Estatísticas do sistema

2. **Memory Store (`app.py`)**
   - Armazenamento em memória (substituível por Postgres/pgvector)
   - Deduplicação automática de experiências
   - Pruning de memórias antigas
   - Consolidação de lições similares

3. **Integration**
   - Integrado ao Orchestrator via MCP
   - Usa Qwen3-235B para processamento de texto
   - Cache inteligente de consultas

## Funcionalidades

### 1. Armazenamento de Experiências

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

### 2. Recuperação de Lições Aprendidas

```python
lessons = await memory_agent.lessons_for_task(
    spec="API de auth com JWT + 2FA",
    stack="python+fastapi+postgres+react",
    limit=10
)
```

Retorna:
- **High-level rules**: Regras de arquitetura
- **Code smells to avoid**: Padrões de código ruins
- **Security pitfalls**: Armadilhas de segurança
- **Performance tips**: Dicas de performance

### 3. Deduplicação Automática

O sistema identifica experiências duplicadas ou muito similares:
- Calcula hash do conteúdo
- Compara similaridade textual (Jaccard)
- Mantém a experiência mais recente/severa
- Remove duplicatas automaticamente

### 4. Pruning de Memórias

Remove experiências antigas de baixa severidade:
- **Critical/High**: Mantidas forever
- **Medium**: Removidas após 90 dias
- **Low**: Removidas após 90 dias
- Configurável via parâmetro

### 5. Consolidação de Lições

Agrupa lições similares em meta-regras:
- Identifica padrões repetitivos
- Gera regras consolidadas
- Calcula confiança baseada na frequência
- Reduz ruído no conhecimento

## Integração com LLMs

### Modelo Especializado

O Memory Agent usa **Qwen3-235B** para:
- Processar texto de experiências
- Gerar lições estruturadas
- Consolidar padrões similares
- Extrair regras práticas

### Fallback Inteligente

Se Qwen3 falhar, fallback para:
1. **GLM-4.5-Air**: Para estruturação
2. **DeepSeek-V3.1**: Para análise crítica

## API MCP

## Endpoints HTTP
- `GET /health` — status do agente
- `POST /tools/call` — executa tools direto por HTTP
- `POST /mcp/tools/call` — alias compatível com MCP
- `POST /mcp` — executa tool via payload `{ tool_name, arguments }`

### Formato de Chamada
- `POST /tools/call` ou `/mcp/tools/call`
  - Body: `{ "tool_name": "memory_stats", "arguments": {} }`
- `POST /mcp`
  - Body: `{ "tool_name": "memory_stats", "arguments": {} }`

Observação: para `store_experience` use `{ "tool_name": "store_experience", "arguments": { ...exp... } }` e para `remember_decision` use `{ "tool_name": "remember_decision", "arguments": { ...decision... } }`.

### Tools Principais

#### `store_experience(exp: Experience) -> str`
Armazena uma nova experiência.

#### `lessons_for_task(spec, stack, limit) -> LessonsBundle`
Recupera lições relevantes para uma tarefa.

#### `memory_stats() -> MemoryStats`
Retorna estatísticas do sistema.

#### `deduplicate_experiences() -> DeduplicationResult`
Remove experiências duplicadas.

#### `prune_stale_memories(cutoff_days) -> PruningResult`
Remove experiências antigas.

#### `consolidate_lessons() -> List[ConsolidatedLesson]`
Agrupa lições similares.

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
OPENROUTER_API_KEY=sua-chave-aqui
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

1. **Memory Agent não responde**
   - Verifique se o container está rodando
   - Confirme a porta 9086 está acessível
   - Teste health check: `curl localhost:9086/health`

2. **Lições não são recuperadas**
   - Verifique se há experiências armazenadas
   - Confirme se a spec e stack estão corretas
   - Teste com diferentes filtros

3. **Deduplicação não funciona**
   - Verifique similaridade threshold
   - Confirme formato das experiências
   - Revise logs de erros

### Debug

```bash
# Ver logs do container
docker logs memory-agent

# Testar health check
curl http://localhost:9086/health

# Ver estatísticas
curl -X POST http://localhost:9086/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "memory_stats", "arguments": {}}'

# Via orquestrador
curl -X POST http://localhost:9080/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_memory_stats", "arguments": {}}'
```

## Exemplo Completo

```python
# 1. Armazenar experiência de segurança
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

# 2. Recuperar lições para nova feature
lessons = await memory_agent.lessons_for_task(
    spec="Create admin dashboard with user management",
    stack="python+fastapi+postgres+react"
)

# 3. Aplicar lições no desenvolvimento
for rule in lessons.get("high_level_rules", []):
    print(f"Rule: {rule['rule']}")
    print(f"Why: {rule['rationale']}")

# 4. Armazenar decisão arquitetônica
decision = {
    "project_id": "my-app",
    "module": "admin",
    "decision_type": "architecture",
    "decision": "Use RBAC for permissions",
    "rationale": "Granular control and auditability"
}
```

Este guia cobre todos os aspectos do Memory Agent. Para dúvidas adicionais, consulte os logs ou a equipe de desenvolvimento.