"""
Docker template generation using Jinja2 files.
The module will render templates found in the `templates/` folder adjacent to this file.
"""

import os
from jinja2 import Environment, FileSystemLoader, select_autoescape


class DockerTemplates:
    """Generates Dockerfile / compose content by rendering Jinja2 templates."""

    @staticmethod
    def _load_template(template_name: str) -> str:
        tmpl_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(
            loader=FileSystemLoader(tmpl_dir),
            autoescape=select_autoescape(['j2'])
        )
        template = env.get_template(template_name)
        return template

    @staticmethod
    def superleme_dockerfile(erlang_version: str, postgres_version: str) -> str:
        """Render Superleme Dockerfile Jinja2 template."""
        template = DockerTemplates._load_template('superleme.Dockerfile.j2')
        return template.render(erlang_version=erlang_version, postgres_version=postgres_version)

    @staticmethod
    def phoenix_dockerfile(elixir_version: str, erlang_version: str, node_version: str) -> str:
        """Render Phoenix Dockerfile Jinja2 template."""
        template = DockerTemplates._load_template('phoenix.Dockerfile.j2')
        return template.render(elixir_version=elixir_version, erlang_version=erlang_version, node_version=node_version)

    @staticmethod
    def superleme_phoenix_dockerfile(erlang_version: str, elixir_version: str, node_version: str) -> str:
        """Render Superleme + Phoenix combined Dockerfile Jinja2 template."""
        template = DockerTemplates._load_template('superleme_phoenix.Dockerfile.j2')
        return template.render(erlang_version=erlang_version, elixir_version=elixir_version, node_version=node_version)

    @staticmethod
    def docker_compose(stack_type: str, postgres_version: str) -> str:
        """Render docker-compose Jinja2 template.

        Args:
            stack_type: one of 'superleme', 'phoenix', or 'full'
            postgres_version: version string (used to populate .env or for info)
        """
        template = DockerTemplates._load_template('docker-compose.yml.j2')
        context = {
            'stack_name': stack_type,
            'include_superleme': stack_type in ['superleme', 'full'],
            'include_phoenix': stack_type in ['phoenix', 'full'],
            'postgres_version': postgres_version,
        }
        return template.render(**context)

    @staticmethod
    def init_postgres_script() -> str:
        """Render PostgreSQL initialization script Jinja2 template."""
        template = DockerTemplates._load_template('init-postgres.sh.j2')
        return template.render()
