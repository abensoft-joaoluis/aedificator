"""
Main Docker manager that coordinates all Docker operations.
"""

import os
import json
from typing import Dict
from .. import console
from ..memory import DockerConfiguration
from .templates import DockerTemplates
from .operations import DockerOperations


class DockerManager:
    """Manages Docker image building and Dockerfile generation."""

    @staticmethod
    def load_config_from_db(project_name: str) -> Dict:
        """
        Load Docker configuration from database.

        Args:
            project_name: 'superleme' or 'sl_phoenix'

        Returns:
            Dictionary with configuration
        """
        try:
            config = DockerConfiguration.get(
                DockerConfiguration.project_name == project_name
            )
            return {
                "use_docker": config.use_docker,
                "postgres_version": config.postgres_version,
                "languages": config.languages,
                "compose_file": config.compose_file,
            }
        except:
            console.print(
                f"[warning]Configuração para {project_name} não encontrada no banco de dados[/warning]"
            )
            return {}

    @staticmethod
    def generate_superleme_dockerfile(
        output_path: str, project_name: str = "superleme"
    ):
        """
        Generate Dockerfile for Superleme (Zotonic) based on database configuration.

        Args:
            output_path: Path where to write the Dockerfile
            project_name: Project name in database (default: 'superleme')
        """
        # Load configuration from database
        config = DockerManager.load_config_from_db(project_name)
        if not config:
            console.print(
                "[error]Não foi possível carregar configuração do banco de dados[/error]"
            )
            return

        languages = json.loads(config.get("languages", "{}"))
        erlang_version = languages.get("erlang", "28")
        postgres_version = config.get("postgres_version", "17-alpine")

        # Generate content using template
        dockerfile_content = DockerTemplates.superleme_dockerfile(
            erlang_version, postgres_version
        )

        # Write Dockerfile
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(dockerfile_content)

        console.print(
            f"[success]Dockerfile do Superleme gerado em: {output_path}[/success]"
        )
        console.print(
            f"Versões configuradas: Erlang {erlang_version}, PostgreSQL {postgres_version}"
        )

    @staticmethod
    def generate_phoenix_dockerfile(output_path: str, project_name: str = "sl_phoenix"):
        """
        Generate Dockerfile for SL Phoenix based on database configuration.

        Args:
            output_path: Path where to write the Dockerfile
            project_name: Project name in database (default: 'sl_phoenix')
        """
        # Load configuration from database
        config = DockerManager.load_config_from_db(project_name)
        if not config:
            console.print(
                "[error]Não foi possível carregar configuração do banco de dados[/error]"
            )
            return

        languages = json.loads(config.get("languages", "{}"))
        elixir_version = languages.get("elixir", "1.19.4")
        erlang_version = languages.get("erlang", "28")
        node_version = languages.get("node", "25.2.1")

        # Generate content using template
        dockerfile_content = DockerTemplates.phoenix_dockerfile(
            elixir_version, erlang_version, node_version
        )

        # Write Dockerfile
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(dockerfile_content)

        console.print(
            f"[success]Dockerfile do SL Phoenix gerado em: {output_path}[/success]"
        )
        console.print(
            f"Versões configuradas: Elixir {elixir_version}, Erlang {erlang_version}, Node.js {node_version}"
        )

    @staticmethod
    def generate_superleme_phoenix_dockerfile(output_path: str):
        """
        Generate combined Dockerfile for Superleme + Phoenix based on database configurations.

        Args:
            output_path: Path where to write the Dockerfile
        """
        superleme_config = DockerManager.load_config_from_db("superleme")
        phoenix_config = DockerManager.load_config_from_db("sl_phoenix")

        if not superleme_config or not phoenix_config:
            console.print(
                "[error]Não foi possível carregar configurações de ambos os projetos[/error]"
            )
            return

        # Get versions from both configs
        superleme_langs = json.loads(superleme_config.get("languages", "{}"))
        phoenix_langs = json.loads(phoenix_config.get("languages", "{}"))

        erlang_version = superleme_langs.get("erlang", "28")
        elixir_version = phoenix_langs.get("elixir", "1.19.4")
        node_version = phoenix_langs.get("node", "25.2.1")

        # Generate content using template
        dockerfile_content = DockerTemplates.superleme_phoenix_dockerfile(
            erlang_version, elixir_version, node_version
        )

        # Write Dockerfile
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(dockerfile_content)

        console.print(
            f"[success]Dockerfile Superleme+Phoenix gerado em: {output_path}[/success]"
        )
        console.print(
            f"Versões configuradas: Erlang {erlang_version}, Elixir {elixir_version}, Node.js {node_version}"
        )

    @staticmethod
    def generate_docker_compose(output_path: str, stack_type: str = "full"):
        """
        Generate docker-compose.yml for different stack configurations.
        Loads configurations from database.

        Args:
            output_path: Path where to write docker-compose.yml
            stack_type: 'superleme', 'phoenix', or 'full'
        """
        # Load configurations from database
        superleme_config = DockerManager.load_config_from_db("superleme")
        postgres_version = superleme_config.get("postgres_version", "17-alpine")

        # Generate content using template
        compose_content = DockerTemplates.docker_compose(stack_type, postgres_version)

        # Write docker-compose.yml
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(compose_content)

        init_script_content = DockerTemplates.init_postgres_script()
        init_script_path = os.path.join(os.path.dirname(output_path), 'init-postgres.sh')
        with open(init_script_path, "w") as f:
            f.write(init_script_content)
        
        os.chmod(init_script_path, 0o755)
        console.print(
            f"[success]Script init-postgres.sh gerado em: {init_script_path}[/success]"
        )

        console.print(
            f"[success]docker-compose.yml ({stack_type}) gerado em: {output_path}[/success]"
        )
        console.print(f"Versão PostgreSQL: {postgres_version}")

        env_dir = os.path.dirname(output_path)
        env_file = os.path.join(env_dir, '.env')
        env_lines = {}
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.rstrip('\n').split('=', 1)
                            env_lines[k] = v
            except Exception:
                env_lines = {}

        env_lines['POSTGRES_VERSION'] = postgres_version
        try:
            langs = json.loads(superleme_config.get('languages', '{}'))
            if langs.get('erlang'):
                env_lines['ERLANG_VERSION'] = langs.get('erlang')
            if langs.get('elixir'):
                env_lines['ELIXIR_VERSION'] = langs.get('elixir')
            if langs.get('node'):
                env_lines['NODE_VERSION'] = langs.get('node')
        except Exception:
            pass

        with open(env_file, 'w') as f:
            for k, v in env_lines.items():
                f.write(f"{k}={v}\n")

        console.print(f"[success].env criado em: {env_file}[/success]")

    @staticmethod
    def build_image(
        dockerfile_path: str,
        image_name: str,
        image_tag: str,
        build_context: str,
        build_args: dict | None = None,
    ):
        """Build Docker image. Delegates to DockerOperations."""
        DockerOperations.build_image(
            dockerfile_path, image_name, image_tag, build_context, build_args
        )

    @staticmethod
    def push_image(image_name: str, image_tag: str, registry: str = None):
        """Push Docker image. Delegates to DockerOperations."""
        DockerOperations.push_image(image_name, image_tag, registry)

    @staticmethod
    def list_images():
        """List Docker images. Delegates to DockerOperations."""
        DockerOperations.list_images()

    @staticmethod
    def remove_image(image_name: str, image_tag: str, force: bool = False):
        """Remove Docker image. Delegates to DockerOperations."""
        DockerOperations.remove_image(image_name, image_tag, force)

    @staticmethod
    def prune_images(all_images: bool = False):
        """Prune unused Docker images. Delegates to DockerOperations."""
        DockerOperations.prune_images(all_images)
