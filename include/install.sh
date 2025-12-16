#!/bin/bash

# Aedificator - Script de Instalação
# Este script instala o Aedificator e suas dependências

set -e  # Sai em caso de erro

# Cores
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funções auxiliares
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║       Aedificator - Instalador       ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Verifica se está sendo executado do diretório correto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_info "Diretório do projeto: $PROJECT_ROOT"
print_info "Diretório do script: $SCRIPT_DIR"

# Verifica se o executável existe
if [ ! -f "$SCRIPT_DIR/aedificator" ]; then
    print_error "Executável 'aedificator' não encontrado em $SCRIPT_DIR"
    print_info "Execute 'make all' no diretório raiz do projeto primeiro"
    exit 1
fi

# Detecta o sistema operacional
OS="$(uname -s)"
case "$OS" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="Mac";;
    CYGWIN*)    PLATFORM="Cygwin";;
    MINGW*)     PLATFORM="MinGw";;
    *)          PLATFORM="UNKNOWN:${OS}"
esac

print_info "Sistema detectado: $PLATFORM"

# Verifica Python (opcional, caso queira rodar em modo desenvolvimento)
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python encontrado: $PYTHON_VERSION"
    HAS_PYTHON=true
else
    print_warning "Python 3 não encontrado (não necessário para executável)"
    HAS_PYTHON=false
fi

# Pergunta onde instalar
echo ""
print_info "Escolha o tipo de instalação:"
echo "  1) Sistema (/usr/local/bin) - requer sudo"
echo "  2) Usuário (~/.local/bin) - sem sudo"
echo "  3) Apenas copiar para diretório específico"
read -p "Escolha [1/2/3]: " INSTALL_TYPE

case $INSTALL_TYPE in
    1)
        INSTALL_DIR="/usr/local/bin"
        if [ "$EUID" -ne 0 ]; then
            print_warning "Instalação no sistema requer privilégios de root"
            SUDO="sudo"
        else
            SUDO=""
        fi
        ;;
    2)
        INSTALL_DIR="$HOME/.local/bin"
        SUDO=""
        mkdir -p "$INSTALL_DIR"
        ;;
    3)
        read -p "Digite o caminho completo do diretório: " CUSTOM_DIR
        INSTALL_DIR="$CUSTOM_DIR"
        SUDO=""
        mkdir -p "$INSTALL_DIR"
        ;;
    *)
        print_error "Opção inválida"
        exit 1
        ;;
esac

# Instala o executável
print_info "Copiando executável para $INSTALL_DIR..."
$SUDO cp "$SCRIPT_DIR/aedificator" "$INSTALL_DIR/"
$SUDO chmod +x "$INSTALL_DIR/aedificator"
print_success "Executável instalado em $INSTALL_DIR/aedificator"

# Cria diretório de dados se não existir
DATA_DIR="$HOME/.local/share/aedificator"
print_info "Criando diretório de dados em $DATA_DIR..."
mkdir -p "$DATA_DIR/logs"
print_success "Diretório de dados criado"

# Verifica se o diretório está no PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    print_warning "O diretório $INSTALL_DIR não está no PATH"

    # Detecta o shell
    SHELL_RC=""
    if [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        print_info "Deseja adicionar $INSTALL_DIR ao PATH em $SHELL_RC? [s/N]"
        read -p "" ADD_PATH
        if [[ "$ADD_PATH" =~ ^[Ss]$ ]]; then
            echo "" >> "$SHELL_RC"
            echo "# Aedificator" >> "$SHELL_RC"
            echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
            print_success "PATH atualizado em $SHELL_RC"
            print_warning "Execute 'source $SHELL_RC' ou reinicie o terminal"
        fi
    fi
fi

# Instalação de dependências opcionais (para desenvolvimento)
if [ "$HAS_PYTHON" = true ]; then
    echo ""
    print_info "Deseja instalar dependências Python para desenvolvimento? [s/N]"
    read -p "" INSTALL_DEPS
    if [[ "$INSTALL_DEPS" =~ ^[Ss]$ ]]; then
        if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
            print_info "Instalando dependências..."
            python3 -m pip install --user -r "$PROJECT_ROOT/requirements.txt"
            print_success "Dependências instaladas"
        else
            print_warning "Arquivo requirements.txt não encontrado"
        fi
    fi
fi

# Cria link simbólico para desinstalação fácil
UNINSTALL_SCRIPT="$INSTALL_DIR/uninstall-aedificator.sh"
print_info "Criando script de desinstalação..."
cat > /tmp/uninstall-aedificator.sh << 'EOF'
#!/bin/bash
echo "Desinstalando Aedificator..."
rm -f "$0/../aedificator"
echo "Aedificator desinstalado com sucesso"
rm -f "$0"
EOF
$SUDO mv /tmp/uninstall-aedificator.sh "$UNINSTALL_SCRIPT"
$SUDO chmod +x "$UNINSTALL_SCRIPT"
print_success "Script de desinstalação criado em $UNINSTALL_SCRIPT"

# Resumo
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════╗"
echo "║     Instalação Concluída com Sucesso! ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo ""
print_info "Para executar: aedificator"
print_info "Para desinstalar: $UNINSTALL_SCRIPT"
print_info "Diretório de dados: $DATA_DIR"
echo ""

# Teste opcional
print_info "Deseja testar a instalação agora? [s/N]"
read -p "" TEST_NOW
if [[ "$TEST_NOW" =~ ^[Ss]$ ]]; then
    print_info "Executando aedificator..."
    "$INSTALL_DIR/aedificator" --help 2>/dev/null || "$INSTALL_DIR/aedificator" || true
fi

exit 0
