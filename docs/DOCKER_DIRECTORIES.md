# Configuração de Diretórios Docker

Este documento descreve as configurações de diretórios dentro dos containers Docker para cada projeto gerenciado pelo Aedificator.

## 🗂️ Estrutura de Diretórios

### Superleme (Zotonic)

**Diretório de Trabalho no Container:** `/opt/zotonic`

O Zotonic é configurado para rodar dentro do container com:
- Código da aplicação montado em `/opt/zotonic`
- Binários executáveis em `/opt/zotonic/bin/`
- Configurações em `/opt/zotonic/config/`
- Módulos e sites em `/opt/zotonic/user/`

**Comandos Docker:**
```bash
docker compose run --rm --service-ports -w /opt/zotonic zotonic <comando>
```

**Exemplos:**
```bash
# Debug mode
docker compose run -w /opt/zotonic zotonic bin/zotonic debug

# Start server
docker compose run -w /opt/zotonic zotonic bin/zotonic start

# Compile
docker compose run -w /opt/zotonic zotonic make
```

**Configuração no docker-compose.yml:**
```yaml
services:
  zotonic:
    working_dir: /opt/zotonic
    volumes:
      - .:/opt/zotonic
    environment:
      - ZOTONIC_CONFIG_DIR=/opt/zotonic/config
```

### SL Phoenix (Phoenix/Elixir)

**Diretório de Trabalho no Container:** `/app`

Aplicações Phoenix/Elixir seguem a convenção de usar `/app` como diretório raiz no container:
- Código da aplicação montado em `/app`
- Mix configs em `/app/config/`
- Assets em `/app/assets/`
- Dependências instaladas em `/app/deps/`

**Comandos Docker:**
```bash
docker compose run --rm --service-ports -w /app app <comando>
```

**Exemplos:**
```bash
# Server de desenvolvimento
docker compose run -w /app app make server

# Setup inicial
docker compose run -w /app app make setup

# Testes
docker compose run -w /app app make test

# Build de produção
docker compose run -w /app app make build
```

**Configuração no docker-compose.yml:**
```yaml
services:
  app:
    working_dir: /app
    volumes:
      - .:/app
    environment:
      - MIX_ENV=dev
      - DATABASE_URL=postgres://postgres:postgres@db:15432/app_dev
```

### Extensão (Node.js/Plugin)

**Diretório de Trabalho no Container:** `/workspace` ou `/app`

Para extensões JavaScript/TypeScript:
- Código fonte em `/workspace` ou `/app`
- node_modules geralmente em volume separado
- Build output em `/workspace/dist` ou `/app/dist`

**Comandos Docker:**
```bash
docker compose run --rm -w /workspace extension <comando>
```

**Exemplos:**
```bash
# Desenvolvimento com watch
docker compose run -w /workspace extension make dev

# Build de produção
docker compose run -w /workspace extension make production
```

## 🔧 Configuração no Aedificator

O Aedificator detecta automaticamente o tipo de projeto baseado no caminho (cwd) e aplica o diretório de trabalho correto:

```python
# executor.py

if 'zotonic' in cwd:
    # Working dir: /opt/zotonic
    docker_cmd = f'docker compose run -w /opt/zotonic zotonic {command}'
    
elif 'phoenix' in cwd:
    # Working dir: /app
    docker_cmd = f'docker compose run -w /app app {command}'
    
else:
    # Working dir padrão
    docker_cmd = f'docker compose run app {command}'
```

## 📝 Boas Práticas

### 1. Volumes
Sempre monte o diretório local no diretório de trabalho do container:
```yaml
volumes:
  - .:/opt/zotonic  # Para Zotonic
  - .:/app          # Para Phoenix
```

### 2. Permissões
Configure o usuário do container para evitar problemas de permissão:
```yaml
user: "${UID}:${GID}"
```

### 3. Cache de Dependências
Use volumes nomeados para cache de dependências:
```yaml
volumes:
  - .:/app
  - deps:/app/deps           # Elixir deps
  - build:/app/_build        # Elixir build
  - node_modules:/app/node_modules  # Node modules
```

### 4. Variáveis de Ambiente
Configure caminhos específicos via environment:
```yaml
environment:
  - ZOTONIC_CONFIG_DIR=/opt/zotonic/config
  - MIX_HOME=/app/.mix
  - HEX_HOME=/app/.hex
```

## 🐛 Troubleshooting

### Problema: Comandos não encontram arquivos

**Causa:** Working directory incorreto dentro do container

**Solução:** Verifique se o `-w` (working directory) está configurado:
```bash
# ✅ CORRETO
docker compose run -w /opt/zotonic zotonic make

# ❌ ERRADO (usa / como working dir)
docker compose run zotonic make
```

### Problema: Permissões negadas

**Causa:** Container rodando como root, arquivos criados como root

**Solução:** Configure user no docker-compose.yml:
```yaml
services:
  zotonic:
    user: "${UID:-1000}:${GID:-1000}"
```

E execute com:
```bash
UID=$(id -u) GID=$(id -g) docker compose run ...
```

### Problema: Dependências não encontradas

**Causa:** Volume de dependências não persistente

**Solução:** Use volumes nomeados:
```yaml
volumes:
  deps:
    driver: local
  build:
    driver: local

services:
  app:
    volumes:
      - .:/app
      - deps:/app/deps
      - build:/app/_build
```

## 🔄 Atualizações Automáticas

O Aedificator atualiza automaticamente o `docker-compose.yml` antes de cada execução para garantir:
- Versões corretas de PostgreSQL, Erlang, Elixir
- Working directories apropriados
- Configurações de ambiente atualizadas

Isso é feito pela função `_update_docker_compose_versions()` no `executor.py`.

## 📚 Referências

- [Zotonic Docker Documentation](https://zotonic.com/docs/latest/deployment/docker.html)
- [Phoenix Docker Best Practices](https://hexdocs.pm/phoenix/deployment.html#containers)
- [Docker Compose Working Directory](https://docs.docker.com/compose/compose-file/compose-file-v3/#working_dir)

---

**Última atualização:** 15 de dezembro de 2025
