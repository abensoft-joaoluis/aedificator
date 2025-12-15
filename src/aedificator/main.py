from pathing.main import Pathing
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
import questionary
import os
from . import console
from .memory import initialize_database, Paths, DockerConfiguration
from .menu import Menu

class Main():
    def __init__(self):
        self.console = console
        # Initialize database and create tables
        db = initialize_database()
        db.create_tables([Paths, DockerConfiguration])

        selected = Pathing.find_folders()
        is_first_install = not selected

        # Try auto-detection if not in database
        auto_detected = None
        if not selected or not all([selected.superleme_path, selected.sl_phoenix_path, selected.extension_path]):
            self.console.print("[info]Detectando pastas do projeto automaticamente...[/info]")
            auto_detected = Pathing.auto_detect_folders()
            detected_count = sum(1 for v in auto_detected.values() if v)
            if detected_count > 0:
                self.console.print(f"[success]Detectadas {detected_count} pastas[/success]")
                if auto_detected["superleme_path"]:
                    self.console.print(f"Superleme: {auto_detected['superleme_path']}")
                if auto_detected["sl_phoenix_path"]:
                    self.console.print(f"SL Phoenix: {auto_detected['sl_phoenix_path']}")
                if auto_detected["extension_path"]:
                    self.console.print(f"Extensão: {auto_detected['extension_path']}")
            else:
                self.console.print("[warning]Nenhuma pasta detectada automaticamente[/warning]")

        # Configure Docker for projects on first install
        docker_configs = {}
        if is_first_install:
            self.console.print("\n[info]Configuração de ambiente Docker[/info]")
            use_docker = questionary.confirm(
                "Deseja usar Docker para executar os projetos?",
                default=True
            ).ask()

            if use_docker:
                self.console.print("[success]Docker será configurado para os projetos[/success]")

                # Ask for Superleme/Zotonic versions
                self.console.print("\n[info]Configuração de versões - Superleme (Zotonic)[/info]")
                erlang_version_superleme = questionary.text(
                    "Versão do Erlang para Superleme:",
                    default="28"
                ).ask()
                postgres_version = questionary.text(
                    "Versão do PostgreSQL:",
                    default="17-alpine"
                ).ask()

                docker_configs['superleme'] = {
                    'use_docker': True,
                    'postgres_version': postgres_version,
                    'languages': f'{{"erlang": "{erlang_version_superleme}", "postgresql": "{postgres_version}"}}'
                }

                # Ask for SL Phoenix versions
                self.console.print("\n[info]Configuração de versões - SL Phoenix[/info]")
                use_docker_phoenix = questionary.confirm(
                    "Usar Docker para SL Phoenix também?",
                    default=False
                ).ask()

                elixir_version = questionary.text(
                    "Versão do Elixir:",
                    default="1.19.4"
                ).ask()
                erlang_version_phoenix = questionary.text(
                    "Versão do Erlang:",
                    default="28"
                ).ask()
                node_version = questionary.text(
                    "Versão do Node.js:",
                    default="25.2.1"
                ).ask()

                docker_configs['sl_phoenix'] = {
                    'use_docker': use_docker_phoenix,
                    'languages': f'{{"elixir": "{elixir_version}", "erlang": "{erlang_version_phoenix}", "node": "{node_version}"}}'
                }
            else:
                self.console.print("[info]Comandos serão executados diretamente no sistema[/info]")
                docker_configs['superleme'] = {'use_docker': False, 'languages': '{}'}
                docker_configs['sl_phoenix'] = {'use_docker': False, 'languages': '{}'}
        else:
            # Load existing Docker configurations
            try:
                superleme_config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
                docker_configs['superleme'] = {
                    'use_docker': superleme_config.use_docker,
                    'postgres_version': superleme_config.postgres_version,
                    'languages': superleme_config.languages
                }
            except:
                docker_configs['superleme'] = {'use_docker': False}

            try:
                phoenix_config = DockerConfiguration.get(DockerConfiguration.project_name == 'sl_phoenix')
                docker_configs['sl_phoenix'] = {
                    'use_docker': phoenix_config.use_docker,
                    'languages': phoenix_config.languages
                }
            except:
                docker_configs['sl_phoenix'] = {'use_docker': False}

        # Use database > auto-detection > user selection (in that priority order)
        self.superleme_folder = (
            (selected.superleme_path if selected else None) or
            (auto_detected["superleme_path"] if auto_detected else None) or
            Pathing.select_folder()
        )
        self.sl_phoenix_folder = (
            (selected.sl_phoenix_path if selected else None) or
            (auto_detected["sl_phoenix_path"] if auto_detected else None) or
            Pathing.select_folder()
        )
        self.extension_folder = (
            (selected.extension_path if selected else None) or
            (auto_detected["extension_path"] if auto_detected else None) or
            Pathing.select_folder()
        )

        # Update existing row or create new one (no duplicates)
        if selected:
            selected.superleme_path = self.superleme_folder
            selected.sl_phoenix_path = self.sl_phoenix_folder
            selected.extension_path = self.extension_folder
            selected.save()
            paths_memory = selected
        else:
            paths_memory = Paths.create(
                superleme_path=self.superleme_folder,
                sl_phoenix_path=self.sl_phoenix_folder,
                extension_path=self.extension_folder
            )

        # Save Docker configurations
        if is_first_install:
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_folder))
            compose_file = os.path.join(zotonic_root, "docker-compose.yml")

            # Save Superleme config
            DockerConfiguration.create(
                project_name='superleme',
                use_docker=docker_configs['superleme']['use_docker'],
                postgres_version=docker_configs['superleme'].get('postgres_version'),
                compose_file=compose_file if os.path.exists(compose_file) else None,
                languages=docker_configs['superleme'].get('languages')
            )

            # Save SL Phoenix config
            DockerConfiguration.create(
                project_name='sl_phoenix',
                use_docker=docker_configs['sl_phoenix']['use_docker'],
                languages=docker_configs['sl_phoenix'].get('languages')
            )

        # Initialize and show menu
        menu = Menu(
            superleme_path=self.superleme_folder,
            sl_phoenix_path=self.sl_phoenix_folder,
            extension_path=self.extension_folder,
            docker_configs=docker_configs
        )
        menu.show_main_menu()

    