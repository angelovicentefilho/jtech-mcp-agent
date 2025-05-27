.PHONY: venv install install-dev test lint clean build publish

PYTHON := python3
VENV := .venv
PIP := $(VENV)/bin/pip
POETRY := poetry
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

# Cores para saída no terminal
GREEN=\033[0;32m
YELLOW=\033[0;33m
BLUE=\033[0;34m
RED=\033[0;31m
NC=\033[0m # No Color

help:
	@echo "$(BLUE)Makefile para jtech-mcp-executor$(NC)"
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  $(YELLOW)make venv$(NC)       - Cria ambiente virtual e instala Poetry"
	@echo "  $(YELLOW)make install$(NC)    - Instala o pacote (somente dependências de produção)"
	@echo "  $(YELLOW)make install-dev$(NC) - Instala o pacote em modo editável com dependências de desenvolvimento"
	@echo "  $(YELLOW)make test$(NC)       - Executa testes unitários"
	@echo "  $(YELLOW)make lint$(NC)       - Executa verificação de linting com Ruff"
	@echo "  $(YELLOW)make clean$(NC)      - Remove arquivos temporários e diretórios de build"
	@echo "  $(YELLOW)make build$(NC)      - Constrói o pacote para distribuição"
	@echo "  $(YELLOW)make publish$(NC)    - Publica o pacote no PyPI"

venv:
	@if [ -d "$(VENV)" ]; then \
		read -p "$(YELLOW)Ambiente virtual já existe. Deseja recriá-lo? [s/N]$(NC) " answer; \
		if [ "$$answer" = "s" ] || [ "$$answer" = "S" ]; then \
			echo "$(RED)Removendo ambiente virtual existente...$(NC)"; \
			rm -rf $(VENV); \
			echo "$(GREEN)Criando novo ambiente virtual...$(NC)"; \
			$(PYTHON) -m venv $(VENV); \
			$(PIP) install --upgrade pip; \
			echo "$(GREEN)Ambiente virtual recriado com sucesso. Ative-o com: source $(VENV)/bin/activate$(NC)"; \
		else \
			echo "$(BLUE)Mantendo ambiente virtual existente.$(NC)"; \
		fi; \
	else \
		echo "$(GREEN)Criando ambiente virtual...$(NC)"; \
		$(PYTHON) -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
		echo "$(GREEN)Ambiente virtual criado com sucesso. Ative-o com: source $(VENV)/bin/activate$(NC)"; \
	fi
	@# Verificar se o Poetry está instalado globalmente
	@if ! command -v poetry &> /dev/null; then \
		echo "$(YELLOW)Poetry não encontrado. Instalando globalmente...$(NC)"; \
		curl -sSL https://install.python-poetry.org | $(PYTHON) -; \
		echo "$(GREEN)Poetry instalado globalmente.$(NC)"; \
	else \
		echo "$(BLUE)Poetry já está instalado.$(NC)"; \
	fi

install: venv
	@echo "$(GREEN)Instalando jtech-mcp-executor...$(NC)"
	@$(POETRY) install --without dev
	@echo "$(GREEN)Instalação concluída.$(NC)"

install-dev: venv
	@echo "$(GREEN)Instalando jtech-mcp-executor com dependências de desenvolvimento...$(NC)"
	@$(POETRY) install
	@echo "$(GREEN)Instalando em modo editável...$(NC)"
	@$(PIP) install -e .
	@echo "$(GREEN)Instalação de desenvolvimento concluída.$(NC)"

test: install-dev
	@echo "$(GREEN)Executando testes...$(NC)"
	@./tests/run_tests.sh
	@echo "$(GREEN)Testes concluídos.$(NC)"

lint: install-dev
	@echo "$(GREEN)Executando linting...$(NC)"
	@$(RUFF) check .
	@echo "$(GREEN)Linting concluído.$(NC)"

clean:
	@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name "*.egg" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name ".ruff_cache" -exec rm -rf {} +
	@echo "$(GREEN)Limpeza concluída.$(NC)"

build: clean install
	@echo "$(GREEN)Iniciando processo de build...$(NC)"
	@# Ler a versão atual do projeto
	@current_version=$$($(POETRY) version -s); \
	echo "$(BLUE)Versão atual: $$current_version$(NC)"; \
	echo ""; \
	echo "$(YELLOW)Opções de versionamento:$(NC)"; \
	echo "  1) Patch (correção de bugs) - incrementa o último número"; \
	echo "  2) Minor (recursos novos, compatível) - incrementa o número do meio"; \
	echo "  3) Major (mudanças incompatíveis) - incrementa o primeiro número"; \
	echo "  4) Inserir versão manualmente"; \
	echo "  5) Manter a versão atual ($$current_version)"; \
	echo ""; \
	read -p "$(YELLOW)Escolha uma opção (1-5) ou pressione ENTER para manter a versão atual:$(NC) " version_choice; \
	echo ""; \
	case "$$version_choice" in \
		1) new_version=$$($(POETRY) version patch -s); echo "$(GREEN)Versão atualizada para: $$new_version$(NC)";; \
		2) new_version=$$($(POETRY) version minor -s); echo "$(GREEN)Versão atualizada para: $$new_version$(NC)";; \
		3) new_version=$$($(POETRY) version major -s); echo "$(GREEN)Versão atualizada para: $$new_version$(NC)";; \
		4) read -p "$(YELLOW)Insira a nova versão (formato: x.y.z):$(NC) " custom_version; \
		   if [ -n "$$custom_version" ]; then \
		       new_version=$$($(POETRY) version "$$custom_version" -s); \
		       echo "$(GREEN)Versão atualizada para: $$new_version$(NC)"; \
		   else \
		       echo "$(RED)Nenhuma versão fornecida. Mantendo versão atual: $$current_version$(NC)"; \
		   fi;; \
		5|"") echo "$(BLUE)Mantendo versão atual: $$current_version$(NC)";; \
		*) echo "$(RED)Opção inválida. Mantendo versão atual: $$current_version$(NC)";; \
	esac; \
	echo ""
	@echo "$(GREEN)Construindo pacote para distribuição...$(NC)"
	@$(POETRY) build
	@echo "$(GREEN)Build concluído. Os artefatos estão no diretório dist/$(NC)"

publish: build
	@echo "$(YELLOW)Publicando pacote no PyPI...$(NC)"
	@echo "$(YELLOW)Certifique-se de que você está logado no Poetry (poetry config pypi-token.pypi <token>)$(NC)"
	@$(POETRY) publish
	@echo "$(GREEN)Publicação concluída.$(NC)"

publish-test: build
	@echo "$(YELLOW)Publicando pacote no TestPyPI...$(NC)"
	@echo "$(YELLOW)Certifique-se de que você está logado no Poetry (poetry config repositories.testpypi https://test.pypi.org/legacy/ && poetry config pypi-token.testpypi <token>)$(NC)"
	@$(POETRY) publish -r testpypi
	@echo "$(GREEN)Publicação no TestPyPI concluída.$(NC)"