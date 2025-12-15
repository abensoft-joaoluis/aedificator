import subprocess
import os
import threading
import time
from typing import Optional, List, Dict
from . import console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text


class Executor:
    """Handles terminal command execution in project folders."""

    @staticmethod
    def _has_docker_compose(cwd: str) -> bool:
        """Check if directory has docker-compose configuration."""
        compose_files = ['docker-compose.yml', 'docker-compose.yaml']
        return any(os.path.exists(os.path.join(cwd, f)) for f in compose_files)

    @staticmethod
    def _wrap_with_docker(command: str, cwd: str, use_docker: bool = True, docker_config: Optional[Dict] = None) -> str:
        """Wrap command with docker-compose exec if needed."""
        if use_docker and Executor._has_docker_compose(cwd):
            # Get the service name from docker config or default to 'zotonic'
            service = 'zotonic'  # Default for Superleme/Zotonic

            # Wrap command to execute inside Docker container
            docker_cmd = f'docker-compose exec {service} {command}'
            return docker_cmd
        return command

    @staticmethod
    def run_command(command: str, cwd: str, background: bool = False, use_docker: bool = False, docker_config: Optional[Dict] = None) -> Optional[subprocess.Popen]:
        """
        Execute a command in the specified directory.

        Args:
            command: The command to execute
            cwd: Working directory path
            background: If True, run in background and return process
            use_docker: If True, use Docker to execute commands
            docker_config: Optional Docker configuration dictionary

        Returns:
            Process object if background=True, None otherwise
        """
        if not os.path.exists(cwd):
            console.print(f"[error]Diretório não encontrado: {cwd}[/error]")
            return None

        # Wrap command with Docker if enabled
        wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

        console.print(f"[info]Executando:[/info] {command}")
        console.print(f"[muted]Diretório: {cwd}[/muted]")
        if use_docker and Executor._has_docker_compose(cwd):
            console.print("[muted]Usando Docker para executar comando[/muted]")

        # Determine project name for logging
        if 'zotonic' in cwd:
            project_name = 'superleme'
        elif 'phoenix' in cwd:
            project_name = 'sl_phoenix'
        elif 'plugin' in cwd:
            project_name = 'extension'
        else:
            project_name = os.path.basename(cwd)

        # Create log directory at project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Create log file
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_dir, f"{project_name}_{timestamp}.log")

        try:
            if background:
                log_file = open(log_filename, 'w')
                process = subprocess.Popen(
                    wrapped_command,
                    shell=True,
                    cwd=cwd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    executable='/bin/bash'
                )
                console.print(f"[success]Processo iniciado em background (PID: {process.pid})[/success]")
                console.print(f"[muted]Log: {log_filename}[/muted]")
                return process
            else:
                with open(log_filename, 'w') as log_file:
                    result = subprocess.run(
                        wrapped_command,
                        shell=True,
                        cwd=cwd,
                        check=False,
                        executable='/bin/bash',
                        stdout=log_file,
                        stderr=subprocess.STDOUT
                    )
                if result.returncode == 0:
                    console.print("[success]Comando executado com sucesso[/success]")
                else:
                    console.print(f"[error]Comando falhou com código {result.returncode}[/error]")
                console.print(f"[muted]Log: {log_filename}[/muted]")
                return None
        except Exception as e:
            console.print(f"[error]Erro ao executar comando: {e}[/error]")
            return None

    @staticmethod
    def run_multiple(commands: List[tuple], background: bool = True, docker_configs: Optional[Dict[str, Dict]] = None) -> List[subprocess.Popen]:
        """
        Execute multiple commands simultaneously with live output display.

        Args:
            commands: List of (command, cwd, use_docker) tuples
            background: Run all in background
            docker_configs: Optional dictionary of docker configurations by project

        Returns:
            List of process objects
        """
        if not background:
            # Run sequentially without live display for non-background
            processes = []
            for command_tuple in commands:
                command, cwd, use_docker = command_tuple
                docker_config = docker_configs.get(cwd) if docker_configs else None
                Executor.run_command(command, cwd, background=False, use_docker=use_docker, docker_config=docker_config)
            return processes

        console.print(f"[info]Executando {len(commands)} comando(s) simultaneamente...[/info]")

        # Start all processes
        process_info = []
        for command_tuple in commands:
            command, cwd, use_docker = command_tuple
            docker_config = docker_configs.get(cwd) if docker_configs else None

            # Wrap command with Docker if needed
            wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

            # Determine project name from cwd
            if 'zotonic' in cwd:
                project_name = 'Superleme'
            elif 'phoenix' in cwd:
                project_name = 'SL Phoenix'
            else:
                project_name = os.path.basename(cwd)

            process = subprocess.Popen(
                wrapped_command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                executable='/bin/bash',
                bufsize=1,
                universal_newlines=True
            )

            process_info.append({
                'process': process,
                'name': project_name,
                'command': command,
                'output': []
            })

        if process_info:
            console.print("[success]Todos os processos iniciados[/success]")
            console.print("[info]Exibindo output em tempo real... Pressione Ctrl+C para parar[/info]\n")

            # Display live output
            Executor._display_live_output(process_info)

        return [p['process'] for p in process_info]

    @staticmethod
    def _display_live_output(process_info: List[Dict]):
        """Display live output from multiple processes using Rich Layout."""
        # Create log directory at project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Create log files
        log_files = []
        for proc_info in process_info:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = os.path.join(log_dir, f"{proc_info['name'].replace(' ', '_')}_{timestamp}.log")
            log_file = open(log_filename, 'w')
            proc_info['log_file'] = log_file
            log_files.append(log_filename)
            console.print(f"[muted]Log para {proc_info['name']}: {log_filename}[/muted]")

        # Create layout
        layout = Layout()

        if len(process_info) == 2:
            layout.split_row(
                Layout(name="left"),
                Layout(name="right")
            )
        else:
            # For more than 2, stack them vertically
            layout.split_column(*[Layout(name=f"proc{i}") for i in range(len(process_info))])

        # Thread function to read process output
        def read_output(proc_info):
            try:
                for line in proc_info['process'].stdout:
                    line_stripped = line.rstrip()
                    proc_info['output'].append(line_stripped)
                    # Write to log file
                    proc_info['log_file'].write(line)
                    proc_info['log_file'].flush()
                    # Keep only last 50 lines in memory
                    if len(proc_info['output']) > 50:
                        proc_info['output'].pop(0)
            except:
                pass

        # Start reader threads
        threads = []
        for proc_info in process_info:
            thread = threading.Thread(target=read_output, args=(proc_info,), daemon=True)
            thread.start()
            threads.append(thread)

        try:
            with Live(layout, console=console, refresh_per_second=4) as live:
                while any(p['process'].poll() is None for p in process_info):
                    # Update each panel
                    for idx, proc_info in enumerate(process_info):
                        output_text = Text()

                        # Add output lines
                        for line in proc_info['output'][-30:]:  # Show last 30 lines
                            output_text.append(line + "\n")

                        # Check if process is still running
                        status = "Running" if proc_info['process'].poll() is None else f"Exited ({proc_info['process'].returncode})"
                        status_style = "green" if proc_info['process'].poll() is None else "red"

                        panel = Panel(
                            output_text,
                            title=f"[bold]{proc_info['name']}[/bold] - [{status_style}]{status}[/{status_style}]",
                            subtitle=f"[dim]{proc_info['command']}[/dim]",
                            border_style="cyan" if proc_info['process'].poll() is None else "red"
                        )

                        if len(process_info) == 2:
                            layout["left" if idx == 0 else "right"].update(panel)
                        else:
                            layout[f"proc{idx}"].update(panel)

                    time.sleep(0.25)

                # Show final state
                time.sleep(1)

        except KeyboardInterrupt:
            console.print("\n[warning]Interrompido pelo usuário[/warning]")
            # Kill all processes
            for proc_info in process_info:
                if proc_info['process'].poll() is None:
                    proc_info['process'].terminate()

        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=1)

        # Close log files
        for proc_info in process_info:
            if 'log_file' in proc_info:
                proc_info['log_file'].close()

        console.print("\n[success]Execução finalizada[/success]")
        console.print("[info]Logs salvos em:[/info]")
        for log_file in log_files:
            console.print(f"  {log_file}")

    @staticmethod
    def run_make(target: str, cwd: str, background: bool = False, use_docker: bool = False, docker_config: Optional[Dict] = None) -> Optional[subprocess.Popen]:
        """Execute a make target in the specified directory."""
        return Executor.run_command(f"make {target}", cwd, background, use_docker, docker_config)
