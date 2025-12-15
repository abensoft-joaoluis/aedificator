# Aedificator

Sistema de automação para gerenciar e executar múltiplos projetos (Superleme, SL Phoenix, e Extensão) com suporte a Docker e execução em tempo real.

## 🎯 O Que é e Por Que Existe

Aedificator é uma ferramenta de automação criada para resolver os desafios de desenvolver e manter múltiplos projetos simultaneamente, cada um com seu próprio stack tecnológico, configurações de banco de dados e requisitos de ambiente.

### O Problema: Complexidade no Desenvolvimento Multi-Projeto

#### Cenário Real

Imagine que você está desenvolvendo um ecossistema completo:
- Um aplicativo **Zotonic (Erlang)** rodando PostgreSQL 17 e Erlang 28
- Um backend **Phoenix (Elixir)** que usa Elixir 1.19.4 e Node.js 25 para assets
- Uma extensão browser com seu próprio build pipeline em Node.js

Cada projeto tem requisitos específicos e muitas vezes **incompatíveis** entre si. Você não pode simplesmente ter Erlang 25 e Erlang 28 instalados nativamente na mesma máquina sem ferramentas como `asdf` ou `mise`. Mesmo assim, trocar versões manualmente é tedioso e propenso a erros.

#### As Dores Diárias

**1. Conflitos de Versão**
- PostgreSQL 14 vs PostgreSQL 17 - drivers incompatíveis, schemas diferentes
- Erlang 25 vs Erlang 28 - APIs mudaram, bytecode incompatível
- Elixir 1.15 vs 1.19 - breaking changes em dependências
- Node.js 20 vs 25 - ECMAScript features e módulos

**Solução manual:** Instalar version managers (`asdf`, `nvm`, `mise`), criar profiles, trocar contextos constantemente. Esquecer de trocar? Horas debuggando erros estranhos.

**2. Navegação Entre Projetos**
```bash
# Workflow típico sem Aedificator:
cd ~/Projects/zotonic
asdf shell erlang 28
make clean && make
bin/zotonic debug

# Ctrl+C, novo terminal
cd ~/Projects/sl_phoenix
asdf shell elixir 1.19.4
mix deps.get
mix phx.server

# Ctrl+C, novo terminal
cd ~/Projects/extension
nvm use 25
npm run dev

# E agora tem 3 terminais abertos... qual é qual?
```

Gerenciar tudo isso manualmente é:
- ❌ **Propenso a erros** - Esquecer de trocar versões causa bugs sutis
- ❌ **Tedioso** - Navegar entre pastas, lembrar comandos exatos
- ❌ **Lento** - Configurar Docker manualmente a cada mudança de versão
- ❌ **Frustrante** - Logs perdidos quando terminal fecha, saída bufferizada não aparece em tempo real
- ❌ **Difícil de documentar** - Como explica para novo dev todos os passos?
- ❌ **Inconsistente** - Cada dev tem configurações diferentes na máquina

**3. Docker: Salvação ou Complicação?**

Docker resolve conflitos de versão isolando ambientes. Mas traz novos desafios:

- **Configuração verbosa**: Cada `docker-compose.yml` tem dezenas de linhas
- **Versões hardcoded**: Quer mudar PostgreSQL 16→17? Edite YAML manualmente em 5 lugares
- **Comandos longos**: `docker compose run --rm --service-ports -w /opt/zotonic zotonic bin/zotonic debug`
- **Debugging difícil**: Saída bufferizada, logs desaparecem quando container morre
- **Volumes e permissões**: `_build` com owner errado? `EACCES` errors em cascata

**4. Trabalho em Equipe**

Quando múltiplos desenvolvedores trabalham nos mesmos projetos:
- "Na minha máquina funciona" - mas qual versão você está usando?
- Onboarding lento - novo dev leva dias configurando ambiente
- Documentação desatualizada - README diz PostgreSQL 14, projeto já usa 17
- Inconsistências - cada um tem docker-compose.yml ligeiramente diferente

### A Solução: Aedificator

Aedificator transforma o caos em ordem com uma interface unificada e automação inteligente.

#### Benefícios Principais

**1. ⚙️ Configuração Inteligente de Versões**

