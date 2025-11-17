# 🚀 Blue AI Multi-Agent MCP System

Sistema multi-agente enterprise baseado em MCP (Model Context Protocol) com orquestração inteligente usando GLM-4.6 + Gemini 2.5 Flash.

## 📋 Visão Geral

Esta arquitetura implementa um sistema distribuído de agentes especializados que trabalham em conjunto para:
- ✅ Analisar requisitos e propor arquiteturas
- ✅ Design de interfaces modernas e responsivas  
- ✅ Gerar código limpo e seguindo best practices
- ✅ Auditar código para segurança e qualidade
- ✅ Research de stacks e dependências atualizadas

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────┐
│                    IDE/Client (stdio MCP)                        │
│                    (Claude/Cursor/VS Code)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ stdio
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BLUE ORCHESTRATOR (Container)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  LLM Router: GLM-4.6 (reasoning) + Gemini 2.5 (struct)  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MCP Client (HttpTransport) → Internal Agent Network    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/MCP
          ┌──────────────────┼──────────────────┬─────────────────┐
          │                  │                  │                 │
          ▼                  ▼                  ▼                 ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐
│ Architect Agent  │ │ Designer/UIX │ │ Coder Agent  │ │ Auditor Agent   │
│  (MCP Server)    │ │ Agent (MCP)  │ │  (MCP Server)│ │  (MCP Server)   │
└──────────────────┘ └──────────────┘ └──────────────┘ └─────────────────┘
          │                  │                  │                 │
          └──────────────────┴──────────────────┴─────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │StackResearch Agent (MCP)│
                      │  Gemini 2.5 Flash Core  │
                      └─────────────────────────┘
```

## 🧠 Dual-LLM Strategy

| Tarefa | Modelo Primário | Modelo Secundário | Justificativa |
|--------|----------------|-------------------|---------------|
| Orquestração & Planning | GLM-4.6 | Gemini (summary) | Reasoning complexo + tool calling |
| Codegen Backend/Frontend | GLM-4.6 | - | Superior code quality |
| Auditoria de Código | GLM-4.6 | Gemini (JSON output) | Deep analysis + structured report |
| Research de Stack | Gemini 2.5 Flash | - | Structured outputs + speed |
| Arquitetura de Sistema | GLM-4.6 | Gemini (normalize) | Reasoning + JSON schema |
| UI/UX Design | GLM-4.6 | Gemini (multimodal) | Code + interpret mockups |
| Import/Version Mapping | Gemini 2.5 Flash | - | Fast + structured |

## 🚀 Instalação Rápida

### 1. Clone e Configure

```bash
git clone <repository>
cd blue-ai-mcp-system
cp .env.example .env
# Edite .env com suas API keys
```

### 2. Configure as API Keys

```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_key_here
GEMINI_API_KEY=your_gemini_key_here
LOG_LEVEL=INFO
```

### 3. Build e Inicie

```bash
# Build das imagens Docker
docker-compose build

# Inicie o sistema
docker-compose up -d

