# Instruções para Agentes de IA - Aedificator

Este documento contém instruções específicas para agentes de IA (como Claude, GPT, etc.) trabalharem com o projeto Aedificator.

## 🎯 Contexto do Projeto

Aedificator é um sistema de automação Python que gerencia múltiplos projetos:
- **Superleme**: Aplicação Zotonic (Erlang)
- **SL Phoenix**: Aplicação Phoenix (Elixir)
- **Extensão**: Extensão/Plugin

O sistema oferece menu interativo, suporte Docker, execução em tempo real e configuração persistente.

## 📋 Regras Gerais

### Idioma
**IMPORTANTE**: Todos os prints, mensagens de console e comunicação com o usuário DEVEM estar em **PORTUGUÊS**.

```python
# ✅ CORRETO
console.print("[success]Comando executado com sucesso[/success]")
console.print(f"Diretório: {cwd}")

# ❌ ERRADO
console.print("[success]Command executed successfully[/success]")
console.print(f"Directory: {cwd}")
```

### Cores e Temas

**Evite cores escuras** (compatibilidade com light mode):
- ✅ Permitido: cyan, yellow, red, green, bold
- ❌ Evite: dim, muted, gray, black, dark

```python
# ✅ CORRETO
console.print("[info]Mensagem[/info]")  # cyan
console.print("Texto normal")           # cor padrão do terminal

# ❌ ERRADO
console.print("[muted]Mensagem[/muted]")  # dim/gray
console.print("[dim]Texto[/dim]")         # escuro
```

### Saída em Tempo Real

Sempre force flush para saída imediata:

```python
# ✅ CORRETO
for line in process.stdout:
    print(line, end='')
    sys.stdout.flush()  # Force immediate output
    log_file.write(line)
    log_file.flush()

# Configure processo sem buffer
process = subprocess.Popen(
    command,
    bufsize=0,  # 0 = unbuffered
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT
)
```

## 🗂️ Estrutura de Arquivos

### Caminhos Importantes

```python
# Estrutura de diretórios (a partir de aedificator/executor.py)
# executor.py -> aedificator/ -> src/
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sempre use caminhos absolutos relativos ao arquivo
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
data_dir = os.path.join(src_dir, "data")
log_dir = os.path.join(src_dir, "data", "logs")
```

### Banco de Dados

Localização: `src/data/aedificator.db`

```python
# Não use os.getcwd() - use caminho relativo ao arquivo!
# ❌ ERRADO
DB_DIR = os.path.join(os.getcwd(), "data")

# ✅ CORRETO
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_DIR = os.path.join(SRC_DIR, "data")
```

## 🐳 Docker

### Atualização Automática de Versões

Antes de executar comandos Docker, SEMPRE atualize o docker-compose.yml:

```python
def run_command(command: str, cwd: str, use_docker: bool = False, docker_config: Optional[Dict] = None):
    # 1. Atualizar docker-compose.yml com versões do DB
    if use_docker and Executor._has_docker_compose(cwd):
        Executor._update_docker_compose_versions(cwd, docker_config)

    # 2. Envolver comando com Docker
    wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

    # 3. Executar
    ...
```

### Flags Verbose

SEMPRE use flags verbose para debugging:

```python
docker_cmd = f'NO_PROXY=* docker compose --ansi=never --verbose --progress=plain -f docker-compose.yml run --service-ports zotonic {command}'
```

**Flags obrigatórias:**
- `--ansi=never`: Previne buffering de códigos ANSI
- `--verbose`: Logs detalhados
- `--progress=plain`: Progresso sem animações

### Variáveis de Ambiente

```python
env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'
env['DOCKER_BUILDKIT_PROGRESS'] = 'plain'
env['NO_PROXY'] = '*'  # Para Zotonic
```

## 🔧 Modificações Comuns

### Adicionar Nova Funcionalidade ao Menu

1. Edite `menu.py`
2. Adicione opção ao menu correspondente
3. Use `Executor.run_command()` ou `Executor.run_make()` para executar

```python
def show_superleme_menu(self):
    choice = questionary.select(
        "Escolha uma operação:",
        choices=[
            "Nova Operação",  # Adicione aqui
            "Voltar"
        ]
    ).ask()

    if choice == "Nova Operação":
        Executor.run_command("comando", cwd, background=False,
                           use_docker=use_docker, docker_config=docker_config)
```

### Adicionar Nova Configuração ao Banco

1. Edite `memory/models.py` para adicionar campo
2. Edite `main.py` para perguntar na primeira instalação
3. Edite `menu.py` para permitir edição nas configurações

```python
# models.py
class DockerConfiguration(BaseModel):
    nova_config = TextField(null=True)  # Novo campo

# main.py - primeira instalação
nova_config = questionary.text("Nova configuração:", default="valor").ask()
docker_configs['projeto']['nova_config'] = nova_config

# menu.py - edição
def _configure_projeto(self):
    nova_config = questionary.text("Nova configuração:").ask()
    config.nova_config = nova_config
    config.save()
```

