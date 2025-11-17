import os
import asyncio
import httpx
import json
import logging
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel
from functools import wraps
from collections import Counter
import hashlib
import datetime

logger = logging.getLogger(__name__)

Role = Literal["system", "user", "assistant"]
TaskType = Literal["orchestration", "code", "critique", "memory"]

class Message(BaseModel):
    role: Role
    content: str


def _retry_on_failure(max_attempts: int = 3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = 2**attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
        return wrapper
    return decorator


class ContextManager:
    """
    Gerencia contexto otimizado para diferentes tipos de tarefas.
    Prioriza informações por relevância e mantém janelas deslizantes.
    """
    
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.context_cache = {}
    
    async def prioritize_for_task(
        self,
        task_type: TaskType,
        available_context: Dict[str, Any],
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Prioriza informações por relevância semântica e retorna contexto otimizado.
        """
        max_tokens = max_tokens or self.max_tokens
        
        # Cache baseado no hash do contexto
        context_hash = hashlib.md5(
            json.dumps(available_context, sort_keys=True).encode()
        ).hexdigest()
        
        cache_key = f"{task_type}_{context_hash}"
        if cache_key in self.context_cache:
            return self.context_cache[cache_key]
        
        # Priorização baseada no tipo de tarefa
        prioritized = self._extract_relevant_context(task_type, available_context)
        
        # Trunca para não exceder max_tokens (estimativa: 1 token ≈ 4 chars)
        max_chars = max_tokens * 4
        if len(prioritized) > max_chars:
            prioritized = prioritized[:max_chars] + "..."
        
        self.context_cache[cache_key] = prioritized
        return prioritized
    
    def _extract_relevant_context(self, task_type: TaskType, context: Dict[str, Any]) -> str:
        """Extrai contexto relevante baseado no tipo de tarefa."""
        
        if task_type == "orchestration":
            # Foco em arquitetura, dependências e estado geral
            sections = []
            if "architecture" in context:
                sections.append(f"Architecture: {context['architecture']}")
            if "dependencies" in context:
                sections.append(f"Dependencies: {context['dependencies']}")
            if "project_state" in context:
                sections.append(f"Project State: {context['project_state']}")
            return "\n".join(sections)
        
        elif task_type == "code":
            # Foco em código, patterns e implementações
            sections = []
            if "code_snippets" in context:
                sections.append(f"Code Examples: {context['code_snippets']}")
            if "api_specs" in context:
                sections.append(f"API Specs: {context['api_specs']}")
            if "database_schema" in context:
                sections.append(f"Database: {context['database_schema']}")
            return "\n".join(sections)
        
        elif task_type == "critique":
            # Foco em requisitos, regras e padrões
            sections = []
            if "requirements" in context:
                sections.append(f"Requirements: {context['requirements']}")
            if "security_rules" in context:
                sections.append(f"Security Rules: {context['security_rules']}")
            if "performance_constraints" in context:
                sections.append(f"Performance: {context['performance_constraints']}")
            return "\n".join(sections)
        
        elif task_type == "memory":
            # Foco em experiências passadas e lições aprendidas
            sections = []
            if "past_experiences" in context:
                sections.append(f"Past Experiences: {context['past_experiences']}")
            if "lessons_learned" in context:
                sections.append(f"Lessons: {context['lessons_learned']}")
            if "error_patterns" in context:
                sections.append(f"Error Patterns: {context['error_patterns']}")
            return "\n".join(sections)
        
        return str(context)


class LLMRouter:
    """
    Roteador LLM com 3 modelos especializados via OpenRouter:
    - GLM-4.5-Air: Orquestração e estratégia
    - Qwen3-235B: Código e raciocínio pesado
    - DeepSeek-V3.1: Crítica e revisão
    """

    def __init__(self) -> None:
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_timeout = 90.0
        self.max_retries = 3
        self.context_manager = ContextManager()
        
        # Estatísticas de uso
        self.call_stats = Counter()

    async def _call_openrouter(
        self,
        model: str,
        messages: List[Message] | List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """Método base para chamadas à API OpenRouter."""
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY não configurada")

        # Normaliza messages para dict se necessário
        if messages and isinstance(messages[0], Message):
            messages = [m.model_dump() for m in messages]

        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://blue-ai-agents",
            "X-Title": "Blue AI Multi-Agent System",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        payload.update(kwargs)

        async with httpx.AsyncClient(timeout=self.default_timeout) as client:
            logger.info(f"Calling {model} with {len(messages)} messages")
            resp = await client.post(self.openrouter_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        logger.info(f"{model} response: {len(content)} chars")
        return content

    @_retry_on_failure(max_attempts=3)
    async def glm_air(
        self,
        messages: List[Message] | List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        reasoning: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        GLM-4.5-Air: Maestro/Orquestrador.
        Ideal para: planejamento, estratégia, conciliação de opiniões.
        """
        self.call_stats["glm_air"] += 1
        
        payload_kwargs = {}
        if reasoning:
            payload_kwargs["reasoning"] = {"enabled": True}
        
        return await self._call_openrouter(
            "z-ai/glm-4.5-air:free",
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **payload_kwargs,
            **kwargs
        )

    @_retry_on_failure(max_attempts=3)
    async def qwen3_235b(
        self,
        messages: List[Message] | List[Dict[str, Any]],
        temperature: float = 0.15,
        max_tokens: int = 8192,
        **kwargs: Any,
    ) -> str:
        """
        Qwen3-235B: Dev sênior/cérebro de código.
        Ideal para: código pesado, arquitetura detalhada, 262k contexto.
        """
        self.call_stats["qwen3_235b"] += 1
        
        return await self._call_openrouter(
            "qwen/qwen3-235b-a22b-2507",
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    @_retry_on_failure(max_attempts=3)
    async def deepseek_v3(
        self,
        messages: List[Message] | List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """
        DeepSeek V3.1: Crítico/revisor agressivo.
        Ideal para: revisão de código, segurança, segundo parecer.
        """
        self.call_stats["deepseek_v3"] += 1
        
        return await self._call_openrouter(
            "deepseek/deepseek-chat-v3.1:free",
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

    async def route_with_fallback(
        self,
        task: TaskType,
        messages: List[Message] | List[Dict[str, Any]],
        max_retries: int = 2,
        **kwargs: Any,
    ) -> str:
        """
        Roteamento com fallback inteligente entre os 3 modelos.
        """
        # Mapeamento primário
        primary_models = {
            "orchestration": self.glm_air,
            "code": self.qwen3_235b,
            "critique": self.deepseek_v3,
            "memory": self.qwen3_235b,  # Qwen é mais estável para estruturar regras
        }
        
        # Fallbacks sensatos
        fallbacks = {
            "orchestration": [self.qwen3_235b],  # Qwen pode orquestrar se GLM cair
            "code": [self.deepseek_v3],  # DeepSeek é forte em código também
            "critique": [self.qwen3_235b],  # Qwen pode criticar
            "memory": [self.glm_air],  # GLM pode estruturar memórias
        }
        
        primary_func = primary_models[task]
        fallback_funcs = fallbacks[task]
        
        # Tenta modelo primário
        try:
            logger.info(f"Trying primary model for {task}")
            return await primary_func(messages, **kwargs)
        except Exception as e:
            logger.warning(f"Primary model for {task} failed: {e}")
            
            # Tenta fallbacks
            for fallback_func in fallback_funcs:
                try:
                    logger.info(f"Trying fallback model for {task}")
                    return await fallback_func(messages, **kwargs)
                except Exception as fallback_error:
                    logger.warning(f"Fallback model for {task} failed: {fallback_error}")
                    continue
            
            raise RuntimeError(f"All models failed for task: {task}")

    async def smart_route(
        self,
        task_type: TaskType,
        messages: List[Message] | str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Roteamento inteligente com gestão de contexto e fallback.
        """
        # Converte string para Message se necessário
        if isinstance(messages, str):
            messages = [Message(role="user", content=messages)]
        
        # Aplica gestão de contexto se fornecido
        if context:
            optimized_context = await self.context_manager.prioritize_for_task(
                task_type, context
            )
            
            # Insere contexto otimizado como system message
            context_message = Message(
                role="system",
                content=f"Contexto relevante para esta tarefa:\n{optimized_context}"
            )
            messages = [context_message] + list(messages)
        
        # Usa roteamento com fallback
        return await self.route_with_fallback(task_type, messages, **kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso dos modelos."""
        return {
            "call_counts": dict(self.call_stats),
            "total_calls": sum(self.call_stats.values()),
            "cache_size": len(self.context_manager.context_cache)
        }

    # Métodos legados para compatibilidade
    async def call_glm46(
        self,
        messages: List[Message] | List[Dict[str, Any]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> str:
        """
        Método legado - redireciona para GLM-4.5-Air.
        """
        logger.warning("call_glm46 is deprecated, use glm_air instead")
        return await self.glm_air(messages, temperature, max_tokens, **kwargs)