**O problema que resolve:**
Você tem que lembrar qual versão cada projeto usa e atualizar manualmente os arquivos Docker toda vez que muda.

**Como o Aedificator resolve:**
- Configure **uma única vez** as versões no menu interativo
- Sistema salva em banco de dados SQLite local
- **Antes de cada execução**, atualiza automaticamente `docker-compose.yml` com as versões corretas
- Regex inteligente encontra e substitui versões: `postgres:16.2-alpine` → `postgres:17-alpine`

**Exemplo prático:**
```bash
# Você: Configura PostgreSQL 17-alpine no menu
# Aedificator: Salva no banco de dados

# Você: Executa "Superleme → Executar"
# Aedificator (automaticamente):
#   1. Lê config do banco: postgres_version = "17-alpine"
#   2. Abre docker-compose.yml
#   3. Substitui: postgres:16 → postgres:17-alpine
#   4. Salva arquivo
#   5. Executa: docker compose run zotonic...

# Resultado: Sempre usa a versão correta, sem você precisar editar YAML!
```

**Economia de tempo:** 5-10 minutos por mudança de versão × N mudanças/mês = horas economizadas

---

**2. 🎯 Menu Centralizado e Intuitivo**

**O problema que resolve:**
Navegar entre pastas, lembrar comandos específicos de cada projeto, abrir múltiplos terminais.

**Como o Aedificator resolve:**
```bash
python -m src.cli
# Interface interativa aparece:
# ┌─ Menu Principal ─┐
# │ Superleme        │
# │ SL Phoenix       │
# │ Extensão         │
# │ ...              │
# └──────────────────┘

# Escolhe "Superleme"
# ┌─ Superleme ─────────────┐
# │ Recompilar (Clean & Make)│
# │ Executar (debug mode)    │
# │ Iniciar (start)          │
# │ Parar (stop)             │
# │ Status                   │
# └──────────────────────────┘
```

**Benefícios:**
- ✅ **Um único ponto de entrada** - não precisa lembrar onde está cada projeto
- ✅ **Comandos prontos** - make, test, lint, build pré-configurados
- ✅ **Contexto automático** - Aedificator sabe qual diretório usar, qual Docker compose, etc.
- ✅ **Zero configuração manual** - depois da primeira execução, tudo está salvo

**Economia de tempo:** 30 segundos por comando × 50 comandos/dia = 25 minutos/dia

---

**3. 📡 Execução em Tempo Real**

**O problema que resolve:**
Comandos longos (compilação, testes) não mostram progresso. Você fica no escuro até terminar. Erros aparecem só no final.

**Como o Aedificator resolve:**
```python
# Implementação técnica:
process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    bufsize=0,  # UNBUFFERED - crucial!
    universal_newlines=True
)

# Lê linha por linha e imprime imediatamente
for line in process.stdout:
    print(line, end='')
    sys.stdout.flush()      # Força flush imediato
    log_file.write(line)
    log_file.flush()
```

**Resultado:**
- ✅ **Feedback instantâneo** - vê cada linha enquanto executa
- ✅ **Erros destacados** - aparece em vermelho assim que acontece
- ✅ **Logs salvos** - mesmo se terminal crashar, log está em disco
- ✅ **Debugging facilitado** - sabe exatamente onde parou

**Benefícios reais:**
- Compilação do Zotonic leva 5 minutos? Vê o progresso em tempo real
- Erro no meio da compilação? Vê imediatamente, não espera 5 minutos
- Docker pull demorando? Vê o download progredindo

**Economia de tempo:** Pegar erros cedo = 10-30 minutos economizados por bug

---

**4. 🐳 Docker Transparente e Inteligente**

**O problema que resolve:**
Docker é poderoso mas verboso. Comandos longos, flags obscuras, volumes complicados.

**Como o Aedificator resolve:**

**Sem Aedificator:**
```bash
docker compose run \
  --rm \
  --service-ports \
  -w /opt/zotonic \
  -u 1000:1000 \
  -e PYTHONUNBUFFERED=1 \
  zotonic \
  bash -c 'rm -rf _build && make clean && make'

# Você tem que:
# - Lembrar todas as flags
# - Saber o working directory correto
# - Saber qual usuário usar
# - Configurar variáveis de ambiente
```

