import questionary
import os
import atexit
import signal
import sys
import json
from typing import Optional
from . import console
from .executor import Executor
from .memory import DockerConfiguration


class Menu:
    """Interactive menu system for project operations."""

    def __init__(self, superleme_path: str, sl_phoenix_path: str, extension_path: str, docker_configs: dict = None):
        self.superleme_path = superleme_path
        self.sl_phoenix_path = sl_phoenix_path
        self.extension_path = extension_path
        self.docker_configs = docker_configs or {}
        self.processes = []

        # Register cleanup handlers
        atexit.register(self._cleanup_processes)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def show_main_menu(self):
        """Display the main menu and handle user selection."""
        try:
            while True:
                console.print("\n[info]Menu Principal[/info]")

                choice = questionary.select(
                    "Escolha uma categoria:",
                    choices=[
                        "Superleme",
                        "SL Phoenix",
                        "Extensão",
                        "Executar Múltiplos",
                        "Configurações",
                        "Sair"
                    ]
                ).ask()

                if choice == "Superleme":
                    self.show_superleme_menu()
                elif choice == "SL Phoenix":
                    self.show_sl_phoenix_menu()
                elif choice == "Extensão":
                    self.show_extension_menu()
                elif choice == "Executar Múltiplos":
                    self.show_combined_menu()
                elif choice == "Configurações":
                    self.show_settings_menu()
                elif choice == "Sair":
                    console.print("[info]Saindo...[/info]")
                    self._cleanup_processes()
                    break
        except KeyboardInterrupt:
            console.print("\n[warning]Interrompido pelo usuário[/warning]")
            self._cleanup_processes()

    def show_superleme_menu(self):
        """Display Superleme project menu."""
        console.print("\n[info]Superleme[/info]")

        # Navigate to zotonic root (parent of apps_user/superleme)
        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
        use_docker = self.docker_configs.get('superleme', {}).get('use_docker', False)
        docker_config = self.docker_configs.get('superleme')

        if use_docker:
            console.print("Modo Docker ativo - usando run.sh")

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "Executar (debug mode)",
                "Iniciar (start)",
                "Parar (stop)",
                "Status",
                "Compilar (make)",
                "Voltar"
            ]
        ).ask()

        # Use different commands for Docker vs native
        if choice == "Executar (debug mode)":
            cmd = "./run.sh" if use_docker else "bin/zotonic debug"
            Executor.run_command(cmd, zotonic_root, background=False, use_docker=use_docker, docker_config=docker_config)
        elif choice == "Iniciar (start)":
            cmd = "./run.sh" if use_docker else "bin/zotonic start"
            Executor.run_command(cmd, zotonic_root, background=False, use_docker=use_docker, docker_config=docker_config)
        elif choice == "Parar (stop)":
            if use_docker:
                console.print("[warning]Para parar Docker, use: docker compose down[/warning]")
            else:
                Executor.run_command("bin/zotonic stop", zotonic_root, background=False, use_docker=False)
        elif choice == "Status":
            cmd = "bin/zotonic status" if not use_docker else "./run.sh"
            Executor.run_command(cmd, zotonic_root, background=False, use_docker=use_docker, docker_config=docker_config)
        elif choice == "Compilar (make)":
            Executor.run_command("make", zotonic_root, background=False, use_docker=use_docker, docker_config=docker_config)

    def show_sl_phoenix_menu(self):
        """Display SL Phoenix project menu."""
        console.print("\n[info]SL Phoenix[/info]")

        use_docker = self.docker_configs.get('sl_phoenix', {}).get('use_docker', False)
        docker_config = self.docker_configs.get('sl_phoenix')

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "make server",
                "make setup",
                "make install",
                "make clean",
                "make test",
                "make lint",
                "make format",
                "make assets",
                "Voltar"
            ]
        ).ask()

        if choice != "Voltar":
            target = choice.replace("make ", "")
            Executor.run_make(target, self.sl_phoenix_path, background=False, use_docker=use_docker, docker_config=docker_config)

    def show_extension_menu(self):
        """Display Extension project menu."""
        console.print("\n[info]Extensão[/info]")

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "make dev",
                "make watch",
                "make build",
                "make production",
                "make lint",
                "make test",
                "make clean",
                "make install",
                "Voltar"
            ]
        ).ask()

        if choice != "Voltar":
            target = choice.replace("make ", "")
            # Extension doesn't use Docker
            Executor.run_make(target, self.extension_path, background=False, use_docker=False)

    def show_combined_menu(self):
        """Display menu for running multiple projects simultaneously."""
        console.print("\n[info]Executar Múltiplos Projetos[/info]")

        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
        superleme_use_docker = self.docker_configs.get('superleme', {}).get('use_docker', False)
        phoenix_use_docker = self.docker_configs.get('sl_phoenix', {}).get('use_docker', False)

        choice = questionary.select(
            "Escolha uma combinação:",
            choices=[
                "Superleme + SL Phoenix (dev)",
                "Superleme + SL Phoenix (build)",
                "Custom",
                "Voltar"
            ]
        ).ask()

        if choice == "Superleme + SL Phoenix (dev)":
            # Use ./run.sh for Docker, bin/zotonic debug for native
            superleme_cmd = "./run.sh" if superleme_use_docker else "bin/zotonic debug"
            commands = [
                (superleme_cmd, zotonic_root, superleme_use_docker),
                ("make server", self.sl_phoenix_path, phoenix_use_docker)
            ]
            new_processes = Executor.run_multiple(commands, background=True, docker_configs=self.docker_configs)
            self.processes.extend(new_processes)

        elif choice == "Superleme + SL Phoenix (build)":
            commands = [
                ("make", zotonic_root, superleme_use_docker),
                ("make build", self.sl_phoenix_path, phoenix_use_docker)
            ]
            Executor.run_multiple(commands, background=False, docker_configs=self.docker_configs)

        elif choice == "Custom":
            self.show_custom_combined()

    def show_custom_combined(self):
        """Allow user to select custom combination of projects."""
        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
        superleme_use_docker = self.docker_configs.get('superleme', {}).get('use_docker', False)
        phoenix_use_docker = self.docker_configs.get('sl_phoenix', {}).get('use_docker', False)

        projects = questionary.checkbox(
            "Selecione os projetos para executar:",
            choices=[
                "Superleme",
                "SL Phoenix"
            ]
        ).ask()

        if not projects:
            return

        commands = []

        if "Superleme" in projects:
            default_cmd = "./run.sh" if superleme_use_docker else "bin/zotonic debug"
            cmd = questionary.text("Comando para Superleme:", default=default_cmd).ask()
            commands.append((cmd, zotonic_root, superleme_use_docker))

        if "SL Phoenix" in projects:
            cmd = questionary.text("Comando para SL Phoenix:", default="make server").ask()
            commands.append((cmd, self.sl_phoenix_path, phoenix_use_docker))

        if commands:
            bg = questionary.confirm("Executar em background?", default=True).ask()
            new_processes = Executor.run_multiple(commands, background=bg, docker_configs=self.docker_configs)
            if bg:
                self.processes.extend(new_processes)

    def show_settings_menu(self):
        """Display settings menu for configuration."""
        console.print("\n[info]Configurações[/info]")

        # Show current Docker status
        superleme_docker = self.docker_configs.get('superleme', {}).get('use_docker', False)
        phoenix_docker = self.docker_configs.get('sl_phoenix', {}).get('use_docker', False)
        console.print(f"Docker Superleme: {'[green]Ativo[/green]' if superleme_docker else '[red]Inativo[/red]'}")
        console.print(f"Docker SL Phoenix: {'[green]Ativo[/green]' if phoenix_docker else '[red]Inativo[/red]'}")

        choice = questionary.select(
            "O que deseja configurar?",
            choices=[
                "Versões de Linguagens - Superleme",
                "Versões de Linguagens - SL Phoenix",
                "Configurações Docker - Superleme",
                "Configurações Docker - SL Phoenix",
                "Voltar"
            ]
        ).ask()

        if choice == "Versões de Linguagens - Superleme":
            self._configure_superleme_versions()
        elif choice == "Versões de Linguagens - SL Phoenix":
            self._configure_phoenix_versions()
        elif choice == "Configurações Docker - Superleme":
            self._configure_superleme_docker()
        elif choice == "Configurações Docker - SL Phoenix":
            self._configure_phoenix_docker()

    def _configure_superleme_versions(self):
        """Configure language versions for Superleme."""
        console.print("\n[info]Configuração de Versões - Superleme[/info]")

        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
            current_langs = json.loads(config.languages) if config.languages else {}
        except:
            current_langs = {}

        erlang_version = questionary.text(
            "Versão do Erlang:",
            default=current_langs.get('erlang', '28')
        ).ask()

        postgres_version = questionary.text(
            "Versão do PostgreSQL:",
            default=current_langs.get('postgresql', '17-alpine')
        ).ask()

        # Update database
        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
            config.languages = json.dumps({"erlang": erlang_version, "postgresql": postgres_version})
            config.postgres_version = postgres_version
            config.save()

            # Update in-memory config
            self.docker_configs['superleme']['languages'] = config.languages
            self.docker_configs['superleme']['postgres_version'] = postgres_version

            console.print("[success]Versões atualizadas com sucesso![/success]")
        except Exception as e:
            console.print(f"[error]Erro ao atualizar versões: {e}[/error]")

    def _configure_phoenix_versions(self):
        """Configure language versions for SL Phoenix."""
        console.print("\n[info]Configuração de Versões - SL Phoenix[/info]")

        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'sl_phoenix')
            current_langs = json.loads(config.languages) if config.languages else {}
        except:
            current_langs = {}

        elixir_version = questionary.text(
            "Versão do Elixir:",
            default=current_langs.get('elixir', '1.19.4')
        ).ask()

        erlang_version = questionary.text(
            "Versão do Erlang:",
            default=current_langs.get('erlang', '28')
        ).ask()

        node_version = questionary.text(
            "Versão do Node.js:",
            default=current_langs.get('node', '25.2.1')
        ).ask()

        # Update database
        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'sl_phoenix')
            config.languages = json.dumps({
                "elixir": elixir_version,
                "erlang": erlang_version,
                "node": node_version
            })
            config.save()

            # Update in-memory config
            self.docker_configs['sl_phoenix']['languages'] = config.languages

            console.print("[success]Versões atualizadas com sucesso![/success]")
        except Exception as e:
            console.print(f"[error]Erro ao atualizar versões: {e}[/error]")

    def _configure_superleme_docker(self):
        """Configure Docker settings for Superleme."""
        console.print("\n[info]Configuração Docker - Superleme[/info]")

        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
            current_use_docker = config.use_docker
        except:
            current_use_docker = False

        use_docker = questionary.confirm(
            "Usar Docker para executar Superleme?",
            default=current_use_docker
        ).ask()

        # Update database
        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'superleme')
            config.use_docker = use_docker
            config.save()

            # Update in-memory config
            self.docker_configs['superleme']['use_docker'] = use_docker

            console.print("[success]Configuração Docker atualizada![/success]")
        except Exception as e:
            console.print(f"[error]Erro ao atualizar configuração: {e}[/error]")

    def _configure_phoenix_docker(self):
        """Configure Docker settings for SL Phoenix."""
        console.print("\n[info]Configuração Docker - SL Phoenix[/info]")

        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'sl_phoenix')
            current_use_docker = config.use_docker
        except:
            current_use_docker = False

        use_docker = questionary.confirm(
            "Usar Docker para executar SL Phoenix?",
            default=current_use_docker
        ).ask()

        # Update database
        try:
            config = DockerConfiguration.get(DockerConfiguration.project_name == 'sl_phoenix')
            config.use_docker = use_docker
            config.save()

            # Update in-memory config
            self.docker_configs['sl_phoenix']['use_docker'] = use_docker

            console.print("[success]Configuração Docker atualizada![/success]")
        except Exception as e:
            console.print(f"[error]Erro ao atualizar configuração: {e}[/error]")

    def _wait_for_processes(self):
        """Wait for background processes to complete or user interrupt."""
        if not self.processes:
            return

        try:
            console.print("\n[info]Processos executando... Pressione Ctrl+C para parar[/info]")
            for process in self.processes:
                process.wait()
            # Clear completed processes
            self.processes.clear()
            console.print("[success]Todos os processos finalizaram[/success]")
        except KeyboardInterrupt:
            console.print("\n[warning]Parando todos os processos...[/warning]")
            self._cleanup_processes()
            console.print("[success]Processos parados[/success]")

    def _cleanup_processes(self):
        """Terminate all running background processes."""
        if not self.processes:
            return

        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    try:
                        console.print(f"[warning]Terminando processo PID {process.pid}...[/warning]")
                    except:
                        pass  # Console might be gone during shutdown
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except:
                        # Force kill if terminate doesn't work
                        process.kill()
            except Exception:
                pass  # Ignore errors during cleanup

        self.processes.clear()

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        console.print("\n[warning]Sinal de interrupção recebido. Limpando processos...[/warning]")
        self._cleanup_processes()
        sys.exit(0)
