# 🚀 Blue AI Multi-Agent MCP System

Enterprise multi-agent system based on MCP (Model Context Protocol) with intelligent orchestration using GLM-4.6.

## 📋 Overview

This architecture implements a distributed system of specialized agents that work together to:
- ✅ Analyze requirements and propose architectures
- ✅ Design modern and responsive interfaces  
- ✅ Generate clean code following best practices
- ✅ Audit code for security and quality
- ✅ Research updated stacks and dependencies

## 🏗️ Architecture

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
│  │  LLM Router: GLM-4.6 (Reasoning & Structured Output)    │  │
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
┌──────────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────────┐ ┌──────────────┐
│ Architect Agent  │ │ Designer/UIX │ │ Coder Agent  │ │ Auditor Agent   │ │ Memory Agent │
│  (MCP Server)    │ │ Agent (MCP)  │ │  (MCP Server)│ │  (MCP Server)   │ │  (MCP Server)│
└──────────────────┘ └──────────────┘ └──────────────┘ └─────────────────┘ └──────────────┘
          │                  │                  │                 │
          └──────────────────┴──────────────────┴─────────────────┘
                                   │
                                   ▼
                      ┌─────────────────────────┐
                      │StackResearch Agent (MCP)│
                      └─────────────────────────┘
```

## 🚀 Quick Install

### 1. Clone and Configure

```bash
git clone <repository>
cd blue-ai-mcp-system
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure API Keys

```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_key_here
LOG_LEVEL=INFO
```

### 3. Build and Start

```bash
# Build the Docker images
docker-compose build

# Start the system
docker-compose up -d

# Check the logs
docker-compose logs -f
```

### 4. Configure Your IDE

#### Claude Desktop
```bash
# Copy the configuration to Claude Desktop
cp config/claude-desktop-mcp.json ~/.config/claude-desktop/mcp_config.json
# Or manually add to the existing file
```

#### Cursor
```bash
# Copy the configuration to Cursor
cp config/cursor-mcp.json ~/.cursor/mcp.json
# Or manually add to the existing file
```

#### VS Code
```bash
# Install the MCP Server extension
# Copy the configuration to VS Code settings
cp config/vscode-mcp.json ~/.vscode/settings.json
# Or manually add to the existing file
```

## 🛠️ Available Agents

### Orchestrator Agent
- **Function**: Full pipeline coordination
- **Port**: 9080
- **Tools**: `build_feature`, `quick_code`, `research_stack`

### Architect Agent  
- **Function**: Backend/frontend architecture design
- **Port**: 9081
- **Tools**: `propose_architecture`, `refine_architecture`

### Designer/UIX Agent
- **Function**: UI and UX design
- **Port**: 9082
- **Tools**: `design_ui`, `generate_component`, `create_design_system`

### Coder Agent
- **Function**: Clean code generation
- **Port**: 9083
- **Tools**: `generate_code`, `refactor_code`, `generate_tests`

### Auditor Agent
- **Function**: Code review and security
- **Port**: 9084
- **Tools**: `review_code`, `security_scan`, `validate_imports`

### StackResearch Agent
- **Function**: Technology and dependency research
- **Port**: 9085
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