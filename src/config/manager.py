import subprocess
import os
import json
from typing import Optional, Dict
from aedificator import console
from aedificator.paths import get_data_dir

class ConfigManager:
    """Manages project configuration files and Docker settings."""

    @staticmethod
    def update_docker_versions(cwd: str, docker_config: Optional[Dict] = None):
        """Update .env file with versions from database config."""
        if not docker_config:
            return

        try:
            postgres_version = docker_config.get('postgres_version')
            if not postgres_version:
                return

            env_file = os.path.join(cwd, '.env')
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
            
            # Update optional language versions
            try:
                langs = json.loads(docker_config.get('languages', '{}'))
                if langs.get('erlang'): env_lines['ERLANG_VERSION'] = langs.get('erlang')
                if langs.get('elixir'): env_lines['ELIXIR_VERSION'] = langs.get('elixir')
                if langs.get('node'):   env_lines['NODE_VERSION'] = langs.get('node')
            except Exception: pass

            with open(env_file, 'w') as f:
                for k, v in env_lines.items():
                    f.write(f"{k}={v}\n")

            console.print(f"[success].env atualizado: POSTGRES_VERSION={postgres_version}[/success]")

        except Exception as e:
            console.print(f"[warning]Erro no .env: {e}[/warning]")

    @staticmethod
    def ensure_superleme_config(zotonic_root, superleme_path):
        """Force-create the correct zotonic_site.config in the container using local template."""
        
        # Paths
        config_file_path = "/opt/zotonic/apps_user/superleme/priv/zotonic_site.config"
        
        # Locate the template relative to this script (src/config.py -> src/config/templates/superleme.config)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "config", "templates", "superleme.config")
        
        console.print(f"[info]Procurando template em: {template_path}[/info]")

        if not os.path.exists(template_path):
            console.print(f"[error]Template não encontrado! Crie o arquivo em: {template_path}[/error]")
            return

        try:
            console.print("[info]Escrevendo zotonic_site.config no container...[/info]")

            # We use 'cat' inside docker to receive the file content from stdin
            # This avoids mounting volumes or copying files manually
            write_cmd = f'docker compose run --rm -i zotonic bash -c "cat > {config_file_path}" < "{template_path}"'
            
            result = subprocess.run(write_cmd, shell=True, cwd=zotonic_root)

            if result.returncode == 0:
                console.print("[success]Configuração escrita com sucesso.[/success]")
            else:
                console.print("[error]Falha ao escrever arquivo no container.[/error]")

        except Exception as e:
            console.print(f"[error]Erro crítico ao gerar config: {e}[/error]")