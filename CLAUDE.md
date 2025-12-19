# Instruções para Claude - Aedificator

Este arquivo contém instruções específicas para Claude (Anthropic) ao trabalhar com o projeto Aedificator.

## 🌐 Idioma

**REGRA FUNDAMENTAL**: Keep all printing operations exclusively in the language **PORTUGUESE**.

Todas as mensagens de console, prints, logs e comunicação com o usuário devem estar em PORTUGUÊS BRASILEIRO.

### Exemplos

```python
# ✅ CORRETO
console.print("[info]Executando comando...[/info]")
console.print("[success]Comando executado com sucesso[/success]")
console.print("[error]Erro ao executar comando[/error]")
console.print(f"Diretório: {cwd}")
console.print(f"Log: {log_filename}")

# ❌ ERRADO
console.print("[info]Executing command...[/info]")
console.print("[success]Command executed successfully[/success]")
console.print("[error]Error executing command[/error]")
console.print(f"Directory: {cwd}")
console.print(f"Log: {log_filename}")
```

### Mensagens Padrão

Use estas mensagens consistentemente:

```python
# Execução
"Executando comando..."
"Comando executado com sucesso"
"Comando falhou com código {returncode}"

# Docker
"Usando Docker para executar comando"
"Modo Docker ativo - usando run.sh"
"Versão do PostgreSQL atualizada para: {version}"

# Logs
"Log: {filename}"
"Logs salvos em:"

# Processos
"Processo iniciado em background (PID: {pid})"
"Processos executando... Pressione Ctrl+C para parar"
"Todos os processos finalizaram"

# Configuração
"Configuração Docker atualizada!"
"Versões atualizadas com sucesso!"

# Erros
"Diretório não encontrado: {path}"
"Não foi possível executar comando: {error}"
"Erro:"
```

## 🎨 Cores e Temas

### Cores Permitidas

O projeto usa Rich com tema personalizado. **Evite cores escuras** para compatibilidade com light mode:

```python
# Tema atual em __init__.py
_theme = Theme({
    "info": "cyan",      # ✅ Informações
    "warning": "yellow",  # ✅ Avisos
    "error": "bold red",  # ✅ Erros
    "success": "green"    # ✅ Sucesso
})

# ✅ PERMITIDO
console.print("[info]...[/info]")
console.print("[success]...[/success]")
console.print("[warning]...[/warning]")
console.print("[error]...[/error]")
console.print("Texto normal")  # Cor padrão do terminal

# ❌ NUNCA USE
console.print("[muted]...[/muted]")  # Removido do tema
console.print("[dim]...[/dim]")      # Escuro demais
console.print("[gray]...[/gray]")    # Escuro demais
console.print("[black]...[/black]")  # Escuro demais
```

### Razão

O usuário usa **light mode** no terminal. Cores escuras (dim, muted, gray, black) são ilegíveis em terminais claros.

## 🗂️ Estrutura de Arquivos

### Hierarquia de Diretórios

```
Aedificator/
├── src/
│   ├── aedificator/
│   │   ├── __init__.py         # Console e tema Rich
│   │   ├── main.py             # Entry point, inicialização
│   │   ├── menu.py             # Menus interativos
│   │   ├── executor.py         # Execução de comandos
│   │   └── memory/
│   │       ├── __init__.py
│   │       ├── db.py           # DB config
│   │       └── models.py       # Peewee models
│   ├── pathing/
│   │   └── main.py             # Detecção de pastas
│   ├── cli.py                  # Entry point
│   └── data/
│       ├── aedificator.db      # SQLite DB
│       └── logs/               # Logs de execução
├── CLAUDE.md                   # Este arquivo
├── AGENTS.md                   # Instruções para agentes
└── README.md                   # Documentação
```

### Cálculo de Caminhos

**IMPORTANTE**: NUNCA use `os.getcwd()` - sempre use caminhos relativos ao arquivo.

```python
# ❌ ERRADO - depende de onde o comando é executado
DB_DIR = os.path.join(os.getcwd(), "data")
log_dir = os.path.join(os.getcwd(), "logs")

# ✅ CORRETO - relativo ao arquivo
# A partir de aedificator/executor.py:
# executor.py -> aedificator/ -> src/ -> data/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
log_dir = os.path.join(project_root, "data", "logs")

# A partir de memory/db.py:
# db.py -> memory/ -> aedificator/ -> src/ -> data/
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(SRC_DIR, "data")
DB_FILE = os.path.join(DB_DIR, "aedificator.db")
```

### Localização de Recursos

