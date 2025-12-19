import subprocess
import os
import sys
import glob
import time
import questionary
from aedificator import console
from executor import Executor
from aedificator.paths import get_backup_file, get_data_dir
from pathing.main import Pathing


class BackupManager:
    """Manages database backup operations."""

    @staticmethod
    def download_backup():
        """Download backup file from remote server."""
        console.print("\n[info]Download de Novo Backup[/info]")

        # Find .pem file
        ssh_dir = os.path.expanduser("~/.ssh")
        pem_files = glob.glob(os.path.join(ssh_dir, "*.pem"))

        if not pem_files:
            console.print("[warning]Nenhum arquivo .pem encontrado em ~/.ssh[/warning]")
            console.print("[info]Selecione o arquivo .pem usando o navegador de arquivos[/info]")
            pem_file = Pathing.select_file(ssh_dir)

            if not pem_file or not os.path.exists(pem_file):
                console.print("[error]Arquivo .pem não encontrado. Download cancelado.[/error]")
                return
        elif len(pem_files) == 1:
            pem_file = pem_files[0]
            console.print(f"[success]Arquivo .pem encontrado: {pem_file}[/success]")
        else:
            console.print(f"[info]Encontrados {len(pem_files)} arquivos .pem em ~/.ssh[/info]")
            console.print("[info]Selecione o arquivo .pem desejado usando o navegador de arquivos[/info]")
            pem_file = Pathing.select_file(ssh_dir)

            if not pem_file or not os.path.exists(pem_file):
                console.print("[error]Arquivo .pem não selecionado. Download cancelado.[/error]")
                return

        # List remote backups
        remote_host = "ubuntu@teste1x.superleme.com.br"
        remote_dir = "/home/ubuntu/bkps"

        console.print(f"\n[info]Listando arquivos em {remote_host}:{remote_dir}[/info]")

        try:
            ssh_command = f'ssh -i "{pem_file}" {remote_host} "ls -1 {remote_dir}/*.backup"'
            result = subprocess.run(
                ssh_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            files = [os.path.basename(f.strip()) for f in result.stdout.strip().split('\n') if f.strip()]

            if not files:
                console.print("[error]Nenhum arquivo .backup encontrado no servidor[/error]")
                return

            selected_file = questionary.select(
                "Selecione o arquivo de backup para baixar:",
                choices=files
            ).ask()

            if not selected_file:
                console.print("[info]Nenhum arquivo selecionado. Download cancelado.[/info]")
                return

        except subprocess.CalledProcessError as e:
            console.print(f"[error]Erro ao listar arquivos no servidor:[/error]")
            console.print(f"[error]{e.stderr}[/error]")
            return
        except Exception as e:
            console.print(f"[error]Erro ao conectar ao servidor: {str(e)}[/error]")
            return

        data_dir = get_data_dir()
        backup_file = get_backup_file()

        remote_file = f"{remote_dir}/{selected_file}"
        scp_command = f'scp -v -i "{pem_file}" {remote_host}:{remote_file} "{backup_file}"'

        console.print(f"\n[info]Executando: {scp_command}[/info]\n")
        sys.stdout.flush()
        sys.stderr.flush()

        try:
            result = subprocess.run(
                scp_command,
                shell=True,
                check=True
            )

            sys.stdout.flush()
            sys.stderr.flush()

            if os.path.exists(backup_file):
                console.print(f"[success]Backup baixado com sucesso: {backup_file}[/success]")
            else:
                console.print("[warning]Comando executado, mas arquivo não encontrado no destino[/warning]")

        except subprocess.CalledProcessError as e:
            console.print(f"[error]Erro ao baixar backup:[/error]")
            console.print(f"[error]{e.stderr}[/error]")
        except Exception as e:
            console.print(f"[error]Erro ao executar comando SCP: {str(e)}[/error]")

    @staticmethod
    def restore_database(zotonic_root, use_docker):
        """Restore database from backup file."""
        backup_file = get_backup_file()

        if not os.path.exists(backup_file):
            console.print(f"[error]Arquivo de backup não encontrado: {backup_file}[/error]")
            console.print("[info]Execute 'Baixar Novo Backup do Banco' nas Configurações primeiro.[/info]")
            return

        console.print(f"[info]Usando backup: {backup_file}[/info]")

        if use_docker:
            BackupManager._restore_docker(zotonic_root, backup_file)
        else:
            BackupManager._restore_local(zotonic_root, backup_file)

        console.print("[success]Processo de restauração finalizado![/success]")

    @staticmethod
    def _restore_docker(zotonic_root, backup_file):
        """Restore database in Docker environment."""
        console.print("[info]Iniciando container PostgreSQL...[/info]")
        Executor.run_command("docker compose up -d postgres", zotonic_root, background=False, use_docker=False)

        console.print("[info]Aguardando PostgreSQL ficar pronto...[/info]")
        Executor.run_command("sleep 5", zotonic_root, background=False, use_docker=False)

        # Detect DB user
        db_user = "postgres"
        env_path = os.path.join(zotonic_root, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith("POSTGRES_USER="):
                            db_user = line.split("=")[1].strip()
                            break
            except Exception:
                pass

        console.print(f"[info]Conectando como superusuário: {db_user}[/info]")

        # Create roles
        console.print("[info]Criando roles...[/info]")
        Executor.run_command(
            f'docker compose exec -T postgres psql -U {db_user} -c "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = \'postgres\') THEN CREATE ROLE postgres WITH LOGIN SUPERUSER; END IF; END$$;"',
            zotonic_root, background=False, use_docker=False
        )

        Executor.run_command(
            f'docker compose exec -T postgres psql -U {db_user} -c "DROP ROLE IF EXISTS superleme_ro; CREATE ROLE superleme_ro;"',
            zotonic_root, background=False, use_docker=False
        )

        if db_user != "superleme":
            Executor.run_command(
                f'docker compose exec -T postgres psql -U {db_user} -c "DROP ROLE IF EXISTS superleme; CREATE ROLE superleme WITH LOGIN PASSWORD \'superleme\';"',
                zotonic_root, background=False, use_docker=False
            )

        # Recreate database
        console.print("[info]Recriando banco de dados...[/info]")
        Executor.run_command(
            f'docker compose exec -T postgres psql -U {db_user} -c "DROP DATABASE IF EXISTS superleme;"',
            zotonic_root, background=False, use_docker=False
        )
        Executor.run_command(
            f'docker compose exec -T postgres psql -U {db_user} -c "CREATE DATABASE superleme OWNER superleme;"',
            zotonic_root, background=False, use_docker=False
        )

        # Restore backup
        console.print("[info]Restaurando backup...[/info]")
        restore_cmd = f'cat "{backup_file}" | docker compose exec -T postgres pg_restore -U {db_user} --verbose -d superleme'
        Executor.run_command(restore_cmd, zotonic_root, background=False, use_docker=False)

        # Post-restore sync
        console.print("\n[info]Banco restaurado com sucesso![/info]")
        
    @staticmethod
    def _restore_local(zotonic_root, backup_file):
        """Restore database locally without Docker."""
        console.print("[info]Restaurando backup localmente...[/info]")
        restore_cmd = f'sudo -u postgres pg_restore --verbose -d superleme "{backup_file}"'
        Executor.run_command(restore_cmd, zotonic_root, background=False, use_docker=False)
