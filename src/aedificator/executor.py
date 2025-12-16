import subprocess
import os
import threading
import time
import sys
import re
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
    def _update_docker_compose_versions(cwd: str, docker_config: Optional[Dict] = None):
        """Update docker-compose.yml with versions from database config."""
        if not docker_config:
            return

        compose_file = os.path.join(cwd, 'docker-compose.yml')
        if not os.path.exists(compose_file):
            compose_file = os.path.join(cwd, 'docker-compose.yaml')
            if not os.path.exists(compose_file):
                return

        try:
            # Read the docker-compose file
            with open(compose_file, 'r') as f:
                content = f.read()

            # Update PostgreSQL version if configured
            postgres_version = docker_config.get('postgres_version')
            if postgres_version:
                # Match patterns like "postgres:16.2-alpine" or "postgres:17-alpine"
                content = re.sub(
                    r'postgres:[0-9]+(\.[0-9]+)?(-[a-zA-Z0-9]+)?',
                    f'postgres:{postgres_version}',
                    content
                )
                console.print(f"[success]Versão do PostgreSQL atualizada para: {postgres_version}[/success]")

            # Write back the updated content
            with open(compose_file, 'w') as f:
                f.write(content)

        except Exception as e:
            console.print(f"[warning]Não foi possível atualizar docker-compose.yml: {e}[/warning]")

    @staticmethod
    def _wrap_with_docker(command: str, cwd: str, use_docker: bool = True, docker_config: Optional[Dict] = None) -> str:
        """Wrap command with docker-compose if needed."""
        if use_docker and Executor._has_docker_compose(cwd):
            # For Zotonic, use docker compose run instead of exec
            # because we need to start the service, not execute in running container
            if 'zotonic' in cwd:
                # Use docker compose run with the command
                # Set NO_PROXY to avoid proxy issues
                # Add verbose flags for better debugging
                # --ansi=never prevents ANSI codes that can cause buffering
                # stdbuf -o0 -e0 forces unbuffered output
                # -w sets working directory inside container to /opt/zotonic
                # --entrypoint="" bypasses the zotonic entrypoint for direct commands like make
                if command.startswith('make') or command.startswith('bash') or command.startswith('sh') or command.startswith('mise'):
                    # For build commands, bypass entrypoint and run directly
                    # Add NO_PROXY and HEX_MIRROR for network issues
                    # Add SHELL=/bin/bash for erlexec compatibility
                    docker_cmd = f'NO_PROXY=* stdbuf -o0 -e0 docker compose --ansi=never --verbose --progress=plain -f docker-compose.yml run --rm --entrypoint="" -w /opt/zotonic -e NO_PROXY=* -e http_proxy= -e https_proxy= -e SHELL=/bin/bash zotonic {command}'
                else:
                    # For zotonic commands, use normal entrypoint
                    # Add SHELL=/bin/bash for erlexec compatibility
                    docker_cmd = f'stdbuf -o0 -e0 docker compose --ansi=never --verbose --progress=plain -f docker-compose.yml run --rm --service-ports -w /opt/zotonic -e SHELL=/bin/bash zotonic {command}'
            elif 'phoenix' in cwd:
                # For Phoenix, use docker compose run with proper working directory
                # Phoenix apps typically expect to be in /app directory inside container
                # Add SHELL=/bin/bash for compatibility
                docker_cmd = f'stdbuf -o0 -e0 docker compose --ansi=never --verbose --progress=plain -f docker-compose.yml run --rm --service-ports -w /app -e SHELL=/bin/bash app {command}'
            else:
                # For other services, use exec
                service = 'app'  # Generic service name
                docker_cmd = f'stdbuf -o0 -e0 docker-compose --ansi=never --verbose exec {service} {command}'
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

        # Update docker-compose.yml with versions from database before running
        if use_docker and Executor._has_docker_compose(cwd):
            Executor._update_docker_compose_versions(cwd, docker_config)

        # Wrap command with Docker if enabled
        wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

        console.print(f"[info]Executando:[/info] {command}")
        console.print(f"Diretório: {cwd}")
        if use_docker and Executor._has_docker_compose(cwd):
            console.print("Usando Docker para executar comando")
            console.print(f"Comando Docker completo: {wrapped_command}")
            console.print("\n" + "="*80)
            console.print("[info]Saída do comando (verbose):[/info]")
            console.print("="*80 + "\n")

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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "data", "logs")
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
                console.print(f"Log: {log_filename}")
                return process
            else:
                # Run command with real-time output to console and log file
                with open(log_filename, 'w', buffering=1) as log_file:
                    # Set environment variables to force unbuffered output
                    env = os.environ.copy()
                    env['PYTHONUNBUFFERED'] = '1'
                    env['DOCKER_BUILDKIT_PROGRESS'] = 'plain'
                    env['BUILDKIT_PROGRESS'] = 'plain'
                    env['COMPOSE_DOCKER_CLI_BUILD'] = '1'

                    # Run command directly without script wrapper
                    # The stdbuf in the docker command handles unbuffered output
                    process = subprocess.Popen(
                        wrapped_command,
                        shell=True,
                        cwd=cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        executable='/bin/bash',
                        bufsize=1,  # line buffered
                        encoding='utf-8',
                        errors='replace',  # Replace invalid UTF-8 bytes with '?' instead of crashing
                        env=env
                    )

                    # Read and print output in real-time
                    console.print("[info]Aguardando saída do comando...[/info]")

                    line_count = 0
                    try:
                        for line in process.stdout:
                            line_count += 1
                            try:
                                # Remove carriage returns and ensure proper line endings
                                # Strip \r to prevent diagonal output
                                line = line.replace('\r\n', '\n').replace('\r', '\n')
                                # Ensure line ends with newline
                                if not line.endswith('\n'):
                                    line = line + '\n'
                                # Print to console
                                print(line, end='', flush=True)
                                # Write to log file
                                log_file.write(line)
                                log_file.flush()
                            except UnicodeDecodeError as ue:
                                # This should not happen with errors='replace', but just in case
                                error_msg = f"[Erro de codificação - caractere inválido ignorado]\n"
                                print(error_msg, flush=True)
                                log_file.write(error_msg)
                                log_file.flush()
                    except Exception as read_error:
                        console.print(f"[warning]Erro ao ler saída: {read_error}[/warning]")

                    # Wait for process to complete
                    process.wait()
                    returncode = process.returncode

                    if line_count == 0:
                        console.print("[warning]Nenhuma saída foi gerada pelo comando[/warning]")

                if returncode == 0:
                    console.print("\n[success]Comando executado com sucesso[/success]")
                else:
                    console.print(f"\n[error]Comando falhou com código {returncode}[/error]")
                console.print(f"Log: {log_filename}")
                return None
        except UnicodeDecodeError as ude:
            console.print(f"[error]Erro de codificação UTF-8 na saída do comando[/error]")
            console.print(f"[warning]O comando produziu caracteres não-UTF-8 que foram substituídos[/warning]")
            console.print(f"Log: {log_filename}")
            return None
        except Exception as e:
            console.print(f"[error]Erro ao executar comando: {e}[/error]")
            console.print(f"Log: {log_filename}")
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

            # Determine project name to get correct docker config
            if 'zotonic' in cwd:
                project_key = 'superleme'
            elif 'phoenix' in cwd:
                project_key = 'sl_phoenix'
            else:
                project_key = None

            docker_config = docker_configs.get(project_key) if docker_configs and project_key else None

            # Update docker-compose.yml with versions from database before running
            if use_docker and Executor._has_docker_compose(cwd):
                Executor._update_docker_compose_versions(cwd, docker_config)

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
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "data", "logs")
        os.makedirs(log_dir, exist_ok=True)

        # Create log files
        log_files = []
        for proc_info in process_info:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = os.path.join(log_dir, f"{proc_info['name'].replace(' ', '_')}_{timestamp}.log")
            log_file = open(log_filename, 'w')
            proc_info['log_file'] = log_file
            log_files.append(log_filename)
            console.print(f"Log para {proc_info['name']}: {log_filename}")

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
                            subtitle=f"{proc_info['command']}",
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
