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

mcp = FastMCP("AuditorAgent")
router = LLMRouter()

@mcp.tool()
async def review_code(
    code: dict,
    context: dict = None
) -> dict:
    """
    Realiza code review completo com foco em qualidade, padrões e best practices.
    
    Args:
        code: Código a ser revisado (backend e frontend)
        context: Contexto adicional (spec, arquitetura, etc.)
    
    Returns:
        Análise completa com issues, métricas e sugestões
    """
    
    schema = {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                        "type": {"type": "string", "enum": ["security", "performance", "style", "bug", "maintainability"]},
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "description": {"type": "string"},
                        "suggestion": {"type": "string"},
                        "rule": {"type": "string"}
                    },
                    "required": ["severity", "type", "description"]
                }
            },
            "metrics": {
                "type": "object",
                "properties": {
                    "complexity": {"type": "number"},
                    "test_coverage": {"type": "number"},
                    "security_score": {"type": "number"},
                    "maintainability_index": {"type": "number"},
                    "code_smells": {"type": "integer"}
                }
            },
            "corrected_code": {"type": "object"},
            "recommendations": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["issues", "metrics", "recommendations"]
    }
    
    prompt = f"""
    Você é um auditor de código sênior especializado em segurança, performance e qualidade.
    
    Tarefa: Realizar uma revisão completa do seguinte código:
    
    Código: {json.dumps(code, indent=2)}
    Contexto: {json.dumps(context, indent=2) if context else 'Nenhum contexto adicional'}
    
    Analise:
    1. Segurança: Vulnerabilidades (SQL injection, XSS, auth issues)
    2. Performance: Bottlenecks, otimizações faltando
    3. Estilo: Conformidade com padrões, code smells
    4. Bugs: Lógica incorreta, edge cases não tratados
    5. Manutenibilidade: Complexidade, duplicação, documentação
    
    Forneça:
    - Issues detalhadas com severidade, tipo, localização
    - Métricas de qualidade (complexidade, cobertura, etc.)
    - Código corrigido para issues críticas
    - Recomendações gerais
    
    Retorne um JSON válido seguindo exatamente este schema:
    {schema}
    """
    
    result_text = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em code review, segurança e qualidade de software."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"issues": [], "metrics": {}, "corrected_code": {}, "recommendations": []}

@mcp.tool()
async def security_scan(
    code: dict
) -> dict:
    """
    Foco exclusivo em vulnerabilidades de segurança.
    
    Args:
        code: Código a ser escaneado
    
    Returns:
        Vulnerabilidades encontradas e fixes recomendados
    """
    
    schema = {
        "type": "object",
        "properties": {
            "vulnerabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "description": {"type": "string"},
                        "owasp_category": {"type": "string"},
                        "fix": {"type": "string"},
                        "cve_reference": {"type": "string"}
                    }
                }
            },
            "security_score": {"type": "number"},
            "critical_count": {"type": "integer"},
            "recommendations": {"type": "array", "items": {"type": "string"}}
        }
    }
    
    prompt = f"""
    Realize uma análise de segurança profunda no seguinte código:
    
    {json.dumps(code, indent=2)}
    
    Foque em:
    1. OWASP Top 10 vulnerabilidades
    2. Injection attacks (SQL, NoSQL, Command, LDAP)
    3. Authentication & Authorization flaws
    4. Sensitive data exposure
    5. XXE, SSRF, CSRF
    6. Insecure deserialization
    7. Using components with known vulnerabilities
    
    Forneça:
    - Lista detalhada de vulnerabilidades
    - Fixes específicos para cada issue
    - Score de segurança (0-10)
    - Recomendações de hardening
    
    Retorne um JSON válido seguindo exatamente este schema:
    {schema}
    """
    
    result_text = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em segurança de aplicações e OWASP."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"vulnerabilities": [], "security_score": 0, "critical_count": 0, "recommendations": []}

@mcp.tool()
async def validate_imports(
    code: dict,
    expected_versions: dict
) -> dict:
    """
    Valida imports e versões de bibliotecas.
    
    Args:
        code: Código com imports
        expected_versions: Versões esperadas das bibliotecas
    
    Returns:
        Validação de imports e recomendações de atualização
    """
    
    schema = {
        "type": "object",
        "properties": {
            "validation_results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "library": {"type": "string"},
                        "current_version": {"type": "string"},
                        "expected_version": {"type": "string"},
                        "status": {"type": "string", "enum": ["ok", "outdated", "deprecated", "vulnerable"]},
                        "recommendation": {"type": "string"},
                        "migration_notes": {"type": "string"}
                    }
                }
            },
            "deprecated_apis": {"type": "array", "items": {"type": "string"}},
            "security_alerts": {"type": "array", "items": {"type": "string"}},
            "update_priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
        }
    }
    
    prompt = f"""
    Valide os imports e versões de bibliotecas no seguinte código:
    
    Código: {json.dumps(code, indent=2)}
    Versões esperadas: {json.dumps(expected_versions, indent=2)}
    
    Verifique:
    1. Versões estão de acordo com as esperadas
    2. APIs depreciadas não estão sendo usadas
    3. Bibliotecas com vulnerabilidades conhecidas
    4. Melhores práticas de imports
    5. Compatibilidade entre bibliotecas
    
    Retorne um JSON válido seguindo exatamente este schema:
    {schema}
    """
    
    result_text = await router.call_glm46(
        messages=[
            Message(role="system", content="Você é um especialista em gestão de dependências e versionamento."),
            Message(role="user", content=prompt)
        ],
        temperature=0.1
    )
    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        return {"validation_results": [], "deprecated_apis": [], "security_alerts": [], "update_priority": "low"}

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
    return JSONResponse({"status": "healthy", "service": "auditor-agent"})

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