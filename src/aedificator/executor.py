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
from unidecode import unidecode


class Executor:
    """Handles terminal command execution in project folders."""

    @staticmethod
    def _safe_decode(byte_data: bytes) -> str:
        """
        Dev-Friendly Decoder:
        1. Prevents crashes from invalid UTF-8.
        2. Preserves ANSI colors (Green/Red) for developer sanity.
        3. Still strips dangerous binary control codes that freeze terminals.
        """
        if not byte_data:
            return ""
            
        # 1. Try UTF-8 first
        try:
            text = byte_data.decode('utf-8')
        except UnicodeDecodeError:
            # 2. Fallback to Latin-1 to prevent crashes on binary blobs
            text = byte_data.decode('latin-1', errors='replace')
            
        # 3. Normalize weird characters (like 'ç' -> 'c') 
        # unidecode preserves ASCII (including Escape codes), so colors stay safe.
        try:
            text = unidecode(text)
        except Exception:
            pass

        # 4. Sanitize Control Characters, BUT KEEP COLORS
        # We strip non-printable chars, but we EXPLICITLY ALLOW:
        # \x09 (Tab), \x0a (Newline), \x0d (Carriage Return), \x1b (ANSI Escape)
        
        # The Regex below strips:
        # \x00-\x08 (Null, Bell, Backspace, etc)
        # \x0b-\x0c (Vertical Tab, Form Feed)
        # \x0e-\x1a (Shift Out/In, Device Controls... stops just before \x1b)
        # \x1c-\x1f (File Separators)
        # \x7f-\x9f (DEL and C1 Control codes)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1a\x1c-\x1f\x7f-\x9f]', '', text)
        
        return text

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

            try:
                import json as _json
                langs = _json.loads(docker_config.get('languages', '{}'))
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

            console.print(f"[success].env criado/atualizado com POSTGRES_VERSION={postgres_version}[/success]")

        except Exception as e:
            console.print(f"[warning]Não foi possível criar/atualizar .env: {e}[/warning]")

    @staticmethod
    def _wrap_with_docker(command: str, cwd: str, use_docker: bool = True, docker_config: Optional[Dict] = None) -> str:
        """Wrap command with docker-compose if needed."""
        if use_docker and Executor._has_docker_compose(cwd):
            if 'zotonic' in cwd:
                if command.startswith('make') or command.startswith('bash') or command.startswith('sh') or command.startswith('mise'):
                    # Added 'force-color' env vars where possible to encourage tools to output color
                    docker_cmd = f'NO_PROXY=* stdbuf -o0 -e0 docker compose --ansi=always --verbose --progress=plain -f docker-compose.yml run --rm --entrypoint="" -w /opt/zotonic -e NO_PROXY=* -e TERM=xterm-256color zotonic {command}'
                else:   
                    docker_cmd = f'stdbuf -o0 -e0 docker compose --ansi=always --verbose --progress=plain -f docker-compose.yml run --rm --service-ports -w /opt/zotonic -e TERM=xterm-256color zotonic {command}'
            elif 'phoenix' in cwd:
                docker_cmd = f'stdbuf -o0 -e0 docker compose --ansi=always --verbose --progress=plain -f docker-compose.yml run --rm --service-ports -w /app -e TERM=xterm-256color app {command}'
            else:
                service = 'app'
                docker_cmd = f'stdbuf -o0 -e0 docker-compose --ansi=always --verbose exec -e TERM=xterm-256color {service} {command}'
            return docker_cmd
        return command

    @staticmethod
    def run_command(command: str, cwd: str, background: bool = False, use_docker: bool = False, docker_config: Optional[Dict] = None) -> Optional[subprocess.Popen]:
        if not os.path.exists(cwd):
            console.print(f"[error]Diretório não encontrado: {cwd}[/error]")
            return None

        if use_docker and Executor._has_docker_compose(cwd):
            Executor._update_docker_compose_versions(cwd, docker_config)

        wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

        console.print(f"[info]Executando:[/info] {command}")
        console.print(f"Diretório: {cwd}")
        if use_docker and Executor._has_docker_compose(cwd):
            console.print("Usando Docker para executar comando")
            console.print(f"Comando Docker completo: {wrapped_command}")
            console.print("\n" + "="*80)
            console.print("[info]Saída do comando (verbose):[/info]")
            console.print("="*80 + "\n")

        if 'zotonic' in cwd:
            project_name = 'superleme'
        elif 'phoenix' in cwd:
            project_name = 'sl_phoenix'
        elif 'plugin' in cwd:
            project_name = 'extension'
        else:
            project_name = os.path.basename(cwd)

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "data", "logs")
        os.makedirs(log_dir, exist_ok=True)

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
                with open(log_filename, 'w', buffering=1, encoding='utf-8', errors='replace') as log_file:
                    env = os.environ.copy()
                    env['PYTHONUNBUFFERED'] = '1'
                    env['DOCKER_BUILDKIT_PROGRESS'] = 'plain'
                    env['BUILDKIT_PROGRESS'] = 'plain'
                    env['COMPOSE_DOCKER_CLI_BUILD'] = '1'
                    # Force color output in many tools
                    env['TERM'] = 'xterm-256color'
                    env['FORCE_COLOR'] = '1'

                    process = subprocess.Popen(
                        wrapped_command,
                        shell=True,
                        cwd=cwd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        executable='/bin/bash',
                        bufsize=0,
                        env=env
                    )

                    console.print("[info]Aguardando saída do comando...[/info]")

                    line_count = 0
                    
                    while True:
                        line_bytes = process.stdout.readline()
                        if not line_bytes:
                            if process.poll() is not None:
                                break
                            continue
                            
                        line_count += 1
                        
                        # Use Safe Decode (Preserving Colors)
                        line_str = Executor._safe_decode(line_bytes)
                        
                        line_str = line_str.replace('\r\n', '\n').replace('\r', '\n')
                        if not line_str.endswith('\n'):
                            line_str = line_str + '\n'
                            
                        print(line_str, end='', flush=True)
                        log_file.write(line_str)
                        log_file.flush()

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
        except Exception as e:
            console.print(f"[error]Erro ao executar comando: {e}[/error]")
            return None

    @staticmethod
    def run_multiple(commands: List[tuple], background: bool = True, docker_configs: Optional[Dict[str, Dict]] = None) -> List[subprocess.Popen]:
        if not background:
            processes = []
            for command_tuple in commands:
                command, cwd, use_docker = command_tuple
                docker_config = docker_configs.get(cwd) if docker_configs else None
                Executor.run_command(command, cwd, background=False, use_docker=use_docker, docker_config=docker_config)
            return processes

        console.print(f"[info]Executando {len(commands)} comando(s) simultaneamente...[/info]")

        process_info = []
        for command_tuple in commands:
            command, cwd, use_docker = command_tuple

            if 'zotonic' in cwd:
                project_key = 'superleme'
            elif 'phoenix' in cwd:
                project_key = 'sl_phoenix'
            else:
                project_key = None

            docker_config = docker_configs.get(project_key) if docker_configs and project_key else None

            if use_docker and Executor._has_docker_compose(cwd):
                Executor._update_docker_compose_versions(cwd, docker_config)

            wrapped_command = Executor._wrap_with_docker(command, cwd, use_docker, docker_config)

            if 'zotonic' in cwd:
                project_name = 'Superleme'
            elif 'phoenix' in cwd:
                project_name = 'SL Phoenix'
            else:
                project_name = os.path.basename(cwd)

            # Pass color env vars
            env = os.environ.copy()
            env['TERM'] = 'xterm-256color'
            env['FORCE_COLOR'] = '1'

            process = subprocess.Popen(
                wrapped_command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                executable='/bin/bash',
                bufsize=0,
                env=env
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
            Executor._display_live_output(process_info)

        return [p['process'] for p in process_info]

    @staticmethod
    def _display_live_output(process_info: List[Dict]):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(project_root, "data", "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_files = []
        for proc_info in process_info:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_filename = os.path.join(log_dir, f"{proc_info['name'].replace(' ', '_')}_{timestamp}.log")
            log_file = open(log_filename, 'w', encoding='utf-8', errors='replace')
            proc_info['log_file'] = log_file
            log_files.append(log_filename)
            console.print(f"Log para {proc_info['name']}: {log_filename}")

        layout = Layout()

        if len(process_info) == 2:
            layout.split_row(
                Layout(name="left"),
                Layout(name="right")
            )
        else:
            layout.split_column(*[Layout(name=f"proc{i}") for i in range(len(process_info))])

        def read_output(proc_info):
            try:
                for line_bytes in iter(proc_info['process'].stdout.readline, b''):
                    if not line_bytes: break
                    
                    # Use Safe Decode (Preserving Colors)
                    line_str = Executor._safe_decode(line_bytes)
                    line_stripped = line_str.rstrip()
                    
                    proc_info['output'].append(line_stripped)
                    proc_info['log_file'].write(line_str)
                    proc_info['log_file'].flush()
                    
                    if len(proc_info['output']) > 50:
                        proc_info['output'].pop(0)
            except Exception as e:
                pass

        threads = []
        for proc_info in process_info:
            thread = threading.Thread(target=read_output, args=(proc_info,), daemon=True)
            thread.start()
            threads.append(thread)

        try:
            with Live(layout, console=console, refresh_per_second=4) as live:
                while any(p['process'].poll() is None for p in process_info):
                    for idx, proc_info in enumerate(process_info):
                        output_text = Text.from_ansi(
                            "".join([line + "\n" for line in proc_info['output'][-30:]])
                        )

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

                time.sleep(1)

        except KeyboardInterrupt:
            console.print("\n[warning]Interrompido pelo usuário[/warning]")
            for proc_info in process_info:
                if proc_info['process'].poll() is None:
                    proc_info['process'].terminate()

        for thread in threads:
            thread.join(timeout=1)

        for proc_info in process_info:
            if 'log_file' in proc_info:
                proc_info['log_file'].close()

        console.print("\n[success]Execução finalizada[/success]")
        console.print("[info]Logs salvos em:[/info]")
        for log_file in log_files:
            console.print(f"  {log_file}")

    @staticmethod
    def run_make(target: str, cwd: str, background: bool = False, use_docker: bool = False, docker_config: Optional[Dict] = None) -> Optional[subprocess.Popen]:
        return Executor.run_command(f"make {target}", cwd, background, use_docker, docker_config)