**Com Aedificator:**
```bash
# Menu: Superleme → Recompilar (Clean & Make)
# Aedificator faz tudo automaticamente:
# - Envolve comando com Docker
# - Adiciona flags corretas (--verbose, --progress=plain)
# - Configura working directory
# - Gerencia permissões
# - Remove volumes órfãos
```

**Funcionalidades extras:**
- ✅ **Detecção automática** - sabe quando usar Docker (via config no banco)
- ✅ **Cleanup inteligente** - remove volumes órfãos antes de rebuild
- ✅ **Permissões corretas** - cria `_build` como user 1000:1000, não root
- ✅ **Flags verbose** - debugging facilitado com `--verbose --progress=plain`

**Benefícios técnicos:**
- Evita "device or resource busy" gerenciando volumes corretamente
- Evita permission denied criando diretórios com ownership correto
- Logs completos com saída verbose do Docker

---

**5. 🚀 Execução Múltipla**

**O problema que resolve:**
Frontend precisa de backend rodando. Backend precisa de banco. Tudo tem que estar up ao mesmo tempo.

**Como o Aedificator resolve:**
```bash
# Menu: Executar Múltiplos → Superleme + SL Phoenix (dev)

# Aedificator (automaticamente):
# - Inicia Zotonic em background
# - Inicia Phoenix em background
# - Monitora ambos
# - Mostra status em tempo real
# - Ctrl+C mata os dois gracefully
```

**Uso prático:**
```
┌─ Processos Executando ─┐
│ [PID 1234] Zotonic      │ ✅ Running
│ [PID 5678] Phoenix      │ ✅ Running
│                          │
│ Pressione Ctrl+C para   │
│ parar todos os processos│
└──────────────────────────┘
```

**Benefícios:**
- ✅ **Gerenciamento centralizado** - um processo controla todos
- ✅ **Cleanup automático** - Ctrl+C mata tudo gracefully (SIGTERM)
- ✅ **Logs separados** - cada projeto tem seu próprio arquivo de log
- ✅ **Ideal para dev** - simula ambiente de produção localmente

---

#### 🎁 Benefícios Adicionais

**Reprodutibilidade**
- Configurações no banco = ambiente reproduzível
- Novo dev: clone repo + `python -m src.cli` = ambiente pronto
- CI/CD: mesmo comando funciona em qualquer máquina

**Documentação Viva**
- Menu mostra todos os comandos disponíveis
- Não precisa consultar README para saber como executar
- Comandos são auto-documentados na interface

**Consistência Entre Desenvolvedores**
- Todos usam mesmo Aedificator = mesmas versões, mesmos comandos
- Elimina "na minha máquina funciona"
- Onboarding: horas → minutos

**Histórico e Auditoria**
- Logs com timestamp preservados
- Sabe exatamente o que foi executado e quando
- Debugging retroativo facilitado

**Manutenibilidade**
- Mudou versão do PostgreSQL? Uma linha no banco
- Novo comando no projeto? Adiciona no menu
- Centralização = menos lugares para atualizar

## 💡 Como Funciona

O Aedificator segue um fluxo simples mas poderoso:

### Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    Aedificator                      │
│                                                     │
│  ┌─────────────┐    ┌──────────────┐               │
│  │  CLI Entry  │───▶│ Menu System  │               │
│  └─────────────┘    └──────┬───────┘               │
│                             │                        │
│                             ▼                        │
│              ┌──────────────────────────┐            │
│              │   Configuration Manager  │            │
│              │  (SQLite Database)       │            │
│              └──────────┬───────────────┘            │
│                         │                            │
│                         ▼                            │
│              ┌──────────────────────────┐            │
│              │  Docker Compose Updater  │            │
│              │  (Regex Version Replacer)│            │
│              └──────────┬───────────────┘            │
│                         │                            │
│                         ▼                            │
│              ┌──────────────────────────┐            │
│              │   Command Executor       │            │
│              │  (Real-time Output)      │            │
│              └──────────┬───────────────┘            │
│                         │                            │
│                         ▼                            │
│              ┌──────────────────────────┐            │
│              │   Log Manager            │            │
│              │  (Timestamped Files)     │            │
│              └──────────────────────────┘            │
└─────────────────────────────────────────────────────┘
```

### Fluxo de Execução Detalhado

**1. Inicialização (Primeira Execução)**
```bash
python -m src.cli
```

O que acontece:
- Detecta automaticamente pastas dos projetos via `pathing.main`
- Pergunta interativamente (via `questionary`):
  - "Usar Docker para Superleme?" → salva em `dockerconfiguration.use_docker`
  - "Versão do PostgreSQL?" → salva em `dockerconfiguration.postgres_version`
  - "Versão do Erlang?" → salva em `dockerconfiguration.languages` (JSON)
- Cria banco SQLite em `src/data/aedificator.db`
- Gera tabelas: `paths`, `dockerconfiguration`

**2. Persistência de Configurações**
```sql
-- Exemplo de dados salvos:
INSERT INTO dockerconfiguration VALUES (
  1,                           -- id
  'superleme',                 -- project_name
  1,                           -- use_docker (boolean)
  '17-alpine',                 -- postgres_version
  '/path/to/docker-compose.yml', -- compose_file
  '{"erlang": "28", "postgresql": "17-alpine"}' -- languages (JSON)
);
```

**3. Atualização Automática de Docker Compose**

Antes de cada comando, o Aedificator:

```python
# executor.py - _update_docker_compose_versions()
def _update_docker_compose_versions(cwd, docker_config):
    compose_file = os.path.join(cwd, 'docker-compose.yml')

    # Lê arquivo
    with open(compose_file, 'r') as f:
        content = f.read()

    # Substitui versão PostgreSQL com regex
    postgres_version = docker_config.get('postgres_version')
    content = re.sub(
        r'postgres:[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9]+)?',
        f'postgres:{postgres_version}',
        content
    )

    # Salva de volta
    with open(compose_file, 'w') as f:
        f.write(content)
```

**Exemplo real:**
```yaml
# Antes:
services:
  postgres:
    image: postgres:16.2-alpine

# Depois (automaticamente):
services:
  postgres:
    image: postgres:17-alpine
```

**4. Execução com Saída em Tempo Real**

```python
# executor.py - run_command()
env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'

process = subprocess.Popen(
    wrapped_command,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    bufsize=0,  # CRÍTICO: unbuffered
    universal_newlines=True,
    env=env
)

# Lê linha por linha
with open(log_filename, 'w') as log_file:
    for line in process.stdout:
        print(line, end='')        # Console
        sys.stdout.flush()         # Força flush
        log_file.write(line)       # Log file
        log_file.flush()           # Salva no disco
```

**5. Logging Persistente**
```
src/data/logs/
├── superleme_20251215_132226.log    # Timestamp no filename
├── superleme_20251215_145801.log
└── sl_phoenix_20251215_133045.log
```

---

### Exemplo Completo: Fluxo de "Recompilar Superleme"

```
┌──────────────────────────────────────────────────────┐
│ USUÁRIO: Seleciona "Superleme → Recompilar"         │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ MENU.PY: show_superleme_menu()                       │
│ - Identifica: zotonic_root = /home/user/zotonic      │
│ - Carrega: docker_config do banco de dados          │
│   └─ use_docker=True, postgres_version='17-alpine'  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ EXECUTOR.PY: Preparação                              │
│ 1. Para containers órfãos                            │
│    docker compose down --volumes --remove-orphans    │
│                                                      │
│ 2. Remove volume zotonic_build                       │
│    docker volume rm zotonic_build                    │
│                                                      │
│ 3. Cria _build com permissões corretas               │
│    docker compose run --user root zotonic \          │
│      bash -c 'mkdir -p _build && chown 1000:1000...' │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ EXECUTOR.PY: Atualização Docker Compose              │
│ - Abre: /home/user/zotonic/docker-compose.yml        │
│ - Regex: postgres:16 → postgres:17-alpine            │
│ - Salva arquivo atualizado                          │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ EXECUTOR.PY: Monta comando Docker                    │
│                                                      │
│ wrapped_command = (                                  │
│   "docker compose run --rm zotonic "                 │
│   "bash -c 'make clean && make'"                     │
│ )                                                    │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ EXECUTOR.PY: Execução                                │
│                                                      │
│ process = subprocess.Popen(                          │
│   wrapped_command,                                   │
│   bufsize=0  # unbuffered                            │
│ )                                                    │
│                                                      │
│ # Loop de saída em tempo real                       │
│ for line in process.stdout:                          │
│   print(line)           # → Terminal                 │
│   log_file.write(line)  # → logs/superleme_....log  │
│   flush()                                            │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│ RESULTADO                                            │
│                                                      │
│ ✅ Compilação rodando com:                            │
│    - PostgreSQL 17 (versão correta)                  │
│    - Erlang 28 (versão correta)                      │
│    - Permissões corretas (_build owned by 1000:1000)│
│    - Saída em tempo real no terminal                │
│    - Log salvo em disco                              │
│                                                      │
│ 🚀 Sem você precisar:                                 │
│    - Lembrar comandos Docker complexos               │
│    - Editar YAML manualmente                         │
│    - Navegar entre diretórios                        │
│    - Debuggar problemas de permissão                 │
└──────────────────────────────────────────────────────┘
```

---

### Casos de Uso Reais

#### 1. **Desenvolvimento Local vs. Docker (Flexibilidade)**

**Cenário:** Você tem um laptop com Erlang instalado nativamente e um desktop onde usa só Docker.

**Como o Aedificator resolve:**
```bash
# Laptop (nativo):
Menu → Configurações → Docker Superleme → Desativar
# Agora: Menu → Superleme → Executar
# Executa: bin/zotonic debug (nativo)

