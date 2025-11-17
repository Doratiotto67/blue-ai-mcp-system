#!/bin/bash

# Blue AI Multi-Agent MCP System - Build Script

set -e

echo "🚀 Blue AI Multi-Agent MCP System - Build Script"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado. Por favor, instale Docker primeiro."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose não está instalado. Por favor, instale Docker Compose primeiro."
        exit 1
    fi
    
    print_status "Docker e Docker Compose estão instalados ✓"
}

# Check environment file
check_env() {
    if [ ! -f .env ]; then
        print_warning "Arquivo .env não encontrado. Copiando de .env.example..."
        cp .env.example .env
        print_warning "Por favor, edite o arquivo .env com suas API keys antes de continuar."
        exit 1
    fi
    
    # Check if API keys are set
    if grep -q "your_openrouter_api_key_here" .env; then
        print_error "OPENROUTER_API_KEY não está configurada no arquivo .env"
        exit 1
    fi
    
    
    
    print_status "Arquivo .env configurado corretamente ✓"
}

# Build base image
build_base_image() {
    print_status "Construindo imagem base..."
    docker build -f docker/Dockerfile.base -t myorg/mcp-base:py312 .
    print_status "Imagem base construída com sucesso ✓"
}

# Build all agent images
build_agent_images() {
    print_status "Construindo imagens dos agentes..."
    
    agents=("orchestrator" "architect" "designer" "coder" "auditor" "stack-research")
    
    for agent in "${agents[@]}"; do
        print_status "Construindo $agent-agent..."
        docker build -f docker/Dockerfile.$agent -t myorg/mcp-$agent:latest .
    done
    
    print_status "Todas as imagens dos agentes construídas com sucesso ✓"
}

# Start the system
start_system() {
    print_status "Iniciando o sistema Blue AI..."
    docker-compose up -d
    print_status "Sistema iniciado com sucesso! ✓"
}

# Check system health
check_health() {
    print_status "Verificando saúde do sistema..."
    
    # Wait a bit for services to start
    sleep 10
    
    # Check each service
    services=("orchestrator" "architect-agent" "designer-agent" "coder-agent" "auditor-agent" "stack-research-agent")
    
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_status "$service está rodando ✓"
        else
            print_error "$agent não está rodando ✗"
        fi
    done
}

# Show logs
show_logs() {
    print_status "Mostrando logs do orchestrator (pressione Ctrl+C para sair):"
    docker-compose logs -f orchestrator
}

# Main menu
main_menu() {
    echo ""
    echo "O que você gostaria de fazer?"
    echo "1) Construir tudo (base + agentes)"
    echo "2) Construir apenas imagem base"
    echo "3) Construir apenas agentes"
    echo "4) Iniciar sistema"
    echo "5) Verificar saúde"
    echo "6) Ver logs"
    echo "7) Sair"
    echo ""
    
    read -p "Escolha uma opção (1-7): " choice
    
    case $choice in
        1)
            check_docker
            check_env
            build_base_image
            build_agent_images
            print_status "Construção completa! Use 'docker-compose up -d' para iniciar."
            ;;
        2)
            check_docker
            build_base_image
            ;;
        3)
            check_docker
            build_agent_images
            ;;
        4)
            check_docker
            check_env
            start_system
            check_health
            ;;
        5)
            check_health
            ;;
        6)
            show_logs
            ;;
        7)
            echo "Saindo..."
            exit 0
            ;;
        *)
            print_error "Opção inválida. Por favor, escolha 1-7."
            main_menu
            ;;
    esac
}

# Check if running with arguments
if [ $# -eq 0 ]; then
    main_menu
else
    case $1 in
        "build-all")
            check_docker
            check_env
            build_base_image
            build_agent_images
            ;;
        "build-base")
            check_docker
            build_base_image
            ;;
        "build-agents")
            check_docker
            build_agent_images
            ;;
        "start")
            check_docker
            check_env
            start_system
            check_health
            ;;
        "health")
            check_health
            ;;
        "logs")
            show_logs
            ;;
        *)
            echo "Uso: $0 [build-all|build-base|build-agents|start|health|logs]"
            exit 1
            ;;
    esac
fi