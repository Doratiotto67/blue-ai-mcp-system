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

mcp = FastMCP("DesignerAgent")
router = LLMRouter()

@mcp.tool()
async def design_ui(
    spec: str,
    architecture: dict | None = None,
    ux_goals: list = None
) -> dict:
    """
    Design de interface de usuário completa baseada na especificação e arquitetura.
    
    Args:
        spec: Especificação da feature
        architecture: Arquitetura proposta pelo Architect Agent
        ux_goals: Objetivos de UX (responsive, accessible, modern, etc.)
    
    Returns:
        Design completo com telas, hierarquia de componentes e tokens de design
    """
    
    schema = {
        "type": "object",
        "properties": {
            "screens": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "layout": {"type": "string"},
                        "components": {"type": "array", "items": {"type": "string"}},
                        "animations": {"type": "array", "items": {"type": "string"}},
                        "description": {"type": "string"}
                    },
                    "required": ["name", "layout", "components"]
                }
            },
            "component_hierarchy": {"type": "object"},
            "design_tokens": {
                "type": "object",
                "properties": {
                    "colors": {"type": "object"},
                    "spacing": {"type": "object"},
                    "typography": {"type": "object"},
                    "shadows": {"type": "object"}
                }
            },
            "accessibility_notes": {"type": "array", "items": {"type": "string"}},
            "responsive_breakpoints": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["screens", "component_hierarchy", "design_tokens"]
    }
    
    prompt = f"""
    Você é um designer de UI/UX especializado em interfaces modernas e acessíveis.
    
    Tarefa: Criar um design completo de interface para:
    
    Especificação: {spec}
    Arquitetura: {json.dumps(architecture or {}, indent=2)}
    Objetivos de UX: {ux_goals or ['responsive', 'accessible', 'modern']}
    
    Requisitos:
    1. Telas: Lista de telas com layout, componentes e animações
    2. Hierarquia: Estrutura de componentes (átomos → moléculas → organismos)
    3. Design Tokens: Cores, espaçamentos, tipografia, sombras
    4. Acessibilidade: Notas sobre ARIA, navegação por teclado, contraste
    5. Responsividade: Breakpoints e comportamentos adaptativos
    
    Use Tailwind CSS e shadcn/ui como base. Foque em design moderno e limpo.
    Retorne um JSON válido seguindo exatamente este schema:
    {schema}
    """
    
    result_text = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em design de interfaces modernas, acessíveis e responsivas."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {
            "screens": [],
            "component_hierarchy": {},
            "design_tokens": {},
            "accessibility_notes": [],
            "responsive_breakpoints": []
        }

@mcp.tool()
async def generate_component(
    component_spec: dict,
    design_system: str = "shadcn"
) -> str:
    """
    Gera código React/TSX para um componente específico.
    
    Args:
        component_spec: Especificação do componente
        design_system: Sistema de design (shadcn, chakra, material)
    
    Returns:
        Código React/TSX do componente
    """
    
    prompt = f"""
    Gere um componente React/TypeScript seguindo esta especificação:
    
    {json.dumps(component_spec, indent=2)}
    
    Use {design_system} como sistema de design.
    Inclua:
    - Props tipadas com TypeScript
    - Estados internos se necessário
    - Handlers de eventos
    - Estilos com Tailwind CSS
    - Comentários explicativos
    - Acessibilidade (ARIA labels, etc.)
    
    Retorne apenas o código do componente, sem imports externos.
    """
    
    code = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em React/TypeScript e component design."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    
    return code.strip()

@mcp.tool()
async def create_design_system(
    brand_guidelines: dict = None
) -> dict:
    """
    Cria um design system completo baseado em diretrizes da marca.
    
    Args:
        brand_guidelines: Diretrizes de marca (cores, fontes, etc.)
    
    Returns:
        Design system com tokens, componentes e padrões
    """
    
    schema = {
        "type": "object",
        "properties": {
            "colors": {
                "type": "object",
                "properties": {
                    "primary": {"type": "string"},
                    "secondary": {"type": "string"},
                    "accent": {"type": "string"},
                    "neutral": {"type": "object"},
                    "semantic": {"type": "object"}
                }
            },
            "typography": {
                "type": "object",
                "properties": {
                    "font_families": {"type": "object"},
                    "font_sizes": {"type": "object"},
                    "font_weights": {"type": "object"},
                    "line_heights": {"type": "object"}
                }
            },
            "spacing": {"type": "object"},
            "shadows": {"type": "object"},
            "border_radius": {"type": "object"},
            "animations": {"type": "object"}
        }
    }
    
    prompt = f"""
    Crie um design system completo para uma aplicação moderna.
    
    {f'Diretrizes de marca: {json.dumps(brand_guidelines, indent=2)}' if brand_guidelines else ''}
    
    Inclua:
    1. Cores: Paleta completa com primary, secondary, accent, neutrals
    2. Tipografia: Famílias de fontes, tamanhos, pesos, alturas de linha
    3. Espaçamentos: Sistema de espaçamento consistente
    4. Sombras: Shadows para diferentes elevações
    5. Border Radius: Para diferentes componentes
    6. Animações: Transições e animações padrão
    
    Use Tailwind CSS como base e extenda conforme necessário.
    Retorne um JSON válido seguindo o schema fornecido.
    """
    
    result_text = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em design systems e design tokens."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {
            "colors": {},
            "typography": {},
            "spacing": {},
            "shadows": {},
            "border_radius": {},
            "animations": {}
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
    return JSONResponse({"status": "healthy", "service": "designer-agent"})

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