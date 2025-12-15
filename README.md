# Aedificator

Sistema de automação para gerenciar e executar múltiplos projetos (Superleme, SL Phoenix, e Extensão) com suporte a Docker e execução em tempo real.

## 🎯 O Que é e Por Que Existe

Aedificator é uma ferramenta de automação criada para resolver os desafios de desenvolver e manter múltiplos projetos simultaneamente, cada um com seu próprio stack tecnológico, configurações de banco de dados e requisitos de ambiente.

### O Problema

Desenvolvedores frequentemente enfrentam cenários onde precisam trabalhar com múltiplos projetos ao mesmo tempo:
- Um aplicativo **Zotonic (Erlang)** que requer PostgreSQL 17 e Erlang 27
- Um backend **Phoenix (Elixir)** que usa PostgreSQL 16 e Elixir 1.16
- Uma extensão/plugin com Node.js e suas próprias dependências

Cada projeto tem:
- **Versões específicas** de linguagens e bancos de dados
- **Comandos diferentes** para build, test, deploy
- **Configurações Docker** complexas e específicas
- **Requisitos de ambiente** que podem conflitar entre si

Gerenciar tudo isso manualmente é:
- ❌ Propenso a erros (esquecer de trocar versões)
- ❌ Tedioso (navegar entre pastas, lembrar comandos)
- ❌ Lento (configurar Docker manualmente a cada mudança)
- ❌ Frustrante (logs perdidos, saída não aparece em tempo real)

### A Solução

Aedificator centraliza tudo em uma interface única:

**1. Configuração Inteligente de Versões**
- Configure uma vez as versões de cada linguagem (Erlang, Elixir, PostgreSQL, Node.js)
- O sistema **atualiza automaticamente** os arquivos `docker-compose.yml` antes de cada execução
- Exemplo: Configurou PostgreSQL 17-alpine? O Aedificator encontra `postgres:16.2-alpine` no seu docker-compose.yml e substitui por `postgres:17-alpine` automaticamente

**2. Menu Centralizado**
- Um único ponto de entrada para todos os projetos
- Selecione o projeto e o comando desejado sem navegar entre pastas
- Comandos prontos (make, start, test, lint) para cada projeto

**3. Execução em Tempo Real**
- Veja a saída de comandos enquanto executam (não espere terminar para ver erros)
- Logs salvos automaticamente com timestamp para referência futura
- Erros destacados em vermelho para identificação rápida

**4. Docker Transparente**
- Opção de usar ou não Docker por projeto
- Quando ativo, envolve comandos automaticamente com `docker compose run`
- Flags verbose para debugging (--verbose, --progress=plain)
- Gerencia serviços e portas automaticamente

**5. Execução Múltipla**
- Execute vários projetos simultaneamente (ex: Superleme + SL Phoenix)
- Painel live mostrando o status de cada projeto
- Ideal para ambientes de desenvolvimento integrados

## 💡 Como Funciona

O Aedificator segue um fluxo simples mas poderoso:

1. **Inicialização**: Na primeira execução, detecta automaticamente as pastas dos projetos e pergunta as configurações
2. **Persistência**: Salva tudo em banco de dados SQLite (`src/data/aedificator.db`)
3. **Atualização**: Antes de executar comandos, atualiza os arquivos docker-compose.yml com as versões configuradas
4. **Execução**: Envolve comandos com Docker (se configurado) e executa com saída em tempo real
5. **Log**: Salva toda a saída em arquivos de log com timestamp para referência

**Exemplo de fluxo:**
```
Usuário seleciona "Superleme → Executar"
    ↓
Aedificator carrega configurações do banco (PostgreSQL 17, Erlang 27)
    ↓
Atualiza docker-compose.yml com as versões corretas
    ↓
Executa: docker compose run --service-ports zotonic bin/zotonic debug
    ↓
Mostra saída em tempo real + salva log em src/data/logs/superleme_20251215_132226.log
```

### Casos de Uso Reais

**Desenvolvimento Local vs. Docker**
- Algumas máquinas têm Erlang/Elixir instalados nativamente
- Outras preferem isolar tudo em Docker
- Aedificator suporta ambos: basta ativar/desativar Docker nas configurações

**Migrações de Banco de Dados**
- Projeto antigo: PostgreSQL 14
- Projeto novo: PostgreSQL 17
- Cada um precisa de sua versão específica
- Aedificator garante que cada projeto use a versão correta automaticamente

**Conflitos de Versão**
- Erlang 25 no Projeto A, Erlang 27 no Projeto B
- Impossível ter ambas versões ativas sem Docker
- Aedificator gerencia isso via containers isolados

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
