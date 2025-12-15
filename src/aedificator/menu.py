import questionary
import os
import atexit
import signal
import sys
from typing import Optional
from . import console
from .executor import Executor


class Menu:
    """Interactive menu system for project operations."""

    def __init__(self, superleme_path: str, sl_phoenix_path: str, extension_path: str):
        self.superleme_path = superleme_path
        self.sl_phoenix_path = sl_phoenix_path
        self.extension_path = extension_path
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

        choice = questionary.select(
            "Escolha uma operação:",
            choices=[
                "Executar (bin/zotonic debug)",
                "Iniciar (bin/zotonic start)",
                "Parar (bin/zotonic stop)",
                "Status (bin/zotonic status)",
                "Compilar (make)",
                "Voltar"
            ]
        ).ask()

        if choice == "Executar (bin/zotonic debug)":
            Executor.run_command("bin/zotonic debug", zotonic_root, background=False)
        elif choice == "Iniciar (bin/zotonic start)":
            Executor.run_command("bin/zotonic start", zotonic_root, background=False)
        elif choice == "Parar (bin/zotonic stop)":
            Executor.run_command("bin/zotonic stop", zotonic_root, background=False)
        elif choice == "Status (bin/zotonic status)":
            Executor.run_command("bin/zotonic status", zotonic_root, background=False)
        elif choice == "Compilar (make)":
            Executor.run_command("make", zotonic_root, background=False)

    def show_sl_phoenix_menu(self):
        """Display SL Phoenix project menu."""
        console.print("\n[info]SL Phoenix[/info]")

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
            Executor.run_make(target, self.sl_phoenix_path, background=False)

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
            Executor.run_make(target, self.extension_path, background=False)

    def show_combined_menu(self):
        """Display menu for running multiple projects simultaneously."""
        console.print("\n[info]Executar Múltiplos Projetos[/info]")

        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))

        choice = questionary.select(
            "Escolha uma combinação:",
            choices=[
                "Superleme + SL Phoenix (dev)",
                "SL Phoenix + Extensão (dev)",
                "Todos os 3 projetos (dev)",
                "Superleme + SL Phoenix (build)",
                "Custom",
                "Voltar"
            ]
        ).ask()

        if choice == "Superleme + SL Phoenix (dev)":
            commands = [
                ("bin/zotonic debug", zotonic_root),
                ("make server", self.sl_phoenix_path)
            ]
            new_processes = Executor.run_multiple(commands, background=True)
            self.processes.extend(new_processes)
            self._wait_for_processes()

        elif choice == "SL Phoenix + Extensão (dev)":
            commands = [
                ("make server", self.sl_phoenix_path),
                ("make dev", self.extension_path)
            ]
            new_processes = Executor.run_multiple(commands, background=True)
            self.processes.extend(new_processes)
            self._wait_for_processes()

        elif choice == "Todos os 3 projetos (dev)":
            commands = [
                ("bin/zotonic debug", zotonic_root),
                ("make server", self.sl_phoenix_path),
                ("make dev", self.extension_path)
            ]
            new_processes = Executor.run_multiple(commands, background=True)
            self.processes.extend(new_processes)
            self._wait_for_processes()

        elif choice == "Superleme + SL Phoenix (build)":
            commands = [
                ("make", zotonic_root),
                ("make build", self.sl_phoenix_path)
            ]
            Executor.run_multiple(commands, background=False)

        elif choice == "Custom":
            self.show_custom_combined()

    def show_custom_combined(self):
        """Allow user to select custom combination of projects."""
        zotonic_root = os.path.dirname(os.path.dirname(self.superleme_path))

        projects = questionary.checkbox(
            "Selecione os projetos para executar:",
            choices=[
                "Superleme",
                "SL Phoenix",
                "Extensão"
            ]
        ).ask()

        if not projects:
            return

        commands = []

        if "Superleme" in projects:
            cmd = questionary.text("Comando para Superleme:", default="bin/zotonic debug").ask()
            commands.append((cmd, zotonic_root))

        if "SL Phoenix" in projects:
            cmd = questionary.text("Comando para SL Phoenix:", default="make server").ask()
            commands.append((cmd, self.sl_phoenix_path))

        if "Extensão" in projects:
            cmd = questionary.text("Comando para Extensão:", default="make dev").ask()
            commands.append((cmd, self.extension_path))

        if commands:
            bg = questionary.confirm("Executar em background?", default=True).ask()
            new_processes = Executor.run_multiple(commands, background=bg)
            if bg:
                self.processes.extend(new_processes)
                self._wait_for_processes()

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
