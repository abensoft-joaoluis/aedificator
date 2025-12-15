# Docker Package

Este pacote gerencia todas as operações relacionadas ao Docker no Aedificator.

## Estrutura

```
docker/
├── __init__.py       # Exporta DockerManager
├── manager.py        # Coordenador principal
├── templates.py      # Templates de Dockerfile e docker-compose
├── operations.py     # Operações Docker (build, push, list, etc)
└── README.md         # Este arquivo
```

## Arquivos

### `manager.py`
Coordenador principal que:
- Carrega configurações do banco de dados
- Gera Dockerfiles customizados
- Gera docker-compose.yml
- Delega operações para `operations.py`

### `templates.py`
Contém templates para:
- **Dockerfile Superleme**: Erlang + PostgreSQL
- **Dockerfile Phoenix**: Elixir + Erlang + Node.js (multi-stage)
- **docker-compose.yml**: Stacks (standalone ou completo)

### `operations.py`
Operações Docker:
- `build_image()`: Build de imagens
- `push_image()`: Push para registry
- `list_images()`: Listar imagens locais
- `remove_image()`: Remover imagem específica
- `prune_images()`: Limpar imagens não utilizadas

## Uso

```python
from .docker import DockerManager

# Gerar Dockerfiles (usa configurações do DB)
DockerManager.generate_superleme_dockerfile("/path/to/Dockerfile.superleme")
DockerManager.generate_phoenix_dockerfile("/path/to/Dockerfile.phoenix")

# Gerar docker-compose.yml
DockerManager.generate_docker_compose("/path/to/docker-compose.yml", stack_type='full')

# Build
DockerManager.build_image("Dockerfile.superleme", "superleme", "latest", "/build/context")

# Push
DockerManager.push_image("superleme", "latest", registry="myregistry.com")

# List
DockerManager.list_images()

# Remove
DockerManager.remove_image("superleme", "latest", force=False)

# Prune
DockerManager.prune_images(all_images=False)
```

## Integração com Banco de Dados

Todas as versões são carregadas automaticamente do banco de dados:

```python
config = DockerManager.load_config_from_db('superleme')
# Returns:
# {
#   'use_docker': True,
#   'postgres_version': '17-alpine',
#   'languages': '{"erlang": "28", "postgresql": "17-alpine"}',
#   'compose_file': '/path/to/docker-compose.yml'
# }
```

## Customização

Para adicionar novo projeto:

1. **Criar template** em `templates.py`:
```python
@staticmethod
def my_project_dockerfile(version: str) -> str:
    return f"""FROM base:{version}
    ...
    """
```

2. **Adicionar método** em `manager.py`:
```python
@staticmethod
def generate_my_project_dockerfile(output_path: str):
    config = DockerManager.load_config_from_db('my_project')
    content = DockerTemplates.my_project_dockerfile(config['version'])
    # Write to file...
```

3. **Adicionar ao menu** em `menu.py`

## Saída em Tempo Real

Todos os comandos Docker usam `Executor.run_command()` para mostrar saída em tempo real:

```python
DockerOperations.build_image(...)
# Você verá:
# - Download de layers
# - Build steps
# - Progresso em tempo real
```

## Logs

Todos os comandos Docker são salvos em `src/data/logs/` com timestamp.

## Observações

- Templates são gerados dinamicamente com versões do DB
- Multi-stage builds para Phoenix (otimização)
- Health checks em docker-compose
- Suporte para registry customizado
- Force removal de imagens em uso
- Prune seletivo (dangling vs all unused)