```python
# Banco de dados
src/data/aedificator.db

# Logs
src/data/logs/{project_name}_{timestamp}.log

# Configurações (no banco de dados)
- Tabela: paths
- Tabela: dockerconfiguration
```

## 🐳 Docker

### Fluxo de Execução

1. **Atualizar docker-compose.yml** com versões do banco de dados
2. **Envolver comando** com Docker Compose
3. **Executar** com flags verbose
4. **Capturar saída** em tempo real
5. **Salvar log** em src/data/logs/

```python
def run_command(command: str, cwd: str, use_docker: bool = False, docker_config: Optional[Dict] = None):
    # 1. Atualizar docker-compose.yml
    if use_docker and Executor._has_docker_compose(cwd):
        Executor._update_docker_compose_versions(cwd, docker_config)

    # 2. Envolver com Docker
    wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

    # 3. Executar e capturar
    # ... código de execução ...
```

### Flags Obrigatórias

```python
docker_cmd = f'NO_PROXY=* docker compose --ansi=never --verbose --progress=plain -f docker-compose.yml run --service-ports zotonic {command}'
```

**Explicação:**
- `NO_PROXY=*`: Evita problemas de proxy (Zotonic específico)
- `--ansi=never`: Remove códigos ANSI que causam buffering
- `--verbose`: Mostra logs detalhados de Docker Compose
- `--progress=plain`: Progresso em texto plano (sem animações)

### Atualização Automática de Versões

O sistema atualiza `docker-compose.yml` automaticamente usando regex:

```python
def _update_docker_compose_versions(cwd: str, docker_config: Optional[Dict] = None):
    # Lê docker-compose.yml
    with open(compose_file, 'r') as f:
        content = f.read()

    # Substitui versão do PostgreSQL
    postgres_version = docker_config.get('postgres_version')
    if postgres_version:
        content = re.sub(
            r'postgres:[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9]+)?',
            f'postgres:{postgres_version}',
            content
        )

    # Salva de volta
    with open(compose_file, 'w') as f:
        f.write(content)
```

**Padrão regex**: `postgres:16.2-alpine` → `postgres:17-alpine`

### Configuração de Portas PostgreSQL

**IMPORTANTE**: Entenda a diferença entre portas internas e externas no Docker:

- **Porta INTERNA** (dentro da rede Docker): **5432** - usada por containers para se comunicar entre si
- **Porta EXTERNA** (acesso do host): **15432** - mapeada para evitar conflito com PostgreSQL local

**Razão**: A porta 5432 já está em uso no host pela instalação local do PostgreSQL, então mapeamos para 15432.

```python
# Configuração CORRETA no zotonic_site.config (comunicação entre containers)
{dbhost, "postgres"},
{dbport, 5432},  # ✅ Porta INTERNA do Docker
{dbuser, "postgres"},
{dbpassword, "abensoft"}

# Acesso do HOST ao PostgreSQL (psql, DBeaver, etc)
# Use: localhost:15432
psql -h localhost -p 15432 -U postgres -d superleme
```

**Regra**:
- **Containers → PostgreSQL**: porta **5432** (interna)
- **Host → PostgreSQL**: porta **15432** (externa)

### Estrutura de Apps Zotonic

Os sites Zotonic têm uma estrutura específica de diretórios:

```
/opt/zotonic/apps_user/
└── superleme/                    # Diretório raiz do projeto
    ├── superleme/                # App Zotonic principal (note a duplicação)
    │   ├── priv/
    │   │   └── zotonic_site.config  # ✅ Arquivo de configuração aqui
    │   └── src/
    │       └── superleme.app.src
    ├── zotonic_mod_sl_*/         # Módulos do projeto
    └── priv/                     # ❌ NÃO colocar zotonic_site.config aqui
```

**Localização correta do config**: `/opt/zotonic/apps_user/superleme/superleme/priv/zotonic_site.config`

**Localização INCORRETA**: `/opt/zotonic/apps_user/superleme/priv/zotonic_site.config`

## 📊 Saída em Tempo Real

### Configuração do Processo

```python
# Variáveis de ambiente para unbuffered output
env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'
env['DOCKER_BUILDKIT_PROGRESS'] = 'plain'

# Processo sem buffer
process = subprocess.Popen(
    wrapped_command,
    shell=True,
    cwd=cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    executable='/bin/bash',
    bufsize=0,  # 0 = unbuffered - CRÍTICO!
    universal_newlines=True,
    env=env
)
```

### Leitura e Flush

```python
# Lê e imprime linha por linha
for line in process.stdout:
    # Print to console
    print(line, end='')
    sys.stdout.flush()  # CRÍTICO - força flush imediato

    # Write to log file
    log_file.write(line)
    log_file.flush()
```

