# 📋 MCP Configuration Documentation

## 🚀 Blue AI Enterprise - Multi-Agent MCP Configuration

This document provides comprehensive configuration details for the Blue AI Enterprise Multi-Agent MCP (Microservice Control Plane) system.

---

## 📁 Files Overview

- **`mcp-configuration.json`** - Main configuration file with all system settings
- **`.env`** - Environment variables for sensitive data
- **`docker-compose.yml`** - Docker orchestration file

---

## 🔧 Quick Setup Guide

### 1. Environment Variables Setup

Create a `.env` file in the project root with the following variables:

```bash
# Docker Configuration
DOCKER_HOST=localhost
DOCKER_PORT=2376
DOCKER_TLS_VERIFY=1

# Agent Authentication Tokens
ORCHESTRATOR_TOKEN=your_orchestrator_token_here
ARCHITECT_TOKEN=your_architect_token_here
DESIGNER_TOKEN=your_designer_token_here
CODER_TOKEN=your_coder_token_here
AUDITOR_TOKEN=your_auditor_token_here
RESEARCH_TOKEN=your_research_token_here

# Agent Passwords
ORCHESTRATOR_PASSWORD=secure_password_1
ARCHITECT_PASSWORD=secure_password_2
DESIGNER_PASSWORD=secure_password_3
CODER_PASSWORD=secure_password_4
AUDITOR_PASSWORD=secure_password_5
RESEARCH_PASSWORD=secure_password_6

# Backend Integration
BACKEND_API_URL=https://api.yourdomain.com
BACKEND_AUTH_TOKEN=your_backend_token_here

# LLM API Keys
OPENROUTER_API_KEY=your_openrouter_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

### 2. Docker Configuration

#### Required Docker Settings:
- **API Version**: 1.45+ (compatible with Docker 28.x)
- **TLS Verification**: Enabled for production
- **Certificate Path**: `~/.docker/certs`

#### Container Labels:
```yaml
labels:
  - "mcp.system=blue-ai-enterprise"
  - "mcp.version=1.0.0"
  - "mcp.environment=production"
```

### 3. Network Configuration

#### Port Mapping:
- **Orchestrator**: 9080 → 8080
- **Architect**: 9081 → 8080
- **Designer**: 9082 → 8080
- **Coder**: 9083 → 8080
- **Auditor**: 9084 → 8080
- **Stack Research**: 9085 → 8080

#### Internal Communication:
- All agents communicate via Docker network `agentesaii_blue_agents`
- HTTP endpoints accessible at `http://localhost:908X/health`
- MCP endpoints at `http://localhost:908X/mcp`

---

## 🧪 Testing Procedures

### Health Check Tests

#### Test Individual Agents:
```powershell
# PowerShell
curl -s http://localhost:9080/health
Invoke-RestMethod -Uri "http://localhost:9080/health" -Method Get
```

#### Test All Agents:
```powershell
# Quick health check script
$ports = 9080..9085
$agents = @("orchestrator", "architect", "designer", "coder", "auditor", "research")

for ($i = 0; $i -lt $ports.Count; $i++) {
    $health = Invoke-RestMethod -Uri "http://localhost:$($ports[$i])/health" -Method Get
    Write-Host "$($agents[$i]): $($health.status)"
}
```

### Inter-Agent Communication Tests

#### Test Tool Execution:
```powershell
# Test architect tool
Invoke-RestMethod -Uri "http://localhost:9080/mcp/tools/call" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"tool_name": "propose_architecture","arguments": {"spec": "Authentication system"}}'
```

#### Test Agent-to-Agent Communication:
```powershell
# Test orchestrator calling other agents
Invoke-RestMethod -Uri "http://localhost:9080/mcp/tools/call" -Method Post `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"tool_name": "communicate_with_agent","arguments": {"target_agent": "architect","message": "Test message"}}'
```

### Backend Integration Tests

#### API Connectivity:
```powershell
# Test backend connection
Invoke-RestMethod -Uri "$env:BACKEND_API_URL/api/health" -Method Get `
  -Headers @{"Authorization"="Bearer $env:BACKEND_AUTH_TOKEN"}
```