# Verifique os logs
docker-compose logs -f
```

### 4. Configure sua IDE

#### Claude Desktop
```bash
# Copie a configuração para o Claude Desktop
cp config/claude-desktop-mcp.json ~/.config/claude-desktop/mcp_config.json
# Ou manualmente adicione ao arquivo existente
```

#### Cursor
```bash
# Copie a configuração para o Cursor
cp config/cursor-mcp.json ~/.cursor/mcp.json
# Ou manualmente adicione ao arquivo existente
```

#### VS Code
```bash
# Instale a extensão MCP Server
# Copie a configuração para as settings do VS Code
cp config/vscode-mcp.json ~/.vscode/settings.json
# Ou manualmente adicione ao arquivo existente
```

## 🛠️ Agentes Disponíveis

### Orchestrator Agent
- **Função**: Coordenação do pipeline completo
- **Porta**: 8080
- **Tools**: `build_feature`, `quick_code`, `research_stack`

### Architect Agent  
- **Função**: Design de arquitetura backend/frontend
- **Porta**: 8081
- **Tools**: `propose_architecture`, `refine_architecture`

### Designer/UIX Agent
- **Função**: Design de interfaces e UX
- **Porta**: 8082
- **Tools**: `design_ui`, `generate_component`, `create_design_system`

### Coder Agent
- **Função**: Geração de código limpo
- **Porta**: 8083
- **Tools**: `generate_code`, `refactor_code`, `generate_tests`

### Auditor Agent
- **Função**: Revisão de código e segurança
- **Porta**: 8084
- **Tools**: `review_code`, `security_scan`, `validate_imports`

### StackResearch Agent
- **Função**: Research de tecnologias e dependências
- **Porta**: 8085
- **Tools**: `get_imports`, `get_stack_snapshot`, `search_best_practice`

## 💻 Uso

### Via IDE (Claude/Cursor/VS Code)

Simplesmente pergunte ao assistente:

```
Use o blue-orchestrator para criar uma aplicação de e-commerce com React e FastAPI
```

### Via API HTTP

```bash
# Teste individual de agentes
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "build_feature",
      "arguments": {
        "spec": "Criar um sistema de autenticação com JWT",
        "context": "Usar FastAPI backend e React frontend"
      }
    }
  }'
```

### Docker Compose

```bash
# Ver status dos containers
docker-compose ps

# Ver logs específicos
docker-compose logs orchestrator
docker-compose logs coder-agent

# Restartar serviço específico
docker-compose restart architect-agent

# Parar tudo
docker-compose down
```

## 📊 Monitoramento

### Health Checks
- Todos os agentes expõem endpoint `/health`
- Docker Compose inclui healthchecks automáticos
- Logs centralizados em `./logs/`

### Métricas
- Tempo de resposta por agente
- Taxa de sucesso das ferramentas
- Uso de tokens por LLM

## 🔧 Desenvolvimento

### Adicionar Novo Agente

1. Crie diretório em `agents/nome-agente/`
2. Implemente `app.py` com tools MCP
3. Crie `Dockerfile.nome-agente` em `docker/`
4. Adicione ao `docker-compose.yml`
5. Configure health checks

### Testes

```bash
# Teste unitário de um agente
cd agents/coder
python -m pytest tests/

# Teste de integração
cd tests/integration
python test_pipeline.py
```

## 🔐 Segurança

- **API Keys**: Nunca commite chaves reais
- **Network Isolation**: Agentes em network Docker isolada
- **Non-root Containers**: Executam como usuário não-root
- **Health Checks**: Monitoramento contínuo de disponibilidade
- **Input Validation**: Validação de entrada em todas as tools

## 📈 Escalabilidade

### Horizontal Scaling
```yaml
# Adicione no docker-compose.yml
coder-agent:
  deploy:
    replicas: 3
```

### Resource Limits
```yaml
# Já configurado no docker-compose.yml
resources:
  limits:
    memory: 512M
  reservations:
    memory: 256M
```

## 🐛 Troubleshooting

### Problemas Comuns

1. **Container não inicia**: Verifique logs com `docker-compose logs [service]`
2. **MCP não conecta**: Confirme network Docker e portas
3. **API Key inválida**: Verifique `.env` e permissões
4. **Timeout em tools**: Ajuste timeouts em `LLMRouter`

### Debug Mode
```bash
# Ative debug logs
export LOG_LEVEL=DEBUG
docker-compose up -d
```

## 📚 Documentação Adicional

- [MCP Protocol](https://modelcontextprotocol.io/)
- [GLM-4.6 Docs](https://openrouter.ai/)
- [Gemini 2.5 Flash](https://ai.google.dev/)
- [FastMCP](https://github.com/jlowin/fastmcp)

## 🤝 Contribuindo

1. Fork o projeto
2. Crie feature branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add nova funcionalidade'`)
4. Push para branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

- Issues: [GitHub Issues](https://github.com/seu-repo/issues)
- Discussions: [GitHub Discussions](https://github.com/seu-repo/discussions)
- Email: suporte@blueai.com

---

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!**