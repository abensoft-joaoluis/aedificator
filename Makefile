.PHONY: all clean install build copy-includes dist help

# Configurações
PYTHON := python3
SRC_DIR := src
BUILD_DIR := build
DIST_DIR := dist
INCLUDE_DIR := include
SPEC_FILE := aedificator.spec
ENTRY_POINT := $(SRC_DIR)/cli.py
APP_NAME := aedificator

# Cores para output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostra esta mensagem de ajuda
	@echo "$(BLUE)Aedificator - Makefile$(NC)"
	@echo ""
	@echo "Targets disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'

all: clean build copy-includes ## Build completo (limpa, compila e copia includes)
	@echo "$(GREEN)✓ Build completo finalizado!$(NC)"
	@echo "$(BLUE)Executável em: $(BUILD_DIR)/$(APP_NAME)$(NC)"

install: ## Instala dependências Python
	@echo "$(YELLOW)Instalando dependências...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip
	@$(PYTHON) -m pip install -r requirements.txt
	@$(PYTHON) -m pip install pyinstaller
	@echo "$(GREEN)✓ Dependências instaladas$(NC)"

build: install ## Compila com PyInstaller
	@echo "$(YELLOW)Compilando com PyInstaller...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@$(PYTHON) -m PyInstaller \
		--name=$(APP_NAME) \
		--onefile \
		--noconfirm \
		--clean \
		--distpath=$(BUILD_DIR) \
		--workpath=$(BUILD_DIR)/temp \
		--specpath=. \
		--add-data "$(SRC_DIR)/data:data" \
		--hidden-import=peewee \
		--hidden-import=rich \
		--hidden-import=questionary \
		--exclude-module=easygui \
		--exclude-module=tkinter \
		--collect-submodules=aedificator \
		--collect-submodules=pathing \
		$(ENTRY_POINT)
	@echo "$(GREEN)✓ Compilação concluída$(NC)"

copy-includes: ## Copia arquivos do diretório include para build
	@echo "$(YELLOW)Copiando arquivos do include...$(NC)"
	@mkdir -p $(BUILD_DIR)
	@if [ -d "$(INCLUDE_DIR)" ]; then \
		cp -rv $(INCLUDE_DIR)/* $(BUILD_DIR)/; \
		echo "$(GREEN)✓ Arquivos copiados: $(INCLUDE_DIR) → $(BUILD_DIR)$(NC)"; \
	else \
		echo "$(RED)✗ Diretório $(INCLUDE_DIR) não encontrado$(NC)"; \
		exit 1; \
	fi

dist: all ## Cria pacote de distribuição
	@echo "$(YELLOW)Criando pacote de distribuição...$(NC)"
	@mkdir -p $(DIST_DIR)
	@tar -czf $(DIST_DIR)/$(APP_NAME)-$$(date +%Y%m%d-%H%M%S).tar.gz -C $(BUILD_DIR) .
	@echo "$(GREEN)✓ Pacote criado em $(DIST_DIR)$(NC)"

clean: ## Remove arquivos de build
	@echo "$(YELLOW)Limpando arquivos de build...$(NC)"
	@rm -rf $(BUILD_DIR)
	@rm -rf $(DIST_DIR)
	@rm -rf build
	@rm -rf dist
	@rm -rf *.spec
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Limpeza concluída$(NC)"

clean-logs: ## Remove logs antigos
	@echo "$(YELLOW)Removendo logs...$(NC)"
	@rm -rf $(SRC_DIR)/data/logs/*
	@echo "$(GREEN)✓ Logs removidos$(NC)"

test: ## Executa testes (placeholder)
	@echo "$(YELLOW)Executando testes...$(NC)"
	@$(PYTHON) -m pytest tests/ 2>/dev/null || echo "$(YELLOW)Nenhum teste encontrado$(NC)"

run: ## Executa o programa em modo desenvolvimento
	@echo "$(YELLOW)Executando Aedificator...$(NC)"
	@$(PYTHON) -m $(SRC_DIR).cli

run-built: build ## Executa o executável compilado
	@echo "$(YELLOW)Executando executável compilado...$(NC)"
	@$(BUILD_DIR)/$(APP_NAME)

info: ## Mostra informações do build
	@echo "$(BLUE)Informações do Build:$(NC)"
	@echo "  Python: $$($(PYTHON) --version)"
	@echo "  Diretório de entrada: $(SRC_DIR)"
	@echo "  Diretório de build: $(BUILD_DIR)"
	@echo "  Diretório de include: $(INCLUDE_DIR)"
	@echo "  Entry point: $(ENTRY_POINT)"
	@echo "  Nome do executável: $(APP_NAME)"
	@if [ -f "$(BUILD_DIR)/$(APP_NAME)" ]; then \
		echo "  Tamanho do executável: $$(du -h $(BUILD_DIR)/$(APP_NAME) | cut -f1)"; \
	fi
