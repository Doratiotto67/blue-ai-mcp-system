# Blue AI Multi-Agent MCP System - Build Script (PowerShell)

Write-Host "🚀 Blue AI Multi-Agent MCP System - Build Script" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Function to print colored output
function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if Docker is installed
function Check-Docker {
    try {
        $dockerVersion = docker --version
        Write-Info "Docker está instalado: $dockerVersion"
        
        $dockerComposeVersion = docker-compose --version
        Write-Info "Docker Compose está instalado: $dockerComposeVersion"
    }
    catch {
        Write-Error "Docker ou Docker Compose não está instalado. Por favor, instale primeiro."
        exit 1
    }
}

# Check environment file
function Check-Env {
    if (-not (Test-Path .env)) {
        Write-Warning "Arquivo .env não encontrado. Copiando de .env.example..."
        Copy-Item .env.example .env
        Write-Warning "Por favor, edite o arquivo .env com suas API keys antes de continuar."
        exit 1
    }
    
    # Check if API keys are set
    $envContent = Get-Content .env -Raw
    if ($envContent -match "your_openrouter_api_key_here") {
        Write-Error "OPENROUTER_API_KEY não está configurada no arquivo .env"
        exit 1
    }
    
    
    
    Write-Info "Arquivo .env configurado corretamente ✓"
}

# Build base image
function Build-BaseImage {
    Write-Info "Construindo imagem base..."
    docker build -f docker/Dockerfile.base -t myorg/mcp-base:py312 .
    Write-Info "Imagem base construída com sucesso ✓"
}

# Build all agent images
function Build-AgentImages {
    Write-Info "Construindo imagens dos agentes..."
    
    $agents = @("orchestrator", "architect", "designer", "coder", "auditor", "stack-research")
    
    foreach ($agent in $agents) {
        Write-Info "Construindo $agent-agent..."
        docker build -f docker/Dockerfile.$agent -t myorg/mcp-$agent:latest .
    }
    
    Write-Info "Todas as imagens dos agentes construídas com sucesso ✓"
}

# Start the system
function Start-System {
    Write-Info "Iniciando o sistema Blue AI..."
    docker-compose up -d
    Write-Info "Sistema iniciado com sucesso! ✓"
}

# Check system health
function Check-Health {
    Write-Info "Verificando saúde do sistema..."
    
    # Wait a bit for services to start
    Start-Sleep -Seconds 10
    
    # Check each service
    $services = @("orchestrator", "architect-agent", "designer-agent", "coder-agent", "auditor-agent", "stack-research-agent")
    
    foreach ($service in $services) {
        $result = docker-compose ps | Select-String "$service.*Up"
        if ($result) {
            Write-Info "$service está rodando ✓"
        } else {
            Write-Error "$service não está rodando ✗"
        }
    }
}

# Show logs
function Show-Logs {
    Write-Info "Mostrando logs do orchestrator (pressione Ctrl+C para sair):"
    docker-compose logs -f orchestrator
}

# Main menu
function Show-MainMenu {
    Write-Host ""
    Write-Host "O que você gostaria de fazer?"
    Write-Host "1) Construir tudo (base + agentes)"
    Write-Host "2) Construir apenas imagem base"
    Write-Host "3) Construir apenas agentes"
    Write-Host "4) Iniciar sistema"
    Write-Host "5) Verificar saúde"
    Write-Host "6) Ver logs"
    Write-Host "7) Sair"
    Write-Host ""
    
    $choice = Read-Host "Escolha uma opção (1-7)"
    
    switch ($choice) {
        "1" {
            Check-Docker
            Check-Env
            Build-BaseImage
            Build-AgentImages
            Write-Info "Construção completa! Use 'docker-compose up -d' para iniciar."
        }
        "2" {
            Check-Docker
            Build-BaseImage
        }
        "3" {
            Check-Docker
            Build-AgentImages
        }
        "4" {
            Check-Docker
            Check-Env
            Start-System
            Check-Health
        }
        "5" {
            Check-Health
        }
        "6" {
            Show-Logs
        }
        "7" {
            Write-Host "Saindo..."
            exit 0
        }
        default {
            Write-Error "Opção inválida. Por favor, escolha 1-7."
            Show-MainMenu
        }
    }
}

# Check if running with arguments
if ($args.Count -eq 0) {
    Show-MainMenu
} else {
    switch ($args[0]) {
        "build-all" {
            Check-Docker
            Check-Env
            Build-BaseImage
            Build-AgentImages
        }
        "build-base" {
            Check-Docker
            Build-BaseImage
        }
        "build-agents" {
            Check-Docker
            Build-AgentImages
        }
        "start" {
            Check-Docker
            Check-Env
            Start-System
            Check-Health
        }
        "health" {
            Check-Health
        }
        "logs" {
            Show-Logs
        }
        default {
            Write-Host "Uso: .\build.ps1 [build-all|build-base|build-agents|start|health|logs]"
            exit 1
        }
    }
}