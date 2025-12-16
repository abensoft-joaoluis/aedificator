# Aedificator - Build e Instalação

Guia completo para compilar e instalar o Aedificator usando PyInstaller.

## 📋 Pré-requisitos

### Para Build
- Python 3.10+
- pip
- make

### Para Instalação (Modo Standalone)
- Nenhuma dependência necessária - executável standalone

### Para Instalação (Modo Desenvolvimento)
- Python 3.10+
- pip
- venv

## 🔨 Build

### Build Completo

```bash
make all
```

Este comando executa:
1. Limpa builds anteriores
2. Instala dependências Python (peewee, rich, questionary)
3. Instala PyInstaller
4. Compila o executável standalone
5. Copia arquivos de `include/` para `build/`

### Outros Comandos Make

```bash
make help              # Mostra todos os comandos disponíveis
make clean             # Remove arquivos de build
make build             # Apenas compila (sem limpar)
make install           # Apenas instala dependências
make copy-includes     # Apenas copia arquivos do include/
make dist              # Cria pacote tar.gz para distribuição
make run               # Executa em modo desenvolvimento
make run-built         # Executa o executável compilado
make info              # Mostra informações do build
```

### Estrutura do Build

Após executar `make all`, você terá:

```
build/
├── aedificator    # Executável standalone (~18MB)
├── install.sh     # Script de instalação
└── temp/          # Arquivos temporários do PyInstaller
```

## 📦 Instalação

### Opção 1: Instalação Standalone (Recomendado)

Executável sem dependências externas.

```bash
cd build/
./install.sh
```

Escolha a opção `1` quando solicitado.

O instalador perguntará:
1. **Local de instalação:**
   - `/usr/local/bin` (sistema - requer sudo)
   - `~/.local/bin` (usuário - recomendado)
   - Diretório customizado

2. **Adicionar ao PATH:** Atualiza automaticamente seu `.bashrc` ou `.zshrc`

3. **Teste:** Opção de testar o executável imediatamente

**Diretórios criados:**
- `~/.local/bin/aedificator` - Executável
- `~/.local/share/aedificator/data/` - Banco de dados
- `~/.local/share/aedificator/logs/` - Logs de execução

### Opção 2: Instalação em Modo Desenvolvimento

Com ambiente virtual Python e dependências.

```bash
cd build/
./install.sh
```

Escolha a opção `2` quando solicitado.

O instalador:
1. Verifica Python 3
2. Oferece instalar Python se não estiver disponível (via apt/dnf/pacman/brew)
3. Cria venv em `~/.local/share/aedificator/venv`
4. Instala dependências do `requirements.txt`
5. Cria wrapper script `aedificator-dev`

**Uso:**
```bash
aedificator-dev
```

## 🗑️ Desinstalação

O instalador cria automaticamente um script de desinstalação:

```bash
bash ~/.local/share/aedificator/uninstall.sh
```

O script remove:
- Executável instalado
- Ambiente virtual (se existir)
- Opcionalmente: dados e logs

## 🔧 Configuração do PyInstaller

O Makefile usa as seguintes configurações:

```makefile
--onefile                      # Executável único
--noconfirm                    # Sem confirmações
--clean                        # Limpa cache antes de compilar
--add-data "src/data:data"     # Inclui diretório de dados
--hidden-import=peewee         # Inclui ORM SQLite
--hidden-import=rich           # Inclui formatação de terminal
--hidden-import=questionary    # Inclui menus interativos
--exclude-module=easygui       # Exclui easygui (não usado)
--exclude-module=tkinter       # Exclui tkinter (não usado)
--collect-submodules=aedificator  # Coleta todos os submódulos
--collect-submodules=pathing      # Coleta módulo de paths
```

## 📊 Informações Técnicas

### Tamanho do Executável
- **Standalone:** ~18MB
- Inclui: Python runtime + bibliotecas + código da aplicação

### Dependências Runtime
- Nenhuma! O executável é completamente standalone
- SQLite incluído no Python runtime
- Todas as bibliotecas estão empacotadas

### Compatibilidade
- **Linux:** Testado em Arch, Ubuntu, Fedora
- **macOS:** Suporte via build nativo
- **Windows:** Suporte via WSL ou build nativo

## 🐛 Troubleshooting

### Erro: "Executável não encontrado"

Execute `make all` no diretório raiz do projeto primeiro:
```bash
cd /path/to/Aedificator
make all
```

### Erro: "Permission denied"

Torne o executável executável:
```bash
chmod +x build/aedificator
chmod +x build/install.sh
```

### Erro: "Python não encontrado" (Modo Dev)

Instale Python 3:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3 python3-pip python3-venv
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip
```

**Arch:**
```bash
sudo pacman -S python python-pip
```

**macOS:**
```bash
brew install python3
```

### Erro durante o build: "Module not found"

Certifique-se de que todas as dependências estão instaladas:
```bash
make install
```

### Executável não está no PATH

Opção 1: Adicione manualmente ao `.bashrc` ou `.zshrc`:
```bash
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

Opção 2: Execute o instalador novamente e aceite adicionar ao PATH.

### Build muito lento

O PyInstaller pode levar 1-2 minutos na primeira execução. Builds subsequentes são mais rápidos devido ao cache.

## 🚀 Criando Distribuição

Para criar um pacote tar.gz para distribuição:

```bash
make dist
```

Isso cria `dist/aedificator-YYYYMMDD-HHMMSS.tar.gz` contendo:
- Executável standalone
- Script de instalação
- Tudo necessário para instalação em outra máquina

**Distribuir:**
```bash
# Envie o arquivo tar.gz
scp dist/aedificator-*.tar.gz user@server:/tmp/

# No servidor de destino:
cd /tmp
tar -xzf aedificator-*.tar.gz
./install.sh
```

## 📝 Notas

- O executável é específico para a arquitetura em que foi compilado (Linux x86_64)
- Para outras arquiteturas, compile no sistema alvo
- O banco de dados SQLite é criado automaticamente no primeiro uso
- Logs são salvos em `~/.local/share/aedificator/logs/`

## 🔄 Workflow de Desenvolvimento

1. **Fazer mudanças no código:**
   ```bash
   vim src/aedificator/main.py
   ```

2. **Testar em modo desenvolvimento:**
   ```bash
   make run
   ```

3. **Build e testar executável:**
   ```bash
   make all
   make run-built
   ```

4. **Criar distribuição:**
   ```bash
   make dist
   ```

5. **Limpar arquivos temporários:**
   ```bash
   make clean
   ```

## 📚 Referências

- [PyInstaller Documentação](https://pyinstaller.org/en/stable/)
- [Python venv](https://docs.python.org/3/library/venv.html)
- [Makefile Tutorial](https://makefiletutorial.com/)
