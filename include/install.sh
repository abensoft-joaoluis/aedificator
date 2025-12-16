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

# Detecta gerenciador de pacotes
PKG_MANAGER=""
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
elif command -v brew &> /dev/null; then
    PKG_MANAGER="brew"
fi

if [ -n "$PKG_MANAGER" ]; then
    print_success "Gerenciador de pacotes detectado: $PKG_MANAGER"
fi

# Verifica Python (opcional, para modo desenvolvimento)
HAS_PYTHON=false
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python encontrado: $PYTHON_VERSION"
    HAS_PYTHON=true
else
    print_warning "Python 3 não encontrado"
fi

# Pergunta o tipo de instalação
echo ""
print_info "Escolha o tipo de instalação:"
echo "  1) Executável standalone (recomendado - sem dependências)"
echo "  2) Modo desenvolvimento (com Python e venv)"
read -p "Escolha [1/2]: " INSTALL_MODE

if [ "$INSTALL_MODE" = "2" ]; then
    # Modo desenvolvimento - instala Python e dependências
    if [ "$HAS_PYTHON" = false ]; then
        print_error "Python 3 é necessário para modo desenvolvimento"

        if [ -n "$PKG_MANAGER" ]; then
            print_info "Deseja instalar Python 3? [s/N]"
            read -p "" INSTALL_PYTHON

            if [[ "$INSTALL_PYTHON" =~ ^[Ss]$ ]]; then
                case "$PKG_MANAGER" in
                    apt)
                        sudo apt-get update
                        sudo apt-get install -y python3 python3-pip python3-venv
                        ;;
                    dnf|yum)
                        sudo $PKG_MANAGER install -y python3 python3-pip
                        ;;
                    pacman)
                        sudo pacman -S --noconfirm python python-pip
                        ;;
                    brew)
                        brew install python3
                        ;;
                esac
                print_success "Python instalado"
                HAS_PYTHON=true
            else
                print_error "Python é necessário para modo desenvolvimento"
                exit 1
            fi
        else
            print_error "Não foi possível detectar gerenciador de pacotes"
            print_info "Instale Python 3 manualmente e execute novamente"
            exit 1
        fi
    fi

    # Cria venv
    VENV_DIR="$HOME/.local/share/aedificator/venv"
    print_info "Criando ambiente virtual em $VENV_DIR..."
    mkdir -p "$(dirname "$VENV_DIR")"
    python3 -m venv "$VENV_DIR"
    print_success "Ambiente virtual criado"

    # Ativa venv e instala dependências
    source "$VENV_DIR/bin/activate"

    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_info "Instalando dependências Python..."
        pip install --upgrade pip
        pip install -r "$PROJECT_ROOT/requirements.txt"
        print_success "Dependências instaladas"
    else
        print_warning "Arquivo requirements.txt não encontrado"
    fi

    deactivate

    # Cria wrapper script
    WRAPPER_SCRIPT="$HOME/.local/bin/aedificator-dev"
    mkdir -p "$HOME/.local/bin"

    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash
# Aedificator Development Wrapper
source "$VENV_DIR/bin/activate"
python3 "$PROJECT_ROOT/src/cli.py" "\$@"
deactivate
EOF

    chmod +x "$WRAPPER_SCRIPT"
    print_success "Wrapper de desenvolvimento criado: $WRAPPER_SCRIPT"

    INSTALL_DIR="$HOME/.local/bin"
    EXECUTABLE_NAME="aedificator-dev"
else
    # Modo standalone - apenas copia executável
    echo ""
    print_info "Escolha o local de instalação:"
    echo "  1) Sistema (/usr/local/bin) - requer sudo"
    echo "  2) Usuário (~/.local/bin) - sem sudo (recomendado)"
    echo "  3) Diretório específico"
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

    EXECUTABLE_NAME="aedificator"
fi

# Cria diretório de dados
DATA_DIR="$HOME/.local/share/aedificator"
print_info "Criando diretório de dados em $DATA_DIR..."
mkdir -p "$DATA_DIR/logs"
mkdir -p "$DATA_DIR/data"
print_success "Diretório de dados criado"

# Verifica se o diretório está no PATH
if [ "$INSTALL_MODE" != "2" ]; then
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        print_warning "O diretório $INSTALL_DIR não está no PATH"

        # Detecta o shell
        SHELL_RC=""
        if [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_RC="$HOME/.bashrc"
        elif [ -f "$HOME/.zshrc" ]; then
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
fi

# Cria script de desinstalação
UNINSTALL_DIR="$HOME/.local/share/aedificator"
UNINSTALL_SCRIPT="$UNINSTALL_DIR/uninstall.sh"
mkdir -p "$UNINSTALL_DIR"

cat > "$UNINSTALL_SCRIPT" << EOF
#!/bin/bash
echo "Desinstalando Aedificator..."

# Remove executável
if [ -f "$INSTALL_DIR/$EXECUTABLE_NAME" ]; then
    ${SUDO:-} rm -f "$INSTALL_DIR/$EXECUTABLE_NAME"
    echo "Executável removido: $INSTALL_DIR/$EXECUTABLE_NAME"
fi

# Remove venv (se existir)
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Ambiente virtual removido: $VENV_DIR"
fi

# Pergunta se quer remover dados
read -p "Deseja remover dados e logs? [s/N] " REMOVE_DATA
if [[ "\$REMOVE_DATA" =~ ^[Ss]$ ]]; then
    rm -rf "$DATA_DIR"
    echo "Dados removidos: $DATA_DIR"
fi

# Remove este script
rm -f "\$0"
echo "Aedificator desinstalado com sucesso"
EOF

chmod +x "$UNINSTALL_SCRIPT"
print_success "Script de desinstalação criado em $UNINSTALL_SCRIPT"

# Resumo
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════╗"
echo "║   Instalação Concluída com Sucesso!   ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo ""

if [ "$INSTALL_MODE" = "2" ]; then
    print_info "Modo: Desenvolvimento (Python + venv)"
    print_info "Para executar: $EXECUTABLE_NAME"
    print_info "Venv: $VENV_DIR"
else
    print_info "Modo: Standalone (executável)"
    print_info "Para executar: $EXECUTABLE_NAME"
fi

print_info "Para desinstalar: bash $UNINSTALL_SCRIPT"
print_info "Diretório de dados: $DATA_DIR"
echo ""

# Teste opcional
if [ "$INSTALL_MODE" != "2" ]; then
    print_info "Deseja testar a instalação agora? [s/N]"
    read -p "" TEST_NOW
    if [[ "$TEST_NOW" =~ ^[Ss]$ ]]; then
        print_info "Testando executável..."
        if "$INSTALL_DIR/$EXECUTABLE_NAME" --version 2>/dev/null; then
            print_success "Teste bem-sucedido!"
        else
            print_info "Executando Aedificator..."
            "$INSTALL_DIR/$EXECUTABLE_NAME" || true
        fi
    fi
fi

exit 0