# Desktop (Docker):
Menu → Configurações → Docker Superleme → Ativar
# Agora: Menu → Superleme → Executar
# Executa: docker compose run zotonic bin/zotonic debug
```

**Benefício:** Mesmo código, mesmo Aedificator, ambientes diferentes. Zero mudança no workflow.

---

#### 2. **Migrações de Banco de Dados (Múltiplas Versões)**

**Cenário:** Você mantém um projeto legado (PostgreSQL 14) e está migrando para novo projeto (PostgreSQL 17).

**Problema sem Aedificator:**
```bash
# Terminal 1: Projeto legado
docker compose down
# edita docker-compose.yml: postgres:17 → postgres:14
docker compose up -d

# Terminal 2: Projeto novo
docker compose down
# edita docker-compose.yml: postgres:14 → postgres:17
docker compose up -d

# Erro: Esqueceu de trocar? Banco usa schema errado, migrations falham.
```

**Com Aedificator:**
- Superleme configurado com PostgreSQL 14
- SL Phoenix configurado com PostgreSQL 17
- Aedificator atualiza YAML automaticamente antes de cada execução
- **Impossível** usar versão errada

---

#### 3. **Conflitos de Versão de Runtime (Erlang 25 vs 28)**

**Cenário:** Projeto A usa Erlang 25 (bytecode antigo), Projeto B usa Erlang 28 (bytecode novo).

**Problema:** Instalar ambas versões nativamente causa conflitos. `asdf` resolve, mas trocar manualmente é tedioso.

**Com Aedificator + Docker:**
- Cada projeto roda em container isolado
- Erlang 25 no container do Projeto A
- Erlang 28 no container do Projeto B
- Aedificator gerencia qual container usar
- **Zero** conflito

---

#### 4. **Onboarding de Novos Desenvolvedores**

**Sem Aedificator:**
```
Dia 1: Instala Erlang, Elixir, PostgreSQL, Node.js
Dia 2: Debugga conflitos de versão, path issues
Dia 3: Finalmente roda o projeto... mas versão errada
Dia 4: "Na minha máquina não funciona"
Dia 5: Desiste e pede ajuda ao senior dev
```

**Com Aedificator:**
```bash
# Dia 1:
git clone projeto
cd projeto/Aedificator
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m src.cli
# Menu: tudo está pré-configurado
# Executa projeto em 30 minutos
```

**Economia:** 4 dias → 30 minutos

---

#### 5. **Debugging em Produção (Logs Históricos)**

**Cenário:** Bug apareceu ontem. Você precisa saber exatamente o que foi executado.

**Com Aedificator:**
```bash
ls src/data/logs/
# superleme_20251214_143022.log  ← Ontem às 14:30
# superleme_20251215_091045.log  ← Hoje às 09:10

