#!/bin/bash

# Arquivo: run_tests.sh
# Descrição: Script para executar os testes unitários do projeto jtech-mcp-executor
# Uso: ./run_tests.sh [módulo específico]

# Cores para saída no terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "======================================================"
echo "         JTECH-MCP-EXECUTOR - TESTES UNITÁRIOS        "
echo "======================================================"
echo -e "${NC}"

# Diretório raiz do projeto
PROJECT_ROOT=$(dirname "$(dirname "$(readlink -f "$0")")")
cd "$PROJECT_ROOT" || exit 1

# Verifica se o Poetry está instalado
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}Poetry não encontrado. Por favor, instale-o com:${NC}"
    echo -e "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Função para executar os testes
run_tests() {
    if [ -n "$1" ]; then
        echo -e "${YELLOW}Executando testes do módulo: ${BLUE}$1${NC}\n"
        poetry run python -m pytest tests/unit/$1 -v
    else
        echo -e "${YELLOW}Executando todos os testes unitários${NC}\n"
        poetry run python -m pytest tests/unit/ -v
    fi
}

# Função para mostrar cobertura de código
run_coverage() {
    echo -e "\n${YELLOW}Gerando relatório de cobertura de código${NC}\n"
    poetry run python -m pytest tests/unit/ --cov=jtech_mcp_executor --cov-report=term
}

# Verifica se um módulo específico foi informado
if [ $# -eq 1 ]; then
    TEST_MODULE="$1"
    
    # Verifica se o arquivo existe
    if [ -f "tests/unit/$TEST_MODULE" ] || [ -d "tests/unit/$TEST_MODULE" ]; then
        run_tests "$TEST_MODULE"
    else
        echo -e "${RED}Módulo de teste não encontrado: $TEST_MODULE${NC}"
        echo -e "Módulos disponíveis:"
        ls -1 tests/unit/*.py | xargs -n 1 basename
        exit 1
    fi
else
    # Executa todos os testes
    run_tests
    
    # Gera relatório de cobertura
    if command -v pytest-cov &> /dev/null; then
        run_coverage
    else
        echo -e "\n${YELLOW}Para ver a cobertura de código, instale o pytest-cov:${NC}"
        echo -e "poetry add pytest-cov --group dev"
    fi
fi

echo -e "\n${GREEN}Testes concluídos!${NC}"