**IMPORTANTE**:
- `bufsize=0` é essencial
- `sys.stdout.flush()` depois de cada print
- `log_file.flush()` para garantir escrita no disco

### Debugging de Saída

Se a saída não aparecer em tempo real:
1. Verifique `bufsize=0`
2. Verifique `sys.stdout.flush()`
3. Verifique variáveis de ambiente (`PYTHONUNBUFFERED`)
4. Verifique se o comando em si não está bufferizando

## 🗄️ Banco de Dados

### Schema

```sql
-- Tabela Paths
CREATE TABLE paths (
    id INTEGER PRIMARY KEY,
    superleme_path TEXT,
    sl_phoenix_path TEXT,
    extension_path TEXT
);

-- Tabela DockerConfiguration
CREATE TABLE dockerconfiguration (
    id INTEGER PRIMARY KEY,
    project_name TEXT,              -- 'superleme' ou 'sl_phoenix'
    use_docker INTEGER,             -- 0 ou 1 (boolean)
    postgres_version TEXT,          -- ex: '17-alpine'
    compose_file TEXT,              -- caminho para docker-compose.yml
    languages TEXT                  -- JSON: {"erlang": "28", "elixir": "1.19.4", ...}
);
```

### Acesso

```python
from .memory import DockerConfiguration, Paths

# Carregar config
config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
postgres_version = config.postgres_version
languages = json.loads(config.languages)

# Atualizar config
config.postgres_version = '17-alpine'
config.save()

# Criar config
DockerConfiguration.create(
    project_name='superleme',
    use_docker=True,
    postgres_version='17-alpine',
    languages='{"erlang": "28", "postgresql": "17-alpine"}'
)
```

### Verificação

Para verificar o conteúdo do banco:

```python
import sqlite3
conn = sqlite3.connect('src/data/aedificator.db')
cursor = conn.cursor()

# Ver configs
cursor.execute('SELECT * FROM dockerconfiguration')
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 🔄 Fluxo de Dados

### Inicialização (main.py)

1. Cria tabelas se não existirem
2. Verifica se é primeira instalação (`not selected or not has_docker_config`)
3. Se primeira instalação:
   - Pergunta se usa Docker
   - Pergunta versões (Erlang, PostgreSQL, Elixir, Node.js)
   - Salva no banco de dados
4. Se não:
   - Carrega configurações do banco
5. Passa configurações para Menu

### Menu (menu.py)

1. Recebe `docker_configs` do main
2. Usuário escolhe operação
3. Menu determina:
   - Comando a executar
   - Diretório de trabalho (cwd)
   - Se usa Docker (use_docker)
   - Configuração Docker (docker_config)
4. Chama `Executor.run_command()` ou `Executor.run_make()`

### Executor (executor.py)

1. Recebe comando, cwd, use_docker, docker_config
2. Se use_docker:
   - Atualiza docker-compose.yml com versões do DB
   - Envolve comando com Docker Compose
3. Cria processo Popen
4. Captura saída em tempo real
5. Salva log em src/data/logs/
6. Retorna status

## 📝 Modificações Comuns

### Adicionar Nova Operação ao Menu

```python
# menu.py - show_superleme_menu()
choice = questionary.select(
    "Escolha uma operação:",
    choices=[
        "Nova Operação",  # Adicione aqui
        "Voltar"
    ]
).ask()

if choice == "Nova Operação":
    Executor.run_command(
        "seu_comando",
        zotonic_root,
        background=False,
        use_docker=use_docker,
        docker_config=docker_config
    )
```

### Adicionar Suporte para Nova Versão

```python
# executor.py - _update_docker_compose_versions()
def _update_docker_compose_versions(cwd: str, docker_config: Optional[Dict] = None):
    # ... código existente ...

    # Adicionar suporte para nova imagem
    if docker_config.get('languages'):
        languages = json.loads(docker_config['languages'])
        node_version = languages.get('node')
        if node_version:
            content = re.sub(
                r'node:[0-9]+(\.[0-9]+)?(\.[0-9]+)?',
                f'node:{node_version}',
                content
            )
```

### Adicionar Novo Campo no Banco

```python
# 1. models.py
class DockerConfiguration(BaseModel):
    nova_config = TextField(null=True)

# 2. main.py - primeira instalação
nova_config = questionary.text("Nova config:", default="valor").ask()
docker_configs['superleme']['nova_config'] = nova_config

# 3. main.py - salvar
DockerConfiguration.create(
    # ... campos existentes ...
    nova_config=docker_configs['superleme'].get('nova_config')
)

# 4. menu.py - configurações
def _configure_superleme_versions(self):
    nova_config = questionary.text("Nova config:").ask()
    config.nova_config = nova_config
    config.save()
