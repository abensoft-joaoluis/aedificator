import subprocess
import tempfile
import os
import questionary
from aedificator import console
from aedificator.memory import Paths


class Pathing():
    def __init__(self):
        pass

    @staticmethod
    def select_folder():
        """Select a folder using ranger-fm."""
        console.print("\n[info]Abrindo navegador de arquivos Ranger...[/info]")
        console.print("[muted]Navegação: ↑/↓ para mover, → para entrar na pasta, ← para voltar[/muted]")
        console.print("[muted]Seleção: Pressione 'q' para selecionar a pasta atual e sair[/muted]\n")
        questionary.press_any_key_to_continue().ask()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            choosefile_path = tmp.name
        
        subprocess.run(["ranger", f"--choosedir={choosefile_path}", "/home/"], check=True)
        
        with open(choosefile_path, 'r') as f:
            selected_dir = f.read().strip()
        os.unlink(choosefile_path)
        
        if selected_dir and os.path.isdir(selected_dir):
            return selected_dir
        
        return questionary.path("Path to config folder:").ask()

    @staticmethod
    def find_folders():
        """Return the stored Paths row from the database if it exists, else None."""
        try:
            query = Paths.select().limit(1)
            rows = list(query)
            if rows:
                return rows[0]
        except Exception:
            return None
        return None