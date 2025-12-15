# Aedificator

Ferramenta de automação para gerenciar múltiplos projetos (Superleme, SL Phoenix, e Extensão) com suporte a Docker, execução em tempo real e gerenciamento centralizado de configurações.

## Visão Geral

Aedificator automatiza a execução de múltiplos projetos com diferentes requisitos tecnológicos, gerenciando versões de dependências, configurações Docker e ambientes de desenvolvimento de forma centralizada.

### Problema

Desenvolvimento simultâneo de múltiplos projetos com stacks diferentes:

- **Zotonic (Erlang)**: PostgreSQL 17, Erlang 28
- **Phoenix (Elixir)**: Elixir 1.19.4, Node.js 25
- **Extensão**: Node.js com pipeline próprio

Desafios:
- Conflitos de versão entre projetos (Erlang 25 vs 28, PostgreSQL 14 vs 17)
- Gerenciamento manual de ambientes via `asdf`, `nvm`, `mise`
- Comandos Docker longos e repetitivos
- Configurações inconsistentes entre desenvolvedores
- Saída bufferizada dificulta depuração em tempo real
- Logs perdidos quando processos terminam

### Solução

## Funcionalidades

### 1. Gerenciamento Automático de Versões

Configurações de versões (PostgreSQL, Erlang, Elixir, Node.js) armazenadas em banco SQLite. Antes de cada execução, atualiza automaticamente `docker-compose.yml` via regex:

```python
# Substitui versões automaticamente
postgres:16.2-alpine → postgres:17-alpine
```

Configuração única via menu interativo, sem edição manual de YAML.

### 2. Interface Centralizada

Menu interativo com `questionary` para gerenciar todos os projetos:

```bash
python -m src.cli
# ┌─ Menu Principal ─┐
# │ Superleme        │
# │ SL Phoenix       │
# │ Extensão         │
# └──────────────────┘
```

Comandos pré-configurados por projeto (compilação, testes, execução).

### 3. Execução em Tempo Real

Saída não-bufferizada com `bufsize=0` e `sys.stdout.flush()`:

```python
process = subprocess.Popen(
    command,
    bufsize=0,  # unbuffered
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)

for line in process.stdout:
    print(line, end='')
    sys.stdout.flush()
    log_file.write(line)
```

Logs persistidos em `src/data/logs/` com timestamp.

### 4. Abstração Docker

Encapsula comandos Docker complexos:

```bash
# Comando manual
docker compose run --rm --service-ports -w /opt/zotonic zotonic bin/zotonic debug

# Via Aedificator
Menu → Superleme → Executar
```

Configuração automática de working directories, permissões e variáveis de ambiente.

### 5. Execução Paralela

Gerencia múltiplos processos com monitoramento e cleanup via SIGTERM.

## Arquitetura

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

## Fluxo de Execução

### Inicialização

1. Detecção automática de projetos via `pathing.main`
2. Configuração interativa (primeira execução):
   - Uso de Docker por projeto
   - Versões de dependências (PostgreSQL, Erlang, Elixir, Node.js)
3. Persistência em SQLite (`src/data/aedificator.db`)

### Schema do Banco

```sql
CREATE TABLE dockerconfiguration (
    id INTEGER PRIMARY KEY,
    project_name TEXT,
    use_docker INTEGER,
    postgres_version TEXT,
    compose_file TEXT,
    languages TEXT  -- JSON
);
```

### Atualização de Docker Compose

Regex aplicado antes de cada execução:

```python
def _update_docker_compose_versions(cwd, docker_config):
    content = re.sub(
        r'postgres:[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9]+)?',
        f'postgres:{docker_config["postgres_version"]}',
        content
    )
```

### Logging

Logs em `src/data/logs/{projeto}_{timestamp}.log` com saída duplicada (console + arquivo).

## Instalação

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

## Dependências

- Python 3.14+
- peewee (ORM SQLite)
- rich (formatação de terminal)
- questionary (menus interativos)

## Uso

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Execute o programa
python -m src.cli
```

### Primeira Execução

1. Cria banco de dados em `src/data/aedificator.db`
2. Detecta pastas dos projetos
3. Solicita configurações:
   - Uso de Docker por projeto
   - Versões (Erlang, PostgreSQL, Elixir, Node.js)

### Menu

Operações disponíveis por projeto:

**Superleme (Zotonic)**
- Executar (modo depuração)
- Iniciar/Parar
- Compilar
- Status

**SL Phoenix**
- Servidor de desenvolvimento
- Configuração inicial
- Testes, linting, formatação
- Compilação de recursos

**Extensão**
- Desenvolvimento (com monitoramento)
- Compilação (desenvolvimento/produção)
- Testes, análise estática

**Execução Múltipla**
- Configurações pré-definidas (Superleme + Phoenix)
- Configuração personalizada

**Configurações**
- Versões de linguagens
- Configurações Docker

## Docker

### Atualização Automática de docker-compose.yml

Antes de cada execução, versões configuradas são aplicadas via regex ao `docker-compose.yml`.

### Working Directories

- **Superleme (Zotonic)**: `/opt/zotonic`
- **SL Phoenix**: `/app`
- **Extensão**: `/workspace` ou `/app`

Configurado automaticamente com flag `-w`.

### Flags

Comandos executados com:
- `--ansi=never`: Remove códigos ANSI
- `--verbose`: Logs detalhados
- `--progress=plain`: Progresso em texto plano
- `stdbuf -o0 -e0`: Saída unbuffered

## Logs

Salvos em `src/data/logs/{projeto}_{timestamp}.log` com saída completa (stdout + stderr).

## Banco de Dados

SQLite em `src/data/aedificator.db`

### Tabelas

**paths**: Caminhos dos projetos
**dockerconfiguration**: Configurações Docker e versões (JSON em campo `languages`)

Resetar: `rm src/data/aedificator.db`

## Interface

Rich com tema personalizado:
- `[info]`: Cyan
- `[success]`: Verde
- `[warning]`: Amarelo
- `[error]`: Vermelho

## Estrutura

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

## Contribuindo

Mantido pela Abensoft.

1. Fork o projeto
2. Crie branch: `git checkout -b feature/nome`
3. Commit: `git commit -m 'Descrição'`
4. Push: `git push origin feature/nome`
5. Abra Pull Request

## Licença

Propriedade da Abensoft.

## Troubleshooting

### Saída com formatação estranha

**Causa:** Caracteres `\r` (carriage return) misturados com newlines

**Solução:** Aedificator remove `\r` automaticamente. Se persistir, verifique se `stdbuf` está instalado:
```bash
which stdbuf || sudo apt-get install coreutils
```

### Logs ausentes

Verifique permissões em `src/data/logs/`.

### Versão Docker incorreta

1. Verifique configuração no menu
2. Confirme que `docker-compose.yml` foi atualizado (veja logs)

### Arquivos não encontrados no container

**Causa:** Working directory incorreto

**Solução:** Verifique flag `-w` nos logs:
- Zotonic: `-w /opt/zotonic`
- Phoenix: `-w /app`

### Saída não em tempo real

Verifique se comando usa `bufsize=0` e `stdbuf -o0 -e0`.

### Banco corrompido

```bash
rm src/data/aedificator.db
```

## Suporte

Contato: equipe Abensoft.