```

## 🐛 Troubleshooting

### Problema: Logs não aparecem

**Sintoma**: Arquivo de log vazio ou não existe

**Diagnóstico**:
```python
# Verifique o caminho calculado
import os
from aedificator.executor import Executor
# Coloque breakpoint ou print no executor.py linha ~77
print(f"DEBUG: log_dir = {log_dir}")
print(f"DEBUG: log_filename = {log_filename}")
```

**Solução**: Caminho estava usando `os.getcwd()`. Mudamos para caminho relativo ao arquivo.

### Problema: Versão errada do PostgreSQL

**Sintoma**: Docker puxa PostgreSQL 16 apesar de configurar 17

**Diagnóstico**:
```bash
# Ver configuração no banco
python3 -c "
import sqlite3
conn = sqlite3.connect('src/data/aedificator.db')
cursor = conn.cursor()
cursor.execute('SELECT project_name, postgres_version FROM dockerconfiguration')
print(cursor.fetchall())
"
```

**Solução**: Implementamos `_update_docker_compose_versions()` que atualiza automaticamente o YAML antes de executar.

### Problema: Saída não é em tempo real

**Sintoma**: Output só aparece no final da execução

**Diagnóstico**:
- Verifique `bufsize` no Popen
- Verifique se tem `sys.stdout.flush()`
- Verifique variáveis de ambiente

**Solução**:
```python
bufsize=0  # Deve ser 0, não 1
sys.stdout.flush()  # Depois de cada print
env['PYTHONUNBUFFERED'] = '1'
```

### Problema: Cores ilegíveis

**Sintoma**: Texto cinza/escuro em terminal light mode

**Solução**: Remova `[muted]`, `[dim]`, `[gray]` do código. Use apenas cores do tema oficial.

## ✅ Checklist antes de Commit

Ao fazer modificações, verifique:

- [ ] Todos os prints estão em PORTUGUÊS
- [ ] Nenhuma cor escura foi usada (dim, muted, gray, black)
- [ ] Caminhos são relativos ao arquivo (`__file__`), não `os.getcwd()`
- [ ] Logs salvos em `src/data/logs/` (não `logs/` ou outro lugar)
- [ ] Docker compose atualizado antes de executar
- [ ] Saída em tempo real (bufsize=0, flush)
- [ ] Flags verbose no Docker (--verbose, --progress=plain, --ansi=never)
- [ ] Erros mostrados em vermelho com conteúdo do log
- [ ] Configurações salvas no banco de dados
- [ ] Documentação atualizada se necessário

## 🎯 Padrões de Código

### Imports

```python
import subprocess
import os
import sys
import re
import json
from typing import Optional, List, Dict
from . import console
from rich.console import Console
from rich.theme import Theme
```

### Estilo de Código

- Use type hints: `def func(arg: str) -> Optional[str]:`
- Docstrings em inglês (código) mas prints em português (usuário)
- Nomes de variáveis em inglês: `postgres_version`, `docker_config`
- Mensagens em português: `"Versão do PostgreSQL atualizada"`

### Console Printing

```python
# Sempre use o console importado de __init__
from . import console

# Informações
console.print("[info]Mensagem[/info]")

# Sucesso
console.print("[success]Mensagem[/success]")

# Avisos
console.print("[warning]Mensagem[/warning]")

# Erros
console.print("[error]Mensagem[/error]")

# Texto normal
console.print("Mensagem")

# EXCEÇÃO: Output de comandos
# Use print() direto para output de subprocess
print(line, end='')
sys.stdout.flush()
```

## 📚 Recursos

- **Peewee ORM**: http://docs.peewee-orm.com/
- **Rich**: https://rich.readthedocs.io/
- **Questionary**: https://questionary.readthedocs.io/
- **Docker Compose**: https://docs.docker.com/compose/

## 🚨 Avisos Críticos

1. **SEMPRE** use português nas mensagens ao usuário
2. **NUNCA** use cores escuras (compatibilidade light mode)
3. **SEMPRE** use caminhos relativos ao arquivo (não `os.getcwd()`)
4. **SEMPRE** salve logs em `src/data/logs/`
5. **SEMPRE** atualize docker-compose.yml antes de executar Docker
6. **SEMPRE** use `bufsize=0` e `flush()` para saída em tempo real
7. **SEMPRE** mostre o comando Docker completo ao usuário
8. **SEMPRE** mostre erros em vermelho com conteúdo do log

---

Claude, siga estas instruções rigorosamente ao trabalhar neste projeto. 🤖
Don't touch docker-compose.yml. It is a temporary file.
