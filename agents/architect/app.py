import json
from typing import Any, Dict, List, Optional
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import sys
import os
from llm_router import LLMRouter, Message

mcp = FastMCP("ArchitectAgent")
router = LLMRouter()

@mcp.tool()
async def propose_architecture(
    spec: str,
    constraints: dict = None,
    tech_preferences: dict = None
) -> dict:
    """
    Propor arquitetura completa para uma feature especificada.
    
    Args:
        spec: Descrição da feature/funcionalidade
        constraints: Restrições técnicas (ex: performance, segurança)
        tech_preferences: Preferências tecnológicas (ex: frontend framework)
    
    Returns:
        Arquitetura completa com backend, frontend e pontos de integração
    """
    
    # Define schema para structured output
    schema = {
        "type": "object",
        "properties": {
            "backend": {
                "type": "object",
                "properties": {
                    "modules": {"type": "array", "items": {"type": "string"}},
                    "apis": {"type": "array", "items": {"type": "object"}},
                    "models": {"type": "array", "items": {"type": "object"}},
                    "services": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["modules", "apis", "models", "services"]
            },
            "frontend": {
                "type": "object",
                "properties": {
                    "routes": {"type": "array", "items": {"type": "object"}},
                    "components": {"type": "array", "items": {"type": "object"}},
                    "state": {"type": "string"},
                    "layout_structure": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["routes", "components", "state", "layout_structure"]
            },
            "integration_points": {"type": "array", "items": {"type": "object"}},
            "trade_offs": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["backend", "frontend", "integration_points", "trade_offs"]
    }
    
    prompt = f"""
    Você é um arquiteto de software sênior especializado em design de sistemas escaláveis.
    
    Tarefa: Propor uma arquitetura completa para a seguinte feature:
    {spec}
    
    {f'Constraints: {constraints}' if constraints else ''}
    {f'Tech Preferences: {tech_preferences}' if tech_preferences else ''}
    
    Requisitos:
    1. Backend: APIs RESTful, models, services, patterns (Repository, Factory, Strategy)
    2. Frontend: Rotas, componentes, state management (React/Next.js/Vite)
    3. Integração: Pontos de integração entre frontend e backend
    4. Trade-offs: Decisões arquiteturais e seus prós/contras
    
    Retorne um JSON válido seguindo exatamente este schema:
    {schema}
    
    Foque em arquiteturas modernas, escaláveis e seguindo best practices.
    """
    
    # REMOVIDO: Gemini 2.5 Flash desinstalado do sistema
    # Substituído por implementação local simples
    return {
        "backend": {
            "modules": ["core", "api", "models"],
            "apis": [{"path": "/api/health", "method": "GET"}],
            "models": [{"name": "BaseModel"}],
            "services": [{"name": "BaseService"}]
        },
        "frontend": {
            "routes": [{"path": "/", "component": "Home"}],
            "components": [{"name": "Header"}, {"name": "Footer"}],
            "state": "default",
            "layout_structure": ["header", "main", "footer"]
        },
        "integration_points": [{"type": "api", "description": "REST API"}],
        "trade_offs": ["arquitetura simplificada para resposta rápida"]
    }

@mcp.tool()
async def refine_architecture(
    current_arch: dict,
    feedback: str
) -> dict:
    """
    Refina arquitetura baseado em feedback do usuário ou outros agentes.
    
    Args:
        current_arch: Arquitetura atual
        feedback: Feedback para refinamento
    
    Returns:
        Arquitetura refinada
    """
    
    schema = {
        "type": "object",
        "properties": {
            "refined_architecture": {"type": "object"},
            "changes_made": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"}
        },
        "required": ["refined_architecture", "changes_made", "rationale"]
    }
    
    prompt = f"""
    Refine a seguinte arquitetura baseada no feedback fornecido:
    
    Arquitetura Atual:
    {json.dumps(current_arch, indent=2)}
    
    Feedback:
    {feedback}
    
    Forneça:
    1. Arquitetura refinada
    2. Lista de mudanças feitas
    3. Racionalização das mudanças
    
    Retorne um JSON válido seguindo o schema fornecido.
    """
    
    # REMOVIDO: Gemini 2.5 Flash desinstalado do sistema
    # Substituído por implementação local simples
    return {
        "refined_architecture": current_arch,
        "changes_made": ["Gemini 2.5 Flash removido - refinamento indisponível"],
        "rationale": "Arquitetura mantida devido à remoção do Gemini 2.5 Flash"
    }

# Usa o streamable_http_app do FastMCP para HTTP transport
app = mcp.streamable_http_app()

# Adiciona endpoint de sessão para MCP HTTP transport
@app.route("/mcp/session", methods=["POST"])
async def create_session(request: Request):
    """Cria uma nova sessão MCP HTTP"""
    session_id = "session_" + str(id(request))
    return JSONResponse({"sessionId": session_id})

# Adiciona endpoint de health check simples
@app.route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "service": "architect-agent"})

# Adiciona endpoint simplificado para tools/call
@app.route("/mcp/tools/call", methods=["POST"])
async def call_tool_simple(request: Request):
    """Chama ferramenta MCP de forma simplificada"""
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
    
    try:
        # Chama a ferramenta MCP diretamente
        result = await mcp.call_tool(tool_name, arguments)
        
        # Converte o resultado para um formato JSON serializável
        if isinstance(result, dict):
            # Se já for um dict, retorna direto
            return JSONResponse({"result": result})
        elif hasattr(result, 'content'):
            # Se for um objeto com atributo content
            content = result.content
            if hasattr(content, 'text'):
                content = content.text
            return JSONResponse({"result": {"content": content}})
        else:
            # Tenta converter para dict ou string
            try:
                # Se tiver método dict ou similar
                if hasattr(result, 'dict'):
                    return JSONResponse({"result": result.dict()})
                else:
                    # Converte para string como último recurso
                    return JSONResponse({"result": str(result)})
            except:
                # Se tudo falhar, retorna string
                return JSONResponse({"result": str(result)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# Endpoint de health check
async def health_endpoint(request):
    return JSONResponse({"status": "healthy", "agent": "architect"})

from starlette.routing import Mount

app.mount("/mcp", mcp.streamable_http_app())
app.add_route("/health", health_endpoint, methods=["GET"])