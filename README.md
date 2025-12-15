# Aedificator

Sistema de automação para gerenciar e executar múltiplos projetos (Superleme, SL Phoenix, e Extensão) com suporte a Docker e execução em tempo real.

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

### Flags Verbose

Todos os comandos Docker são executados com:
- `--ansi=never`: Remove códigos ANSI que causam buffering
- `--verbose`: Mostra logs detalhados
- `--progress=plain`: Progresso em texto plano sem animações

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

### Logs não aparecem
- Verifique se o diretório `src/data/logs/` existe
- O programa cria automaticamente, mas pode haver problema de permissões

### Docker não está usando versão correta
- Verifique a configuração no menu "Configurações"
- O programa atualiza o docker-compose.yml automaticamente antes de cada execução
- Verifique os logs para ver qual comando Docker foi executado

### Saída não aparece em tempo real
- O programa usa `bufsize=0` e `sys.stdout.flush()`
- Se ainda tiver problema, verifique se o comando não está bufferizando internamente

### Banco de dados corrompido
```bash
rm src/data/aedificator.db
# Reinicie o programa
```

## 📞 Suporte

Para suporte, entre em contato com a equipe Abensoft.
