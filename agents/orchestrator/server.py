import asyncio
import json
import logging
import os
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from mcp import client
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Importa o LLMRouter do common
from llm_router import LLMRouter, Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa MCP server para IDE (stdio)
mcp = FastMCP("BlueOrchestrator")
router = LLMRouter()

# Clientes MCP para agentes internos (HTTP)
class AgentClients:
    """Gerencia conexões HTTP para agentes especializados"""
    
    def __init__(self):
        # Usa nomes de serviço do Docker Compose para comunicação interna
        self.architect_url = "http://architect-agent:8080/mcp"
        self.designer_url = "http://designer-agent:8080/mcp"
        self.coder_url = "http://coder-agent:8080/mcp"
        self.auditor_url = "http://auditor-agent:8080/mcp"
        self.stack_url = "http://stack-research-agent:8080/mcp"
        memory_base = os.getenv("MEMORY_AGENT_URL", "http://memory-agent:8080")
        self.memory_url = f"{memory_base}/mcp"
    
    async def call_agent(
        self,
        agent_url: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Chama tool de um agente via MCP HTTP usando transporte simplificado.
        """
        import httpx
        
        # Usa uma abordagem direta - envia para um endpoint simplificado
        # que criaremos nos agentes
        payload = {
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            logger.info(f"Calling {agent_url}/tools/call -> {tool_name}")
            for attempt in range(3):
                try:
                    resp = await client.post(f"{agent_url}/tools/call", json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception as e:
                    if attempt == 2:
                        raise e
                    await asyncio.sleep(2 ** attempt)
        
        if "error" in data:
            raise Exception(f"Agent error: {data['error']}")
        
        return data.get("result", {})

agents = AgentClients()


@mcp.tool()
async def build_feature(spec: str, context: str = "", stack: str = "python+fastapi+react") -> str:
    """
    Orquestra pipeline completo para implementar uma feature com memória de aprendizado:
    0. Memory: busca lições aprendidas
    1. Architect: propõe arquitetura (com lições)
    2. StackResearch: mapeia imports e versões
    3. Designer: cria layout e componentes (com lições)
    4. Coder: gera código (com lições)
    5. Auditor: revisa código (com lições)
    6. Memory: armazena experiências da execução
    
    Args:
        spec: Especificação da feature (user story, requisitos)
        context: Contexto adicional (código existente, constraints)
        stack: Stack tecnológico (ex: python+fastapi+react)
    
    Returns:
        Resultado estruturado com arquitetura, código e review
    """
    logger.info(f"Building feature: {spec[:100]}...")
    
    try:
        # Step 0: Buscar lições da memória
        logger.info("Step 0/6: Loading learned lessons")
        lessons_result = await agents.call_agent(
            agents.memory_url,
            "lessons_for_task",
            {
                "spec": spec,
                "stack": stack,
                "limit": 10
            }
        )
        lessons = _as_dict(lessons_result)
        
        # Prepara contexto com lições aprendidas
        lessons_text = ""
        if lessons and lessons.get("total_lessons", 0) > 0:
            lessons_text = "LIÇÕES APRENDIDAS (NÃO REPETIR ESTES ERROS):\n"
            
            # High-level rules
            if lessons.get("high_level_rules"):
                lessons_text += "\nRegras de Alto Nível:\n"
                for rule in lessons["high_level_rules"]:
                    lessons_text += f"- {rule.get('rule', '')}: {rule.get('rationale', '')}\n"
            
            # Code smells
            if lessons.get("code_smells_to_avoid"):
                lessons_text += "\nCode Smells a Evitar:\n"
                for smell in lessons["code_smells_to_avoid"]:
                    lessons_text += f"- {smell.get('rule', '')}: {smell.get('rationale', '')}\n"
            
            # Security pitfalls
            if lessons.get("security_pitfalls"):
                lessons_text += "\nArmadilhas de Segurança:\n"
                for pitfall in lessons["security_pitfalls"]:
                    lessons_text += f"- {pitfall.get('rule', '')}: {pitfall.get('rationale', '')}\n"
            
            logger.info(f"Loaded {lessons.get('total_lessons', 0)} lessons from memory")
        
        # Contexto enriquecido com lições
        enriched_context = f"{context}\n\n{lessons_text}" if lessons_text else context
        
        # Step 1: Arquitetura (com lições)
        logger.info("Step 1/6: Architecture planning")
        arch_result = await agents.call_agent(
            agents.architect_url,
            "propose_architecture",
            {
                "spec": spec,
                "context": enriched_context,
                "lessons": lessons,
                "stack": stack
            }
        )
        architecture = _as_dict(arch_result)
        
        # Step 2: Stack Research (imports atualizados)
        logger.info("Step 2/6: Stack research")
        
        # Extrai bibliotecas mencionadas
        libraries = ["react", "fastapi", "@tanstack/react-query"]  # Smart detection aqui
        
        stack_result = await agents.call_agent(
            agents.stack_url,
            "get_stack_snapshot",
            {"libraries": libraries}
        )
        imports_map = _as_dict(stack_result)
        
        # Step 3: UI/UX Design (com lições)
        logger.info("Step 3/6: UI/UX design")
        design_result = await agents.call_agent(
            agents.designer_url,
            "design_ui",
            {
                "spec": spec,
                "architecture": architecture,
                "ux_goals": ["responsive", "accessible", "modern"],
                "lessons": lessons,
                "context": enriched_context
            }
        )
        ui_design = _as_dict(design_result)
        
        # Step 4: Code Generation (com lições)
        logger.info("Step 4/6: Code generation")
        code_result = await agents.call_agent(
            agents.coder_url,
            "generate_code",
            {
                "spec": spec,
                "architecture": architecture,
                "ui_design": ui_design,
                "imports": imports_map,
                "lessons": lessons,
                "context": enriched_context
            }
        )
        code = _as_dict(code_result)
        
        # Step 5: Code Review (com lições)
        logger.info("Step 5/6: Code review")
        review_result = await agents.call_agent(
            agents.auditor_url,
            "review_code",
            {
                "code": code,
                "context": {
                    "spec": spec,
                    "architecture": architecture,
                    "lessons": lessons
                }
            }
        )
        review = _as_dict(review_result)
        
        # Step 6: Armazenar experiências relevantes
        logger.info("Step 6/6: Storing experiences")
        await _store_execution_experiences(spec, stack, architecture, code, review)
        
        # Agrega resultados
        final_output = {
            "architecture": architecture,
            "imports": imports_map,
            "ui_design": ui_design,
            "code": code,
            "review": review,
            "lessons_applied": lessons,
            "status": "success"
        }
        
        # Formata para apresentação
        formatted = await _format_feature_output(final_output)
        
        logger.info("Feature build complete!")
        return formatted
        
    except Exception as e:
        logger.error(f"Error building feature: {e}", exc_info=True)
        
        # Armazena experiência de erro
        try:
            await _store_error_experience(spec, stack, str(e))
        except Exception as store_error:
            logger.error(f"Failed to store error experience: {store_error}")
        
        return f"Error: {str(e)}\n\nPlease check logs for details."

async def _store_execution_experiences(
    spec: str, 
    stack: str, 
    architecture: Dict, 
    code: Dict, 
    review: Dict
) -> None:
    """
    Armazena experiências da execução bem-sucedida.
    """
    try:
        # Extrai problemas do review
        issues = review.get("issues", [])
        high_issues = [i for i in issues if i.get("severity") in ["high", "critical"]]
        
        if high_issues:
            # Armazena experiência de problemas encontrados
            for issue in high_issues:
                experience = {
                    "project_id": "blue-ai-agents",
                    "module": issue.get("file", "unknown"),
                    "stack": stack,
                    "severity": issue.get("severity", "high"),
                    "error_type": "bug",
                    "summary": issue.get("description", ""),
                    "root_cause": "Code generation issue detected in review",
                    "fix_applied": issue.get("suggestion", ""),
                    "tags": ["code-review", "auto-generated"],
                    "affected_components": [issue.get("file", "unknown")]
                }
                
                await agents.call_agent(
                    agents.memory_url,
                    "store_experience",
                    experience
                )
        
        # Armazena decisão arquitetônica
        if architecture:
            decision = {
                "project_id": "blue-ai-agents",
                "module": "architecture",
                "decision_type": "architecture",
                "decision": f"Architecture for: {spec[:50]}...",
                "rationale": architecture.get("rationale", "Generated based on requirements"),
                "alternatives_considered": architecture.get("alternatives", [])
            }
            
            await agents.call_agent(
                agents.memory_url,
                "remember_decision",
                decision
            )
            
    except Exception as e:
        logger.error(f"Error storing execution experiences: {e}")


async def _store_error_experience(spec: str, stack: str, error_msg: str) -> None:
    """
    Armazena experiência de erro na execução.
    """
    try:
        experience = {
            "project_id": "blue-ai-agents",
            "module": "orchestrator",
            "stack": stack,
            "severity": "high",
            "error_type": "bug",
            "summary": f"Pipeline execution failed for: {spec[:50]}...",
            "root_cause": "Orchestration pipeline error",
            "fix_applied": "Needs investigation",
            "tags": ["pipeline-error", "orchestrator"],
            "affected_components": ["orchestrator"],
            "llm_comment": error_msg
        }
        
        await agents.call_agent(
            agents.memory_url,
            "store_experience",
            experience
        )
        
    except Exception as e:
        logger.error(f"Error storing error experience: {e}")



@mcp.tool()
async def quick_code(
    description: str,
    language: str = "python",
    style: str = "modern"
) -> str:
    """
    Geração rápida de código usando os 3 modelos especializados.
    Usa Qwen3-235B para código, com fallback para outros modelos.
    
    Args:
        description: O que o código deve fazer
        language: python | typescript | javascript
        style: modern | minimal | verbose
    
    Returns:
        Código gerado
    """
    messages = [
        Message(
            role="system",
            content=f"You are an expert {language} developer. "
                    f"Generate {style} code that follows best practices."
        ),
        Message(
            role="user",
            content=f"Generate code for: {description}"
        )
    ]
    
    if not router.openrouter_key:
        # Fallback stub
        if language == "python":
            return f"def main():\n    print('hello')\n\nif __name__ == '__main__':\n    main()"
        if language == "typescript":
            return "export function sum(a:number,b:number){return a+b}"
        return "function sum(a,b){return a+b}"
    
    try:
        # Usa Qwen3-235B para código com fallback
        code = await router.smart_route("code", messages, temperature=0.1)
        return code
    except Exception as e:
        logger.warning(f"Qwen3 failed for quick_code, trying fallback: {e}")
        # Fallback para GLM-Air
        try:
            code = await router.glm_air(messages, temperature=0.1)
            return code
        except Exception as e2:
            logger.error(f"All models failed for quick_code: {e2}")
            return f"// Error generating code: {str(e2)}"


@mcp.tool()
async def memory_maintenance() -> str:
    """
    Executa manutenção da memória: deduplicação e pruning.
    """
    try:
        results = []
        
        # Deduplicação
        dedup_result = await agents.call_agent(
            agents.memory_url,
            "deduplicate_experiences",
            {}
        )
        results.append(f"Deduplication: {dedup_result}")
        
        # Pruning de memórias antigas
        prune_result = await agents.call_agent(
            agents.memory_url,
            "prune_stale_memories",
            {"cutoff_days": 90}
        )
        results.append(f"Pruning: {prune_result}")
        
        # Consolidação de lições
        consolidate_result = await agents.call_agent(
            agents.memory_url,
            "consolidate_lessons",
            {}
        )
        results.append(f"Consolidation: {consolidate_result}")
        
        # Estatísticas finais
        stats = await agents.call_agent(
            agents.memory_url,
            "memory_stats",
            {}
        )
        results.append(f"Stats: {stats}")
        
        return "\n\n".join([str(r) for r in results])
        
    except Exception as e:
        logger.error(f"Error in memory maintenance: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_memory_stats() -> str:
    """
    Retorna estatísticas da memória de aprendizado.
    """
    try:
        stats = await agents.call_agent(
            agents.memory_url,
            "memory_stats",
            {}
        )
        
        # Formata para exibição
        formatted = "# Memory Agent Statistics\n\n"
        if isinstance(stats, dict):
            for key, value in stats.items():
                formatted += f"**{key.replace('_', ' ').title()}:** {value}\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def research_stack(library: str, context: str = "") -> str:
    """
    Pesquisa informações atualizadas sobre uma biblioteca.
    
    Args:
        library: Nome da biblioteca (ex: 'react', '@tanstack/react-query')
        context: Contexto adicional (ex: 'typescript', 'next.js 15')
    
    Returns:
        Informações estruturadas: versão, imports, exemplos, notas
    """
    result = await agents.call_agent(
        agents.stack_url,
        "get_imports",
        {"library": library, "context": context}
    )
    import_data = _as_dict(result)
    
    # Formata para legibilidade
    formatted = f"# {import_data.get('library', library)}\n\n"
    formatted += f"**Version:** {import_data.get('recommended_version', 'N/A')}\n\n"
    
    if imports := import_data.get('imports', []):
        formatted += "## Imports\n\n"
        for imp in imports[:5]:  # Top 5
            formatted += f"```{context or 'typescript'}\n{imp.get('import_line', '')}\n```\n\n"
    
    if notes := import_data.get('notes', []):
        formatted += "## Notes\n\n"
        for note in notes:
            formatted += f"- {note}\n"
    
    return formatted


async def _format_feature_output(data: Dict[str, Any]) -> str:
    """
    Formata output do build_feature para apresentação limpa.
    """
    # Estrutura básica
    output = "# Feature Implementation\n\n"
    
    # Architecture
    if arch := data.get("architecture"):
        output += "## Architecture\n\n"
        output += json.dumps(arch, indent=2)
        output += "\n\n"
    
    # Code
    if code := data.get("code"):
        output += "## Code\n\n"
        
        backend_files = code.get("backend", {}).get("files", [])
        frontend_files = code.get("frontend", {}).get("files", [])
        
        if backend_files:
            output += "### Backend\n\n"
            for file in backend_files[:3]:  # Top 3 arquivos
                path = file.get("path", "unknown")
                content = file.get("content", "")
                output += f"**{path}**\n\n```python\n{content[:500]}...\n```\n\n"
        
        if frontend_files:
            output += "### Frontend\n\n"
            for file in frontend_files[:3]:
                path = file.get("path", "unknown")
                content = file.get("content", "")
                output += f"**{path}**\n\n```typescript\n{content[:500]}...\n```\n\n"
    
    # Review Summary
    if review := data.get("review"):
        output += "## Code Review\n\n"
        
        issues = review.get("issues", [])
        if issues:
            high = [i for i in issues if i.get("severity") == "high"]
            if high:
                output += f"⚠️  **{len(high)} high-severity issues found**\n\n"
            
            for issue in issues[:5]:  # Top 5
                sev = issue.get("severity", "unknown")
                desc = issue.get("description", "")
                output += f"- **[{sev.upper()}]** {desc}\n"
        else:
            output += "✅ No major issues detected\n"
    
    return output


# Rotas HTTP customizadas para comunicação entre agentes
async def tools_call_endpoint(request):
    """Endpoint para chamada de tools via HTTP simples"""
    try:
        try:
            data = await request.json()
        except Exception:
            body = await request.body()
            txt = body.decode("utf-8", errors="ignore")
            i = txt.find("{")
            if i > 0:
                txt = txt[i:]
            if txt.startswith("'") or txt.replace(" ", "").startswith("'{"):
                txt = txt.replace("'", '"')
            data = json.loads(txt)
        tool_name = data.get("tool_name")
        arguments = data.get("arguments", {})
        
        if tool_name == "communicate_with_agent":
            target_agent = arguments.get("target_agent")
            message = arguments.get("message")
            
            # Redireciona para o agente alvo
            agents = AgentClients()
            
            if target_agent == "architect":
                result = await agents.call_agent(agents.architect_url, "process_message", {"message": message})
            elif target_agent == "designer":
                result = await agents.call_agent(agents.designer_url, "process_message", {"message": message})
            elif target_agent == "coder":
                result = await agents.call_agent(agents.coder_url, "process_message", {"message": message})
            elif target_agent == "auditor":
                result = await agents.call_agent(agents.auditor_url, "process_message", {"message": message})
            elif target_agent == "stack-research":
                result = await agents.call_agent(agents.stack_url, "process_message", {"message": message})
            else:
                result = {"error": f"Unknown agent: {target_agent}"}
            
            return JSONResponse(result)
        
        # Se for uma tool específica de um agente, redireciona
        if tool_name in ["propose_architecture", "analyze_dependencies"]:
            agents = AgentClients()
            result = await agents.call_agent(agents.architect_url, tool_name, arguments)
            return JSONResponse({"result": result})
        elif tool_name in ["design_ui", "create_design_system"]:
            agents = AgentClients()
            result = await agents.call_agent(agents.designer_url, tool_name, arguments)
            return JSONResponse({"result": result})
        elif tool_name in ["generate_code", "generate_tests"]:
            agents = AgentClients()
            result = await agents.call_agent(agents.coder_url, tool_name, arguments)
            return JSONResponse({"result": result})
        elif tool_name in ["review_code", "audit_security"]:
            agents = AgentClients()
            result = await agents.call_agent(agents.auditor_url, tool_name, arguments)
            return JSONResponse({"result": result})
        elif tool_name in ["get_stack_snapshot", "research_library"]:
            agents = AgentClients()
            result = await agents.call_agent(agents.stack_url, tool_name, arguments)
            return JSONResponse({"result": result})
        
        result = await mcp.call_tool(tool_name, arguments)
        if isinstance(result, dict):
            return JSONResponse({"result": result})
        elif hasattr(result, "content"):
            content = result.content
            if hasattr(content, "text"):
                content = content.text
            return JSONResponse({"result": {"content": content}})
        else:
            try:
                if hasattr(result, "dict"):
                    return JSONResponse({"result": result.dict()})
                else:
                    return JSONResponse({"result": str(result)})
            except:
                return JSONResponse({"result": str(result)})
        
    except Exception as e:
        logger.error(f"Error in tools_call_endpoint: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)

async def health_endpoint(request):
    """Endpoint de health check"""
    return JSONResponse({"status": "healthy", "agent": "orchestrator"})
async def session_endpoint(request):
    return JSONResponse({"sessionId": f"session_{id(request)}"})

# Entrypoint para stdio (IDE)
if __name__ == "__main__":
    mcp.run(transport="stdio")
else:
    app = mcp.streamable_http_app()
    from starlette.routing import Route
    app.router.routes.append(Route("/health", health_endpoint, methods=["GET"]))
    app.router.routes.append(Route("/mcp/tools/call", tools_call_endpoint, methods=["POST"]))
    app.router.routes.append(Route("/mcp/session", session_endpoint, methods=["POST"]))
    async def quick_code_http(request):
        q = request.query_params
        desc = q.get("description", "hello")
        lang = q.get("language", "python")
        style = q.get("style", "modern")
        if q.get("stub") == "1" or q.get("use_stub") == "1":
            if lang == "python":
                res = "def main():\n    print('hello')\n\nif __name__ == '__main__':\n    main()"
            elif lang == "typescript":
                res = "export function sum(a:number,b:number){return a+b}"
            else:
                res = "function sum(a,b){return a+b}"
        else:
            res = await quick_code(desc, lang, style)
        return JSONResponse({"result": res})
    app.router.routes.append(Route("/mcp/tools/quick_code", quick_code_http, methods=["GET"]))
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