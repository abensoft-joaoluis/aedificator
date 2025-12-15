import subprocess
import os
from typing import Optional, List
from . import console


class Executor:
    """Handles terminal command execution in project folders."""

    @staticmethod
    def _has_mise(cwd: str) -> bool:
        """Check if directory uses mise."""
        mise_files = ['.mise.toml', '.tool-versions', '.mise.local.toml']
        return any(os.path.exists(os.path.join(cwd, f)) for f in mise_files)

    @staticmethod
    def _trust_mise(cwd: str):
        """Trust mise configuration in directory."""
        try:
            subprocess.run(
                ['mise', 'trust'],
                cwd=cwd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except:
            pass

    @staticmethod
    def _wrap_with_mise(command: str, cwd: str) -> str:
        """Wrap command with mise if needed."""
        if Executor._has_mise(cwd):
            # Trust mise configuration first
            Executor._trust_mise(cwd)
            # Use mise exec to run command with proper environment
            # Use -- to separate mise options from the command
            mise_cmd = f'mise x -- {command}'
            return mise_cmd
        return command

    @staticmethod
    def run_command(command: str, cwd: str, background: bool = False) -> Optional[subprocess.Popen]:
        """
        Execute a command in the specified directory.

        Args:
            command: The command to execute
            cwd: Working directory path
            background: If True, run in background and return process

        Returns:
            Process object if background=True, None otherwise
        """
        if not os.path.exists(cwd):
            console.print(f"[error]Diretório não encontrado: {cwd}[/error]")
            return None

        # Wrap command with mise if directory uses it
        wrapped_command = Executor._wrap_with_mise(command, cwd)

        console.print(f"[info]Executando:[/info] {command}")
        console.print(f"[muted]Diretório: {cwd}[/muted]")
        if Executor._has_mise(cwd):
            console.print("[muted]Usando mise para gerenciar ambiente[/muted]")

        try:
            if background:
                process = subprocess.Popen(
                    wrapped_command,
                    shell=True,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    executable='/bin/bash'
                )
                console.print(f"[success]Processo iniciado em background (PID: {process.pid})[/success]")
                return process
            else:
                result = subprocess.run(
                    wrapped_command,
                    shell=True,
                    cwd=cwd,
                    check=False,
                    executable='/bin/bash'
                )
                if result.returncode == 0:
                    console.print("[success]Comando executado com sucesso[/success]")
                else:
                    console.print(f"[error]Comando falhou com código {result.returncode}[/error]")
                return None
        except Exception as e:
            console.print(f"[error]Erro ao executar comando: {e}[/error]")
            return None

    @staticmethod
    def run_multiple(commands: List[tuple], background: bool = True) -> List[subprocess.Popen]:
        """
        Execute multiple commands simultaneously.

        Args:
            commands: List of (command, cwd) tuples
            background: Run all in background

        Returns:
            List of process objects
        """
        processes = []
        console.print(f"[info]Executando {len(commands)} comando(s) simultaneamente...[/info]")

        for command, cwd in commands:
            process = Executor.run_command(command, cwd, background=background)
            if process:
                processes.append(process)

        if background and processes:
            console.print("[success]Todos os processos iniciados[/success]")
            console.print("[muted]Use Ctrl+C para parar todos os processos[/muted]")

        return processes

    @staticmethod
    def run_make(target: str, cwd: str, background: bool = False) -> Optional[subprocess.Popen]:
        """Execute a make target in the specified directory."""
        return Executor.run_command(f"make {target}", cwd, background)
