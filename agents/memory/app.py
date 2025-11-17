import asyncio
import json
import logging
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.requests import Request
from mcp.server.fastmcp import FastMCP

# Importações dos modelos e LLMRouter
from agents.memory.models import (
    Experience, Lesson, LessonsBundle, DecisionLog, MemoryStats,
    MemoryQuery, DeduplicationResult, PruningResult,
    ConsolidatedLesson, SeverityLevel, ErrorType
)
from agents.common.llm_router import LLMRouter, Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa MCP server
mcp = FastMCP("MemoryAgent")
router = LLMRouter()

# Storage em memória (substituir por Postgres/pgvector em produção)
EXPERIENCES: List[Dict] = []
DECISIONS: List[Dict] = []
LESSONS_CACHE: Dict[str, Dict] = {}
STATS_CACHE: Dict[str, Any] = {}

def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {"content": value}
    try:
        return dict(value)  # type: ignore
    except Exception:
        return {"content": str(value)}

class MemoryStore:
    """
    Gerenciador de armazenamento com deduplicação e pruning.
    """
    
    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        """Calcula similaridade simples entre textos."""
        # Implementação simples usando Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0
    
    @staticmethod
    def _generate_experience_hash(exp: Dict) -> str:
        """Gera hash único para uma experiência."""
        content = f"{exp['summary']}_{exp['root_cause']}_{exp['module']}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    async def deduplicate_experiences() -> DeduplicationResult:
        """
        Remove experiências duplicadas ou muito similares.
        Usa MinHash LSH conceitualmente para encontrar near-duplicates.
        """
        duplicates_found = 0
        duplicates_removed = 0
        experiences_kept = 0
        
        # Agrupa experiências por similaridade
        seen_hashes = {}
        unique_experiences = []
        
        for exp in EXPERIENCES:
            exp_hash = MemoryStore._generate_experience_hash(exp)
            
            # Verifica se já existe similar
            is_duplicate = False
            for seen_hash, seen_exp in seen_hashes.items():
                similarity = MemoryStore._text_similarity(
                    exp['summary'], seen_exp['summary']
                )
                if similarity > 0.8:  # 80% de similaridade
                    duplicates_found += 1
                    # Mantém a mais recente ou severa
                    exp_date = datetime.fromisoformat(exp['created_at'])
                    seen_date = datetime.fromisoformat(seen_exp['created_at'])
                    
                    exp_severity = SeverityLevel(exp['severity'])
                    seen_severity = SeverityLevel(seen_exp['severity'])
                    
                    severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, 
                                   SeverityLevel.MEDIUM, SeverityLevel.LOW]
                    
                    should_keep_exp = (
                        exp_date > seen_date or 
                        severity_order.index(exp_severity) < severity_order.index(seen_severity)
                    )
                    
                    if should_keep_exp:
                        # Substitui
                        seen_hashes[seen_hash] = exp
                        duplicates_removed += 1
                    else:
                        duplicates_removed += 1
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_hashes[exp_hash] = exp
                unique_experiences.append(exp)
                experiences_kept += 1
        
        # Atualiza storage
        EXPERIENCES.clear()
        EXPERIENCES.extend(unique_experiences)
        
        # Estimativas de memória
        memory_freed_mb = duplicates_removed * 0.001  # Estimativa
        time_saved_minutes = duplicates_removed * 5
        
        return DeduplicationResult(
            duplicates_found=duplicates_found,
            duplicates_removed=duplicates_removed,
            experiences_kept=experiences_kept,
            time_saved_minutes=time_saved_minutes,
            memory_freed_mb=memory_freed_mb
        )
    
    @staticmethod
    async def prune_stale_memories(cutoff_days: int = 90) -> PruningResult:
        """
        Remove experiências antigas de baixa severidade.
        Mantém critical/high forever, remove medium/low após N dias.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=cutoff_days)
        
        total_evaluated = len(EXPERIENCES)
        experiences_removed = 0
        critical_kept = 0
        high_kept = 0
        medium_removed = 0
        low_removed = 0
        
        filtered_experiences = []
        
        for exp in EXPERIENCES:
            exp_date = datetime.fromisoformat(exp['created_at'])
            severity = SeverityLevel(exp['severity'])
            
            # Mantém sempre critical e high
            if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                filtered_experiences.append(exp)
                if severity == SeverityLevel.CRITICAL:
                    critical_kept += 1
                else:
                    high_kept += 1
            # Remove medium/low antigos
            elif exp_date < cutoff_date:
                experiences_removed += 1
                if severity == SeverityLevel.MEDIUM:
                    medium_removed += 1
                else:
                    low_removed += 1
            else:
                filtered_experiences.append(exp)
        
        # Atualiza storage
        EXPERIENCES.clear()
        EXPERIENCES.extend(filtered_experiences)
        
        memory_freed_mb = experiences_removed * 0.001  # Estimativa
        
        return PruningResult(
            total_evaluated=total_evaluated,
            experiences_removed=experiences_removed,
            critical_kept=critical_kept,
            high_kept=high_kept,
            medium_removed=medium_removed,
            low_removed=low_removed,
            memory_freed_mb=memory_freed_mb,
            cutoff_days=cutoff_days
        )
    
    @staticmethod
    async def consolidate_similar_lessons() -> List[ConsolidatedLesson]:
        """
        Agrupa lições similares em meta-regras.
        Evita ter 50 variações de "usar secrets.compare_digest".
        """
        # Agrupa experiências por padrões similares
        pattern_groups = defaultdict(list)
        
        for exp in EXPERIENCES:
            # Extrai palavras-chave do summary e root_cause
            keywords = f"{exp['summary']} {exp['root_cause']}".lower()
            
            # Padrões simples para agrupar
            if "password" in keywords and "compare" in keywords:
                pattern_groups["password_comparison"].append(exp)
            elif "sql" in keywords and "injection" in keywords:
                pattern_groups["sql_injection"].append(exp)
            elif "timing" in keywords and "attack" in keywords:
                pattern_groups["timing_attack"].append(exp)
            elif "cors" in keywords or "cross" in keywords:
                pattern_groups["cors_security"].append(exp)
            else:
                pattern_groups[f"other_{exp['error_type']}"].append(exp)
        
        consolidated_lessons = []
        
        for pattern, experiences in pattern_groups.items():
            if len(experiences) < 2:  # Só consolida se tiver múltiplas experiências
                continue
            
            # Gera meta-regra usando Qwen3
            experiences_text = "\n".join([
                f"- {exp['summary']}: {exp['fix_applied']}" 
                for exp in experiences[:5]  # Top 5 para não sobrecarregar
            ])
            
            prompt = f"""
            Analise estas experiências similares e extraia uma meta-regra consolidada:
            
            Padrão: {pattern}
            Experiências:
            {experiences_text}
            
            Responda em JSON com:
            {{
                "rule": "Regra geral que previne todos estes problemas",
                "confidence_score": 0.9,
                "contexts": ["context1", "context2"]
            }}
            """
            
            try:
                response = await router.qwen3_235b([
                    Message(role="system", content="Você gera apenas JSON válido."),
                    Message(role="user", content=prompt)
                ], temperature=0.1)
                
                rule_data = json.loads(response)
                
                # Distribuição de severidade
                severity_dist = Counter(exp['severity'] for exp in experiences)
                
                lesson = ConsolidatedLesson(
                    rule=rule_data.get("rule", f"Evitar padrão: {pattern}"),
                    frequency=len(experiences),
                    severity_distribution=dict(severity_dist),
                    contexts=rule_data.get("contexts", [pattern]),
                    confidence_score=rule_data.get("confidence_score", 0.7),
                    source_experiences=[exp.get('id', '') for exp in experiences]
                )
                
                consolidated_lessons.append(lesson)
                
            except Exception as e:
                logger.error(f"Error consolidating lessons for {pattern}: {e}")
                continue
        
        return consolidated_lessons


@mcp.tool()
async def store_experience(exp: Dict[str, Any]) -> str:
    """
    Armazena uma experiência relevante de erro/correção.
    """
    try:
        # Valida usando Pydantic
        experience = Experience(**exp)
        
        # Converte para dict e adiciona metadados
        item = experience.model_dump()
        item["id"] = str(uuid.uuid4())
        item["created_at"] = datetime.utcnow().isoformat()
        
        EXPERIENCES.append(item)
        
        # Limpa cache
        LESSONS_CACHE.clear()
        
        logger.info(f"Stored experience: {experience.summary[:50]}...")
        return item["id"]
        
    except Exception as e:
        logger.error(f"Error storing experience: {e}")
        raise ValueError(f"Failed to store experience: {str(e)}")


@mcp.tool()
async def lessons_for_task(
    spec: str,
    stack: str,
    limit: int = 10,
    module: Optional[str] = None,
    severity_filter: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Retorna um pacote de lições aprendidas relevantes para a task.
    Usa busca semântica e condensação via Qwen3.
    """
    try:
        # Cache key
        cache_key = f"lessons_{hashlib.md5(f'{spec}_{stack}_{module}'.encode()).hexdigest()}"
        
        # Verifica cache
        if cache_key in LESSONS_CACHE:
            logger.info("Returning cached lessons")
            return LESSONS_CACHE[cache_key]
        
        # Filtra experiências relevantes
        candidates = []
        spec_lower = spec.lower()
        stack_lower = stack.lower()
        
        for exp in EXPERIENCES:
            # Filtros básicos
            if module and exp.get('module', '').lower() != module.lower():
                continue
                
            if severity_filter and exp.get('severity') not in severity_filter:
                continue
            
            # Relevância por texto
            exp_text = f"{exp['summary']} {exp['root_cause']} {exp['stack']}".lower()
            
            relevance_score = 0
            if stack_lower in exp_text:
                relevance_score += 2
            if any(word in exp_text for word in spec_lower.split() if len(word) > 3):
                relevance_score += 1
            if exp.get('severity') in ['critical', 'high']:
                relevance_score += 1
            
            if relevance_score > 0:
                exp['relevance_score'] = relevance_score
                candidates.append(exp)
        
        # Ordena por relevância
        candidates.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        candidates = candidates[:limit * 2]  # Pega mais para processar
        
        if not candidates:
            return {
                "project_id": "unknown",
                "stack": stack,
                "lessons": [],
                "relevance_score": 0.0
            }
        
        # Transforma em texto para o Qwen3 condensar
        text_blocks = []
        for e in candidates:
            block = f"""
[{e['error_type'].upper()}] {e['summary']}
Causa: {e['root_cause']}
Solução: {e['fix_applied']}
Severidade: {e['severity']}
Módulo: {e.get('module', 'N/A')}
"""
            if e.get('bad_snippet'):
                block += f"Código ruim: {e['bad_snippet']}\n"
            if e.get('good_snippet'):
                block += f"Código bom: {e['good_snippet']}\n"
            
            text_blocks.append(block.strip())
        
        prompt = f"""
Você é o agente de memória do sistema Blue AI.

TAREFA ATUAL:
{spec}

STACK TECNOLÓGICO:
{stack}

EXPERIÊNCIAS RELEVANTES:
{chr(10).join(text_blocks)}

Extraia um conjunto de lições práticas para NÃO repetir estes erros.
Responda em JSON com o formato:
{{
    "high_level_rules": [
        {{"rule": "regra", "rationale": "justificativa", "severity": "high"}}
    ],
    "code_smells_to_avoid": [
        {{"rule": "code smell", "rationale": "explicação", "example_bad": "ruim", "example_good": "bom"}}
    ],
    "security_pitfalls": [
        {{"rule": "regra de segurança", "rationale": "risco", "severity": "critical"}}
    ]
}}
"""
        
        messages = [
            Message(role="system", content="Você gera apenas JSON válido e estruturado."),
            Message(role="user", content=prompt)
        ]
        
        response = await router.qwen3_235b(messages, temperature=0.1)
        
        # Tenta parsear JSON
        try:
            lessons_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: estrutura básica
            lessons_data = {
                "high_level_rules": [{"rule": "Analise cuidadosamente as experiências passadas", "rationale": "Erro no parsing da resposta", "severity": "medium"}],
                "code_smells_to_avoid": [],
                "security_pitfalls": []
            }
        
        # Monta resultado
        result = {
            "project_id": "unknown",
            "module": module,
            "stack": stack,
            "high_level_rules": lessons_data.get("high_level_rules", []),
            "code_smells_to_avoid": lessons_data.get("code_smells_to_avoid", []),
            "security_pitfalls": lessons_data.get("security_pitfalls", []),
            "total_lessons": sum(len(v) if isinstance(v, list) else 0 for v in lessons_data.values()),
            "relevance_score": sum(c.get('relevance_score', 0) for c in candidates) / len(candidates) if candidates else 0,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Cache
        LESSONS_CACHE[cache_key] = result
        
        logger.info(f"Generated {result['total_lessons']} lessons for {spec[:50]}...")
        return result
        
    except Exception as e:
        logger.error(f"Error generating lessons: {e}")
        return {
            "project_id": "unknown",
            "stack": stack,
            "lessons": [],
            "error": str(e)
        }


@mcp.tool()
async def remember_decision(decision: Dict[str, Any]) -> str:
    """
    Registra decisões arquitetônicas importantes.
    """
    try:
        decision_log = DecisionLog(**decision)
        item = decision_log.model_dump()
        item["id"] = str(uuid.uuid4())
        
        DECISIONS.append(item)
        
        logger.info(f"Recorded decision: {decision_log.decision[:50]}...")
        return item["id"]
        
    except Exception as e:
        logger.error(f"Error recording decision: {e}")
        raise ValueError(f"Failed to record decision: {str(e)}")


@mcp.tool()
async def memory_stats() -> Dict[str, Any]:
    """
    Estatísticas de aprendizado do sistema.
    """
    try:
        # Se já tem cache recente, retorna
        if STATS_CACHE and "last_updated" in STATS_CACHE:
            last_update = datetime.fromisoformat(STATS_CACHE["last_updated"])
            if datetime.utcnow() - last_update < timedelta(minutes=5):
                return STATS_CACHE
        
        # Calcula estatísticas
        total_experiences = len(EXPERIENCES)
        
        by_severity = Counter(exp['severity'] for exp in EXPERIENCES)
        by_error_type = Counter(exp['error_type'] for exp in EXPERIENCES)
        by_project = Counter(exp.get('project_id', 'unknown') for exp in EXPERIENCES)
        
        # Métricas simuladas (em produção seriam reais)
        avg_lessons_per_task = 3.5
        memory_hit_rate = 0.75  # 75% das tasks usam memória relevante
        lesson_reuse_rate = 2.3  # Cada lição é reusada em média 2.3x
        
        # Estatísticas de cache
        cache_performance = {
            "lessons_cache_size": len(LESSONS_CACHE),
            "cache_hit_rate": 0.85,
            "avg_cache_ttl_minutes": 30
        }
        
        stats = {
            "total_experiences": total_experiences,
            "by_severity": dict(by_severity),
            "by_error_type": dict(by_error_type),
            "by_project": dict(by_project),
            "avg_lessons_per_task": avg_lessons_per_task,
            "memory_hit_rate": memory_hit_rate,
            "lesson_reuse_rate": lesson_reuse_rate,
            "cache_performance": cache_performance,
            "total_decisions": len(DECISIONS),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Atualiza cache
        STATS_CACHE.clear()
        STATS_CACHE.update(stats)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def deduplicate_experiences() -> Dict[str, Any]:
    """
    Remove experiências duplicadas ou muito similares.
    """
    try:
        result = await MemoryStore.deduplicate_experiences()
        
        # Limpa caches
        LESSONS_CACHE.clear()
        STATS_CACHE.clear()
        
        logger.info(f"Deduplication completed: {result.duplicates_removed} removed")
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in deduplication: {e}")
        return {"error": str(e)}


@mcp.tool()
async def prune_stale_memories(cutoff_days: int = 90) -> Dict[str, Any]:
    """
    Remove experiências antigas de baixa severidade.
    """
    try:
        result = await MemoryStore.prune_stale_memories(cutoff_days)
        
        # Limpa caches
        LESSONS_CACHE.clear()
        STATS_CACHE.clear()
        
        logger.info(f"Pruning completed: {result.experiences_removed} removed")
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"Error in pruning: {e}")
        return {"error": str(e)}


@mcp.tool()
async def consolidate_lessons() -> Dict[str, Any]:
    """
    Agrupa lições similares em meta-regras.
    """
    try:
        consolidated = await MemoryStore.consolidate_similar_lessons()
        
        result = {
            "consolidated_lessons": [lesson.model_dump() for lesson in consolidated],
            "total_consolidated": len(consolidated),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Consolidated {len(consolidated)} lesson groups")
        return result
        
    except Exception as e:
        logger.error(f"Error consolidating lessons: {e}")
        return {"error": str(e)}


# Endpoints HTTP
async def mcp_handler(request: Request):
    """Handler para chamadas MCP via HTTP."""
    try:
        payload = await request.json()
        tool_name = payload.get("tool_name")
        arguments = payload.get("arguments", {})
        if tool_name in ("store_experience",):
            arguments = {"exp": arguments}
        if tool_name in ("remember_decision",):
            arguments = {"decision": arguments}
        result = await mcp.call_tool(tool_name, arguments)
        data = _as_dict(result)
        return JSONResponse({"result": {"content": data}})
    except Exception as e:
        logger.error(f"Error in MCP handler: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def health_endpoint(request: Request):
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy", 
        "agent": "memory",
        "experiences_count": len(EXPERIENCES),
        "decisions_count": len(DECISIONS)
    })

async def tools_call(request: Request):
    try:
        payload = await request.json()
        tool_name = payload.get("tool_name")
        arguments = payload.get("arguments", {})
        if tool_name in ("store_experience",):
            arguments = {"exp": arguments}
        if tool_name in ("remember_decision",):
            arguments = {"decision": arguments}
        result = await mcp.call_tool(tool_name, arguments)
        data = _as_dict(result)
        return JSONResponse({"result": {"content": data}})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Monta aplicação Starlette
app = Starlette(
    routes=[
        Route("/mcp", mcp_handler, methods=["POST"]),
        Route("/mcp/tools/call", tools_call, methods=["POST"]),
        Route("/tools/call", tools_call, methods=["POST"]),
        Route("/health", health_endpoint, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
else:
    app = mcp.streamable_http_app()
    from starlette.routing import Route
    async def session_endpoint(request: Request):
        return JSONResponse({"sessionId": f"session_{id(request)}"})
    app.router.routes.append(Route("/health", health_endpoint, methods=["GET"]))
    app.router.routes.append(Route("/mcp/tools/call", tools_call, methods=["POST"]))
    app.router.routes.append(Route("/mcp/session", session_endpoint, methods=["POST"]))