cat src/data/logs/superleme_20251214_143022.log
# Vê exatamente:
# - Qual comando foi executado
# - Qual output teve
# - Onde parou/falhou
```

**Benefício:** Auditoria completa, debugging retroativo

## 📋 Características

- **Menu Interativo**: Interface de linha de comando intuitiva com questionary
- **Suporte Docker**: Execução de comandos dentro de containers Docker com configuração automática
- **Execução em Tempo Real**: Visualize a saída de comandos enquanto executam (stdout/stderr em tempo real)
- **Logs Persistentes**: Todos os comandos são salvos em `src/data/logs/` com timestamp
- **Configuração de Versões**: Configure versões de linguagens (Erlang, Elixir, PostgreSQL, Node.js) que atualizam automaticamente o docker-compose.yml
- **Detecção Automática**: Encontra pastas de projetos automaticamente
- **Execução Múltipla**: Execute múltiplos projetos simultaneamente com painel live
- **Modo Verbose**: Docker compose com flags --verbose e --progress=plain para debugging

## 🚀 Instalação

```bash
# Clone o repositório
git clone <repo-url>
cd Aedificator

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

## 📦 Dependências

- Python 3.14+
- peewee (ORM para SQLite)
- rich (Interface de terminal colorida)
- questionary (Menus interativos)

## 🎯 Uso

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o programa
python -m src.cli
```

### Primeira Execução

Na primeira execução, o programa irá:

1. Criar banco de dados em `src/data/aedificator.db`
2. Detectar automaticamente as pastas dos projetos
3. Perguntar se deseja usar Docker
4. Solicitar versões de linguagens (Erlang, PostgreSQL, Elixir, Node.js)
5. Salvar configurações no banco de dados

### Menu Principal

O menu oferece as seguintes opções:

- **Superleme**: Gerenciar projeto Zotonic
  - Executar (debug mode)
  - Iniciar (start)
  - Parar (stop)
  - Status
  - Compilar (make)

- **SL Phoenix**: Gerenciar projeto Phoenix
  - make server
  - make setup
  - make install
  - make clean
  - make test
  - make lint
  - make format
  - make assets

- **Extensão**: Gerenciar extensão
  - make dev
  - make watch
  - make build
  - make production
  - make lint
  - make test
  - make clean
  - make install

- **Executar Múltiplos**: Execute vários projetos simultaneamente
  - Superleme + SL Phoenix (dev)
  - Superleme + SL Phoenix (build)
  - Custom (escolha os projetos e comandos)

- **Configurações**
  - Versões de Linguagens - Superleme
  - Versões de Linguagens - SL Phoenix
  - Configurações Docker - Superleme
  - Configurações Docker - SL Phoenix

## 🐳 Docker

### Configuração Automática

O Aedificator atualiza automaticamente o `docker-compose.yml` com as versões configuradas no banco de dados antes de executar qualquer comando.

**Exemplo:**
- Você configura PostgreSQL 17-alpine no menu
- Ao executar Superleme, o programa:
  1. Lê a configuração do banco de dados
  2. Atualiza `postgres:16.2-alpine` → `postgres:17-alpine` no docker-compose.yml
  3. Executa o comando Docker com a versão correta

### Diretórios de Trabalho

Cada projeto usa um diretório de trabalho específico dentro do container:

- **Superleme (Zotonic)**: `/opt/zotonic` - onde o Zotonic espera encontrar seus arquivos
- **SL Phoenix**: `/app` - convenção padrão para aplicações Elixir/Phoenix
- **Extensão**: `/workspace` ou `/app` - dependendo da configuração

O Aedificator configura automaticamente o working directory correto com a flag `-w` no comando Docker.

📖 **Documentação completa:** Veja [DOCKER_DIRECTORIES.md](docs/DOCKER_DIRECTORIES.md) para detalhes sobre configuração de diretórios, volumes, permissões e troubleshooting.

### Flags Verbose

Todos os comandos Docker são executados com:
- `--ansi=never`: Remove códigos ANSI que causam buffering
- `--verbose`: Mostra logs detalhados
- `--progress=plain`: Progresso em texto plano sem animações
- `stdbuf -o0 -e0`: Força saída sem buffer para logs em tempo real

## 📊 Logs

Todos os comandos executados são salvos em:

```
src/data/logs/
├── superleme_20251215_132226.log
├── sl_phoenix_20251215_133045.log
└── extension_20251215_134512.log
```

Os logs incluem:
- Saída completa (stdout + stderr)
- Timestamp no nome do arquivo
- Erros são impressos em vermelho no console em tempo real

## 🗄️ Banco de Dados

Localizado em `src/data/aedificator.db` (SQLite)

### Tabelas

**Paths**: Armazena caminhos dos projetos
- `superleme_path`
- `sl_phoenix_path`
- `extension_path`

**DockerConfiguration**: Configurações Docker por projeto
- `project_name` (superleme, sl_phoenix)
- `use_docker` (boolean)
- `postgres_version` (ex: 17-alpine)
- `compose_file` (caminho para docker-compose.yml)
- `languages` (JSON com versões: erlang, elixir, node, postgresql)

### Resetar Banco de Dados

```bash
rm src/data/aedificator.db
# Na próxima execução, o programa irá recriar e perguntar todas as configurações
```

## 🎨 Interface

A interface usa Rich para formatação colorida:

- **[info]** Cyan: Informações
- **[success]** Verde: Sucesso
- **[warning]** Amarelo: Avisos
- **[error]** Vermelho: Erros
- Texto normal: Cor padrão do terminal (compatível com light mode)

## 🔧 Estrutura do Projeto

```
Aedificator/
├── src/
│   ├── aedificator/
│   │   ├── __init__.py         # Console e tema Rich
│   │   ├── main.py             # Lógica principal e inicialização
│   │   ├── menu.py             # Sistema de menus interativos
│   │   ├── executor.py         # Execução de comandos e Docker
│   │   └── memory/             # Persistência de dados
│   │       ├── __init__.py
│   │       ├── db.py           # Configuração do banco de dados
│   │       └── models.py       # Modelos Peewee
│   ├── pathing/
│   │   ├── __init__.py
│   │   └── main.py             # Detecção e seleção de pastas
│   ├── cli.py                  # Entry point
│   └── data/
│       ├── aedificator.db      # Banco de dados SQLite
│       └── logs/               # Logs de execução
├── CLAUDE.md                   # Instruções para Claude
├── AGENTS.md                   # Funcionalidades para agentes
├── README.md                   # Este arquivo
└── requirements.txt            # Dependências Python
```

## 🤝 Contribuindo

Este projeto é mantido pela Abensoft. Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Propriedade da Abensoft. Todos os direitos reservados.

## 🐛 Troubleshooting

### Logs aparecem na diagonal ou com caracteres estranhos
**Problema:** Saída do Docker aparece em diagonal ou com formatação estranha

**Causa:** Caracteres de controle (carriage return `\r`) misturados com newlines

**Solução:** O Aedificator remove automaticamente caracteres `\r` e força line buffering. Se ainda tiver problemas:
```bash
# Verifique se stdbuf está instalado
which stdbuf

