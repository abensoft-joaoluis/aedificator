import questionary
import os
import atexit
import signal
import sys
import json
import subprocess
import time
import threading
import secrets
import asyncio
from pathlib import Path
from typing import Optional

# Fix for Pyrlang split dependencies
try:
    from pyrlang import Node
    from term import Atom
    PYRLANG_AVAILABLE = True
except ImportError:
    PYRLANG_AVAILABLE = False

from aedificator import console
from aedificator.memory import DockerConfiguration
from aedificator.docker import DockerManager
from executor import Executor
from backup import BackupManager
from config import ConfigManager


class Menu:
    """Interactive menu system for project operations."""

    def __init__(self, superleme_path: str, sl_phoenix_path: str, extension_path: str, docker_configs: dict = None):
        self.superleme_path = superleme_path
        self.sl_phoenix_path = sl_phoenix_path
        self.extension_path = extension_path
        self.docker_configs = docker_configs or {}
        self.processes = []
        
        # Erlang/Pyrlang State
        self.py_node = None
        self.py_node_thread = None
        self.erlang_cookie = None
        self.node_name = "aedificator_ctl@localhost"

        # Register cleanup handlers
        atexit.register(self._cleanup_processes)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _ensure_cookie(self):
        """
        Ensures ~/.erlang.cookie exists, has correct permissions (400),
        and loads it into memory so Python and Erlang share the secret.
        """
        cookie_path = Path.home() / ".erlang.cookie"
        
        if not cookie_path.exists():
            console.print("[info]Gerando novo Erlang cookie...[/info]")
            # Generate a secure random cookie
            cookie_content = secrets.token_urlsafe(16)
            with open(cookie_path, 'w') as f:
                f.write(cookie_content)
        
        # Enforce permissions (Erlang requires 400 - read only by owner)
        try:
            os.chmod(cookie_path, 0o400)
        except Exception:
            pass # Windows or specific FS might ignore this
        
        with open(cookie_path, 'r') as f:
            self.erlang_cookie = f.read().strip()
            
        return self.erlang_cookie

    def _ensure_epmd(self):
        """Ensures the Erlang Port Mapper Daemon is running."""
        try:
            # Try to connect to EPMD port to see if it's running
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 4369))
            sock.close()
            
            if result != 0:
                console.print("[info]Iniciando EPMD (Erlang Port Mapper Daemon)...[/info]")
                # Start epmd in daemon mode
                subprocess.Popen(["epmd", "-daemon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(0.5) # Give it a moment to bind
        except Exception as e:
            console.print(f"[warning]Não foi possível verificar/iniciar EPMD: {e}[/warning]")

    def _start_pyrlang_node(self):
        """Starts the Python script as a hidden Erlang node in the background."""
        if not PYRLANG_AVAILABLE:
            return

        if self.py_node:
            return

        # 1. Ensure EPMD is running before anything else
        self._ensure_epmd()
        
        # 2. Ensure Cookie
        cookie = self._ensure_cookie()

        def run_node():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Initialize Python as a hidden node. 
                self.py_node = Node(node_name=self.node_name, cookie=cookie)
                self.py_node.run()
            except Exception as e:
                console.print(f"[error]Falha ao iniciar nó Pyrlang: {e}[/error]")

        # Run as daemon
        self.py_node_thread = threading.Thread(target=run_node, daemon=True)
        self.py_node_thread.start()
        
        time.sleep(0.2)
        
    def show_main_menu(self):
        """Display the main menu and handle user selection."""
        
        # Start the Erlang node immediately on boot
        if PYRLANG_AVAILABLE:
            self._start_pyrlang_node()
        
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
                        "Docker Images",
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
                elif choice == "Docker Images":
                    self.show_docker_images_menu()
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

        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
        use_docker = self.docker_configs.get('superleme', {}).get('use_docker', False)
        docker_config = self.docker_configs.get('superleme')

        if use_docker:
            console.print("[cyan]Modo Docker ativo[/cyan]")

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "1. Reconstruir imagem Docker",
                "2. Recompilar (Clean & Make)",
                "3. Executar (debug mode)",
                "4. Restaurar Backup do Banco de Dados",
                "5. Parar (stop)",
                "Voltar"
            ]
        ).ask()

        if choice == "1. Reconstruir imagem Docker":
            if use_docker:
                console.print("[info]Atualizando receitas Docker (overwrite)...[/info]")

                dockerfile_path = os.path.join(zotonic_root, "Dockerfile.superleme")
                compose_path = os.path.join(zotonic_root, "docker-compose.yml")

                DockerManager.generate_superleme_dockerfile(dockerfile_path)
                DockerManager.generate_docker_compose(compose_path, stack_type='superleme')

                console.print("[info]Garantindo configuração do site...[/info]")
                ConfigManager.ensure_superleme_config(zotonic_root, self.superleme_path)

                console.print("[info]Reconstruindo imagem Docker zotonic:latest...[/info]")
                Executor.run_command("docker compose build --no-cache zotonic", zotonic_root, background=False, use_docker=False)
            else:
                console.print("[warning]Docker não está ativo para este projeto.[/warning]")

        elif choice == "2. Recompilar (Clean & Make)":
            if use_docker:
                console.print("[info]Garantindo integridade dos arquivos Docker...[/info]")
                compose_path = os.path.join(zotonic_root, "docker-compose.yml")
                DockerManager.generate_docker_compose(compose_path, stack_type='superleme')

                console.print("[warning]Parando containers e removendo volumes Docker...[/warning]")
                Executor.run_command("docker compose down --volumes --remove-orphans", zotonic_root, background=False, use_docker=False)

                console.print("[info]Removendo volume zotonic_build explicitamente...[/info]")
                Executor.run_command("docker volume rm zotonic_build 2>/dev/null || true", zotonic_root, background=False, use_docker=False)

                console.print("[info]Criando volume com permissões corretas...[/info]")
                Executor.run_command("docker compose run --rm --user root zotonic bash -c 'mkdir -p _build && chown -R 1000:1000 _build'", zotonic_root, background=False, use_docker=False)

                console.print("[info]Executando clean build...[/info]")
                cmd = "docker compose run --rm zotonic bash -c 'make clean && make'"
            else:
                cmd = "rm -rf _build && make clean && make"
            Executor.run_command(cmd, zotonic_root, background=False, use_docker=False, docker_config=docker_config)

        elif choice == "3. Executar (debug mode)":
            if PYRLANG_AVAILABLE and self.py_node:
                console.print(f"[green]Conexão direta ativa: {self.node_name}[/green]")

            console.print("[info]Iniciando shell Zotonic... (Você pode digitar comandos aqui)[/info]")

            if use_docker:
                ConfigManager.ensure_superleme_config(zotonic_root, self.superleme_path)
                Executor.run_command("docker compose down --remove-orphans", zotonic_root, background=False, use_docker=False)
                cmd = "docker compose run --rm --service-ports zotonic bin/zotonic debug"
            else:
                cmd = "bin/zotonic debug"

            Executor.run_command(cmd, zotonic_root, background=False, use_docker=False, docker_config=docker_config)
            
        elif choice == "4. Restaurar Backup do Banco de Dados":
            if use_docker:
                console.print("[info]Restaurando backup do banco de dados...[/info]")
                BackupManager.restore_database(zotonic_root, use_docker)
            else:
                console.print("[warning]Restauração de backup disponível apenas no modo Docker.[/warning]")

        elif choice == "5. Parar (stop)":
            if use_docker:
                Executor.run_command("docker compose down", zotonic_root, background=False, use_docker=False)
            else:
                Executor.run_command("bin/zotonic stop", zotonic_root, background=False, use_docker=False)

    def show_sl_phoenix_menu(self):
        """Display SL Phoenix project menu."""
        console.print("\n[info]SL Phoenix[/info]")

        use_docker = self.docker_configs.get('sl_phoenix', {}).get('use_docker', False)
        docker_config = self.docker_configs.get('sl_phoenix')

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "Reconstruir imagem Docker",
                "Setup Completo",
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

        if choice == "Reconstruir imagem Docker":
            if use_docker:
                console.print("[info]Atualizando receitas Docker (overwrite)...[/info]")
                
                dockerfile_path = os.path.join(self.sl_phoenix_path, "Dockerfile.phoenix")
                compose_path = os.path.join(self.sl_phoenix_path, "docker-compose.phoenix.yml")
                
                DockerManager.generate_phoenix_dockerfile(dockerfile_path)
                DockerManager.generate_docker_compose(compose_path, stack_type='phoenix')

                console.print("[info]Reconstruindo imagem Docker sl_phoenix:latest...[/info]")
                Executor.run_command("docker compose build --no-cache phoenix", self.sl_phoenix_path, background=False, use_docker=False)
            else:
                console.print("[warning]Docker não está ativo para este projeto.[/warning]")
        elif choice == "Setup Completo":
            console.print("[info]Executando setup completo do Phoenix...[/info]")
            console.print("[info]1. Instalando dependências Elixir (mix deps.get)...[/info]")
            Executor.run_command("mix deps.get", self.sl_phoenix_path, background=False, use_docker=use_docker, docker_config=docker_config)
            
            console.print("[info]2. Compilando projeto (mix compile)...[/info]")
            Executor.run_command("mix compile", self.sl_phoenix_path, background=False, use_docker=use_docker, docker_config=docker_config)
            
            console.print("[info]3. Instalando assets Node.js (cd assets && npm install)...[/info]")
            assets_path = os.path.join(self.sl_phoenix_path, "assets")
            if os.path.exists(assets_path):
                Executor.run_command("npm install", assets_path, background=False, use_docker=use_docker, docker_config=docker_config)
            else:
                console.print("[warning]Diretório assets não encontrado, pulando npm install[/warning]")
            
            console.print("[info]4. Criando e migrando banco de dados...[/info]")
            Executor.run_command("mix ecto.setup", self.sl_phoenix_path, background=False, use_docker=use_docker, docker_config=docker_config)
            
            console.print("[success]Setup do Phoenix concluído![/success]")
        elif choice != "Voltar":
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
                "Baixar Novo Backup do Banco",
                "Limpar Processos Docker em Background",
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
        elif choice == "Baixar Novo Backup do Banco":
            BackupManager.download_backup()
        elif choice == "Limpar Processos Docker em Background":
            self._cleanup_docker_processes()

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

    def _cleanup_docker_processes(self):
        """Clean up Docker containers and processes running in background."""
        console.print("\n[info]Limpeza de Processos Docker[/info]")

        choice = questionary.select(
            "Escolha o tipo de limpeza:",
            choices=[
                "Listar containers em execução",
                "Parar todos os containers Docker Compose",
                "Parar e remover containers órfãos",
                "Limpeza completa (containers + volumes + networks)",
                "Voltar"
            ]
        ).ask()

        if choice == "Listar containers em execução":
            console.print("\n[info]Containers Docker em execução:[/info]")
            Executor.run_command("docker ps -a", os.path.expanduser("~"), background=False, use_docker=False)

        elif choice == "Parar todos os containers Docker Compose":
            console.print("\n[warning]Parando todos os containers Docker Compose...[/warning]")

            # Stop Superleme
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            if os.path.exists(os.path.join(zotonic_root, "docker-compose.yml")):
                console.print("[info]Parando containers do Superleme...[/info]")
                Executor.run_command("docker compose down", zotonic_root, background=False, use_docker=False)

            # Stop Phoenix
            if os.path.exists(os.path.join(self.sl_phoenix_path, "docker-compose.phoenix.yml")):
                console.print("[info]Parando containers do SL Phoenix...[/info]")
                Executor.run_command("docker compose -f docker-compose.phoenix.yml down", self.sl_phoenix_path, background=False, use_docker=False)

            console.print("[success]Containers parados com sucesso![/success]")

        elif choice == "Parar e remover containers órfãos":
            console.print("\n[warning]Removendo containers órfãos...[/warning]")

            # Clean Superleme
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            if os.path.exists(os.path.join(zotonic_root, "docker-compose.yml")):
                console.print("[info]Limpando containers órfãos do Superleme...[/info]")
                Executor.run_command("docker compose down --remove-orphans", zotonic_root, background=False, use_docker=False)

            # Clean Phoenix
            if os.path.exists(os.path.join(self.sl_phoenix_path, "docker-compose.phoenix.yml")):
                console.print("[info]Limpando containers órfãos do SL Phoenix...[/info]")
                Executor.run_command("docker compose -f docker-compose.phoenix.yml down --remove-orphans", self.sl_phoenix_path, background=False, use_docker=False)

            console.print("[success]Containers órfãos removidos![/success]")

        elif choice == "Limpeza completa (containers + volumes + networks)":
            confirm = questionary.confirm(
                "ATENÇÃO: Isso irá remover containers, volumes e networks. Continuar?",
                default=False
            ).ask()

            if confirm:
                console.print("\n[warning]Executando limpeza completa...[/warning]")

                # Clean Superleme
                zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
                if os.path.exists(os.path.join(zotonic_root, "docker-compose.yml")):
                    console.print("[info]Limpeza completa do Superleme...[/info]")
                    Executor.run_command("docker compose down --volumes --remove-orphans", zotonic_root, background=False, use_docker=False)

                # Clean Phoenix
                if os.path.exists(os.path.join(self.sl_phoenix_path, "docker-compose.phoenix.yml")):
                    console.print("[info]Limpeza completa do SL Phoenix...[/info]")
                    Executor.run_command("docker compose -f docker-compose.phoenix.yml down --volumes --remove-orphans", self.sl_phoenix_path, background=False, use_docker=False)

                # Prune unused networks
                console.print("[info]Removendo networks não utilizadas...[/info]")
                Executor.run_command("docker network prune -f", os.path.expanduser("~"), background=False, use_docker=False)

                console.print("[success]Limpeza completa concluída![/success]")
            else:
                console.print("[info]Limpeza cancelada.[/info]")

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

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        console.print("\n[warning]Sinal de interrupção recebido. Limpando processos...[/warning]")
        self._cleanup_processes()
        sys.exit(0)

    def show_docker_images_menu(self):
        """Display Docker Images management menu."""
        console.print("\n[info]Gerenciamento de Docker Images[/info]")

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "Gerar Dockerfiles",
                "Build de Imagens",
                "Push para Registry",
                "Listar Imagens Locais",
                "Remover Imagem",
                "Limpar Imagens Não Utilizadas",
                "Voltar"
            ]
        ).ask()

        if choice == "Gerar Dockerfiles":
            self._generate_dockerfiles_submenu()
        elif choice == "Build de Imagens":
            self._build_images_submenu()
        elif choice == "Push para Registry":
            self._push_images_submenu()
        elif choice == "Listar Imagens Locais":
            DockerManager.list_images()
        elif choice == "Remover Imagem":
            self._remove_image_submenu()
        elif choice == "Limpar Imagens Não Utilizadas":
            self._prune_images_submenu()

    def _generate_dockerfiles_submenu(self):
        """Submenu for generating Dockerfiles."""
        console.print("\n[info]Gerar Dockerfiles[/info]")

        choice = questionary.select(
            "Qual stack deseja gerar?",
            choices=[
                "Superleme (standalone)",
                "SL Phoenix (standalone)",
                "Stack Completo (Superleme + Phoenix)",
                "Voltar"
            ]
        ).ask()

        if choice == "Superleme (standalone)":
            # Get output path
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            dockerfile_path = os.path.join(zotonic_root, "Dockerfile.superleme")
            compose_path = os.path.join(zotonic_root, "docker-compose.superleme.yml")

            DockerManager.generate_superleme_dockerfile(dockerfile_path)
            DockerManager.generate_docker_compose(compose_path, stack_type='superleme')

        elif choice == "SL Phoenix (standalone)":
            dockerfile_path = os.path.join(self.sl_phoenix_path, "Dockerfile.phoenix")
            compose_path = os.path.join(self.sl_phoenix_path, "docker-compose.phoenix.yml")

            DockerManager.generate_phoenix_dockerfile(dockerfile_path)
            DockerManager.generate_docker_compose(compose_path, stack_type='phoenix')

        elif choice == "Stack Completo (Superleme + Phoenix)":
            # Generate in a common parent directory
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            parent_dir = os.path.dirname(zotonic_root)

            superleme_dockerfile = os.path.join(parent_dir, "Dockerfile.superleme")
            phoenix_dockerfile = os.path.join(parent_dir, "Dockerfile.phoenix")
            compose_path = os.path.join(parent_dir, "docker-compose.full-stack.yml")

            DockerManager.generate_superleme_dockerfile(superleme_dockerfile)
            DockerManager.generate_phoenix_dockerfile(phoenix_dockerfile)
            DockerManager.generate_docker_compose(compose_path, stack_type='full')

    def _build_images_submenu(self):
        """Submenu for building Docker images."""
        console.print("\n[info]Build de Imagens Docker[/info]")

        choice = questionary.select(
            "Qual imagem deseja buildar?",
            choices=[
                "Superleme",
                "SL Phoenix",
                "Ambos (Superleme + Phoenix)",
                "Voltar"
            ]
        ).ask()

        if choice == "Voltar":
            return

        # Ask for image tag
        image_tag = questionary.text(
            "Tag da imagem:",
            default="latest"
        ).ask()

        if choice == "Superleme":
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            dockerfile_path = os.path.join(zotonic_root, "Dockerfile.superleme")

            # Check if Dockerfile exists
            if not os.path.exists(dockerfile_path):
                console.print("[warning]Dockerfile não encontrado. Gerando...[/warning]")
                DockerManager.generate_superleme_dockerfile(dockerfile_path)

            # Load build args from DB config
            super_config = DockerManager.load_config_from_db("superleme")
            langs = json.loads(super_config.get('languages', '{}'))
            build_args = {
                'POSTGRES_VERSION': super_config.get('postgres_version'),
                'ERLANG_VERSION': langs.get('erlang')
            }

            DockerManager.build_image(dockerfile_path, "zotonic", image_tag, zotonic_root, build_args)

        elif choice == "SL Phoenix":
            dockerfile_path = os.path.join(self.sl_phoenix_path, "Dockerfile.phoenix")

            # Check if Dockerfile exists
            if not os.path.exists(dockerfile_path):
                console.print("[warning]Dockerfile não encontrado. Gerando...[/warning]")
                DockerManager.generate_phoenix_dockerfile(dockerfile_path)

            # Load build args for Phoenix
            phoenix_config = DockerManager.load_config_from_db("sl_phoenix")
            phoenix_langs = json.loads(phoenix_config.get('languages', '{}'))
            build_args = {
                'ELIXIR_VERSION': phoenix_langs.get('elixir'),
                'ERLANG_VERSION': phoenix_langs.get('erlang'),
                'NODE_VERSION': phoenix_langs.get('node')
            }
            DockerManager.build_image(dockerfile_path, "sl_phoenix", image_tag, self.sl_phoenix_path, build_args)

        elif choice == "Ambos (Superleme + Phoenix)":
            # Build Superleme
            zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))
            superleme_dockerfile = os.path.join(zotonic_root, "Dockerfile.superleme")

            if not os.path.exists(superleme_dockerfile):
                console.print("[warning]Dockerfile do Superleme não encontrado. Gerando...[/warning]")
                DockerManager.generate_superleme_dockerfile(superleme_dockerfile)

            # Build Superleme with args
            super_config = DockerManager.load_config_from_db("superleme")
            super_langs = json.loads(super_config.get('languages', '{}'))
            build_args = {'POSTGRES_VERSION': super_config.get('postgres_version'), 'ERLANG_VERSION': super_langs.get('erlang')}
            DockerManager.build_image(superleme_dockerfile, "zotonic", image_tag, zotonic_root, build_args)

            # Build Phoenix
            phoenix_dockerfile = os.path.join(self.sl_phoenix_path, "Dockerfile.phoenix")

            if not os.path.exists(phoenix_dockerfile):
                console.print("[warning]Dockerfile do Phoenix não encontrado. Gerando...[/warning]")
                DockerManager.generate_phoenix_dockerfile(phoenix_dockerfile)

            phoenix_config = DockerManager.load_config_from_db("sl_phoenix")
            phoenix_langs = json.loads(phoenix_config.get('languages', '{}'))
            build_args = {'ELIXIR_VERSION': phoenix_langs.get('elixir'), 'ERLANG_VERSION': phoenix_langs.get('erlang'), 'NODE_VERSION': phoenix_langs.get('node')}
            DockerManager.build_image(phoenix_dockerfile, "sl_phoenix", image_tag, self.sl_phoenix_path, build_args)

    def _push_images_submenu(self):
        """Submenu for pushing Docker images to registry."""
        console.print("\n[info]Push para Registry[/info]")

        # Ask for registry
        registry = questionary.text(
            "Registry URL (deixe vazio para Docker Hub):",
            default=""
        ).ask()

        registry = registry.strip() if registry else None

        choice = questionary.select(
            "Qual imagem deseja enviar?",
            choices=[
                "Superleme",
                "SL Phoenix",
                "Ambos",
                "Voltar"
            ]
        ).ask()

        if choice == "Voltar":
            return

        # Ask for image tag
        image_tag = questionary.text(
            "Tag da imagem:",
            default="latest"
        ).ask()

        if choice == "Superleme":
            DockerManager.push_image("superleme", image_tag, registry)
        elif choice == "SL Phoenix":
            DockerManager.push_image("sl-phoenix", image_tag, registry)
        elif choice == "Ambos":
            DockerManager.push_image("superleme", image_tag, registry)
            DockerManager.push_image("sl-phoenix", image_tag, registry)

    def _remove_image_submenu(self):
        """Submenu for removing Docker images."""
        console.print("\n[info]Remover Imagem Docker[/info]")

        # List images first
        DockerManager.list_images()

        choice = questionary.select(
            "Qual imagem deseja remover?",
            choices=[
                "Superleme",
                "SL Phoenix",
                "Voltar"
            ]
        ).ask()

        if choice == "Voltar":
            return

        # Ask for image tag
        image_tag = questionary.text(
            "Tag da imagem:",
            default="latest"
        ).ask()

        # Ask if force removal
        force = questionary.confirm(
            "Forçar remoção (mesmo se em uso)?",
            default=False
        ).ask()

        if choice == "Superleme":
            DockerManager.remove_image("zotonic", image_tag, force)
        elif choice == "SL Phoenix":
            DockerManager.remove_image("sl_phoenix", image_tag, force)

    def _prune_images_submenu(self):
        """Submenu for pruning unused Docker images."""
        console.print("\n[info]Limpar Imagens Não Utilizadas[/info]")

        all_images = questionary.confirm(
            "Remover TODAS as imagens não utilizadas (não apenas dangling)?",
            default=False
        ).ask()

        confirm = questionary.confirm(
            "Tem certeza? Esta operação não pode ser desfeita.",
            default=False
        ).ask()

        if confirm:
            DockerManager.prune_images(all_images)