#### Data Synchronization:
```powershell
# Test agent registration
Invoke-RestMethod -Uri "$env:BACKEND_API_URL/api/agents" -Method Post `
  -Headers @{"Authorization"="Bearer $env:BACKEND_AUTH_TOKEN"} `
  -Body '{"agent_id": "test-agent", "endpoint": "http://localhost:9080"}'
```

---

## 🔍 Troubleshooting Guide

### Common Issues

#### 1. Connection Refused Errors
**Symptoms**: `curl: (7) Failed to connect to localhost port 908X`
**Solutions**:
- Check if containers are running: `docker ps`
- Verify port mappings: `docker port <container_name>`
- Check firewall settings
- Ensure Docker daemon is running

#### 2. Authentication Failures
**Symptoms**: `401 Unauthorized` or `403 Forbidden`
**Solutions**:
- Verify tokens in `.env` file
- Check token expiration settings
- Ensure correct auth headers
- Review security settings in config

#### 3. Health Check Failures
**Symptoms**: `{"status": "unhealthy"}`
**Solutions**:
- Check container logs: `docker logs <container_name>`
- Verify health check endpoints
- Review timeout settings
- Check resource constraints

#### 4. Inter-Agent Communication Issues
**Symptoms**: `500 Internal Server Error`
**Solutions**:
- Verify network connectivity between containers
- Check Docker network configuration
- Review agent endpoint URLs
- Ensure proper error handling

### Log Analysis

#### View Container Logs:
```powershell
# Recent logs
docker logs <container_name> --tail 50

# Follow logs in real-time
docker logs -f <container_name>

# Filter by error level
docker logs <container_name> 2>&1 | Select-String "ERROR"
```

#### Enable Debug Logging:
```json
{
  "logging": {
    "level": "DEBUG",
    "format": "json"
  }
}
```

---

## 🔒 Security Best Practices

### Authentication
- Use strong, unique tokens for each agent
- Implement token rotation (default: 1 hour)
- Enable multi-factor authentication where possible
- Store credentials securely (environment variables)

### Network Security
- Enable TLS for all communications
- Use certificate validation
- Implement proper CORS policies
- Restrict allowed origins

### Data Protection
- Encrypt sensitive data at rest
- Use secure key storage
- Implement proper audit logging
- Mask sensitive fields in logs

---

## 📊 Performance Optimization

### Resource Limits
```yaml
# Docker Compose resource limits
resources:
  limits:
    cpus: '1.0'
    memory: 1G
  reservations:
    cpus: '0.5'
    memory: 512M
```

### Caching Strategy
- Enable response caching (TTL: 300s)
- Implement connection pooling
- Use efficient data structures
- Monitor cache hit rates

### Scaling Considerations
- Horizontal scaling for agents
- Load balancing across instances
- Database connection pooling
- Async processing for heavy tasks

---

## 🔄 Maintenance Procedures

### Regular Tasks
- Monitor health check responses
- Review logs for anomalies
- Update security tokens
- Check resource usage

### Updates and Upgrades
- Backup current configuration
- Test in staging environment
- Rolling updates for zero downtime
- Verify compatibility after updates

### Backup and Recovery
- Export configuration regularly
- Test recovery procedures
- Maintain rollback capabilities
- Document disaster recovery plans

---

## 📞 Support and Resources

### Documentation
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Docker API Reference](https://docs.docker.com/engine/api/)
- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk)

### Contact Information
- **Maintainer**: DevOps Team
- **Support**: support@blue-ai.enterprise
- **Documentation**: https://docs.blue-ai.enterprise/mcp

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Share experiences and best practices
- Updates: Follow for latest releases and security patches

---

## 🎯 Quick Reference

### Essential Commands:
```powershell
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart specific agent
docker-compose restart orchestrator
```

### Configuration Files:
- Main config: `mcp-configuration.json`
- Environment: `.env`
- Docker: `docker-compose.yml`
- Agent configs: `agents/*/config.json`

---

*Last updated: 2024-01-01*
*Version: 1.0.0*