# Se não estiver, instale coreutils
sudo apt-get install coreutils  # Debian/Ubuntu
sudo yum install coreutils      # CentOS/RHEL
```

### Logs não aparecem
- Verifique se o diretório `src/data/logs/` existe
- O programa cria automaticamente, mas pode haver problema de permissões

### Docker não está usando versão correta
- Verifique a configuração no menu "Configurações"
- O programa atualiza o docker-compose.yml automaticamente antes de cada execução
- Verifique os logs para ver qual comando Docker foi executado

### Comandos Docker não encontram arquivos
**Problema:** Erro "file not found" ou "command not found" dentro do container

**Causa:** Working directory incorreto dentro do container

**Solução:** O Aedificator configura automaticamente:
- Zotonic: `-w /opt/zotonic`
- Phoenix: `-w /app`

Verifique no log se o comando inclui o `-w` correto.

### Saída não aparece em tempo real
- O programa usa `bufsize=1` (line buffered) e `flush()` após cada linha
- Comandos Docker incluem `stdbuf -o0 -e0` para forçar unbuffered
- Se ainda tiver problema, verifique se o comando não está bufferizando internamente

### Banco de dados corrompido
```bash
rm src/data/aedificator.db
# Reinicie o programa
```

## 📞 Suporte

Para suporte, entre em contato com a equipe Abensoft.