### Adicionar Suporte para Nova Linguagem/Versão

1. Adicione ao JSON `languages` na configuração
2. Crie função de atualização no `executor.py`
3. Aplique ao docker-compose.yml antes de executar

```python
# Exemplo: adicionar versão do Node.js ao Superleme
def _update_docker_compose_versions(cwd: str, docker_config: Optional[Dict] = None):
    # ... código existente PostgreSQL ...

    # Adicionar suporte Node.js
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

## 🪲 Debugging

### Verificar Configurações do Banco

```python
import sqlite3
conn = sqlite3.connect('src/data/aedificator.db')
cursor = conn.cursor()

# Ver todas as configs
cursor.execute('SELECT * FROM dockerconfiguration')
for row in cursor.fetchall():
    print(row)

# Ver paths
cursor.execute('SELECT * FROM paths')
for row in cursor.fetchall():
    print(row)
```

### Logs

Todos os comandos são salvos em `src/data/logs/` com formato:
```
{project_name}_{timestamp}.log
```

Sempre mostre o caminho do log ao usuário:
```python
console.print(f"Log: {log_filename}")
```

### Erros Comuns

**Erro: "no such table"**
- Banco de dados não foi inicializado
- Solução: Deletar `src/data/aedificator.db` e reiniciar

**Erro: Versão errada do PostgreSQL**
- docker-compose.yml não foi atualizado
- Verifique se `_update_docker_compose_versions()` está sendo chamado

**Erro: Logs não aparecem**
- Caminho do log dir está errado (deve ser `src/data/logs/`, não `logs/`)
- Verifique cálculo de `project_root`

**Erro: Saída não é em tempo real**
- `bufsize` deve ser 0
- Falta `sys.stdout.flush()`
- Variáveis de ambiente não configuradas

## 📝 Checklist para Modificações

Ao modificar o código, verifique:

- [ ] Todos os prints estão em PORTUGUÊS
- [ ] Nenhuma cor escura (dim/muted/gray) foi usada
- [ ] Caminhos são relativos ao arquivo, não `os.getcwd()`
- [ ] Logs são salvos em `src/data/logs/`
- [ ] Docker compose é atualizado antes de executar
- [ ] Saída é em tempo real (bufsize=0, flush)
- [ ] Flags verbose estão presentes (--verbose, --progress=plain)
- [ ] Configurações são salvas no banco de dados
- [ ] Erros são mostrados em vermelho com conteúdo do log
- [ ] Documentação foi atualizada se necessário

## 🔍 Análise de Código

Ao analisar código existente:

1. **Identifique o fluxo**: cli.py → main.py → menu.py → executor.py
2. **Verifique configurações**: main.py carrega do DB, passa para menu, menu passa para executor
3. **Trace execução**: menu escolhe comando → executor atualiza docker-compose → executor executa
4. **Logs**: executor cria timestamp → salva em src/data/logs/ → mostra caminho

## 💡 Dicas

- Use `console.print()` do Rich, não `print()` direto (exceto para output de comandos)
- Sempre teste com Docker ativo E desativo
- Verifique compatibilidade com light mode (sem cores escuras)
- Mantenha mensagens concisas e informativas
- Use regex para substituições em docker-compose.yml (mais robusto que string replace)
- Sempre faça backup do docker-compose.yml antes de modificar (ou use git)

## 🚀 Deployment

O projeto não tem deployment - é executado localmente:

```bash
source venv/bin/activate
python -m src.cli
```

Para distribuir:
1. Criar requirements.txt atualizado: `pip freeze > requirements.txt`
2. Documentar versões mínimas de Python/dependências
3. Testar em ambiente limpo

## 📚 Recursos

- **Peewee ORM**: http://docs.peewee-orm.com/
- **Rich Console**: https://rich.readthedocs.io/
- **Questionary**: https://questionary.readthedocs.io/
- **Docker Compose**: https://docs.docker.com/compose/

## ⚠️ Avisos Importantes

1. **NUNCA** use `os.getcwd()` para caminhos - sempre relativo ao arquivo
2. **SEMPRE** flush stdout para saída em tempo real
3. **SEMPRE** atualize docker-compose.yml antes de executar Docker
4. **SEMPRE** use português nas mensagens
5. **NUNCA** use cores escuras (dim, muted, gray)
6. **SEMPRE** mostre o comando Docker completo ao usuário quando usar Docker
7. **SEMPRE** salve logs em `src/data/logs/` com timestamp
8. **SEMPRE** mostre erros em vermelho com conteúdo do log

---

Este documento deve ser seguido por todos os agentes de IA trabalhando neste projeto.
