import subprocess
import os
import time
import sys
import re
from typing import Optional, List, Dict
from aedificator import console
from config import ConfigManager
from process import ProcessManager
from unidecode import unidecode
from aedificator.paths import get_logs_dir


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
            
        try:
            text = byte_data.decode('utf-8')
        except UnicodeDecodeError:
            text = byte_data.decode('latin-1', errors='replace')
            
 

        try:
            text = unidecode(text)
        except Exception:
            pass

        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1a\x1c-\x1f\x7f-\x9f]', '', text)
        
        return text

    @staticmethod
    def _has_docker_compose(cwd: str) -> bool:
        """Check if directory has docker-compose configuration."""
        compose_files = ['docker-compose.yml', 'docker-compose.yaml']
        return any(os.path.exists(os.path.join(cwd, f)) for f in compose_files)


    @staticmethod
    def _wrap_with_docker(command: str, cwd: str, use_docker: bool = True, docker_config: Optional[Dict] = None) -> str:
        """Wrap command with docker-compose if needed."""
        if use_docker and Executor._has_docker_compose(cwd):
            if 'zotonic' in cwd:
                if command.startswith('make') or command.startswith('bash') or command.startswith('sh') or command.startswith('mise'):
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
            ConfigManager.update_docker_versions(cwd, docker_config)

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

        log_dir = get_logs_dir()

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
                ConfigManager.update_docker_versions(cwd, docker_config)

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
            ProcessManager.display_live_output(process_info, Executor._safe_decode)

        return [p['process'] for p in process_info]

    @staticmethod
    def run_make(target: str, cwd: str, background: bool = False, use_docker: bool = False, docker_config: Optional[Dict] = None) -> Optional[subprocess.Popen]:
        return Executor.run_command(f"make {target}", cwd, background, use_docker, docker_config)