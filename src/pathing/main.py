import subprocess
import tempfile
import os
import questionary
from pathlib import Path
from aedificator import console
from aedificator.memory import Paths


class Pathing:
    def __init__(self):
        pass

    @staticmethod
    def auto_detect_folders():
        """Automatically detect the three main folders based on patterns.
        Searches /home/devel first, then falls back to entire /home directory.
        Returns a dict with keys: superleme_path, sl_phoenix_path, extension_path.
        """
        detected = {
            "superleme_path": None,
            "sl_phoenix_path": None,
            "extension_path": None,
        }

        # Search locations in priority order
        search_roots = ["/home/devel", "/home"]

        for search_root in search_roots:
            if not os.path.exists(search_root):
                continue

            # Only search if we haven't found all folders yet
            if all(detected.values()):
                break

            # Search for superleme folder (inside zotonic/apps_user)
            if not detected["superleme_path"]:
                try:
                    for root, dirs, files in os.walk(search_root):
                        # Limit depth to avoid excessive searching
                        depth = root[len(search_root) :].count(os.sep)
                        if depth > 5:
                            dirs[:] = []
                            continue

                        if root.endswith(
                            os.path.join("zotonic", "apps_user", "superleme")
                        ):
                            detected["superleme_path"] = root
                            break
                except PermissionError:
                    pass

            # Search for sl_phoenix folder (Phoenix/Elixir project)
            if not detected["sl_phoenix_path"]:
                try:
                    for root, dirs, files in os.walk(search_root):
                        depth = root[len(search_root) :].count(os.sep)
                        if depth > 3:
                            dirs[:] = []
                            continue

                        # Check if directory name contains phoenix or is sl_phoenix
                        if (
                            "phoenix" in os.path.basename(root).lower()
                            or os.path.basename(root) == "sl_phoenix"
                        ):
                            # Verify it's a Phoenix project
                            if "mix.exs" in files or "lib" in dirs:
                                detected["sl_phoenix_path"] = root
                                break
                except PermissionError:
                    pass

            # Search for extension folder (Chrome extension - specifically plugin-simulacao)
            if not detected["extension_path"]:
                try:
                    for root, dirs, files in os.walk(search_root):
                        depth = root[len(search_root) :].count(os.sep)
                        if depth > 3:
                            dirs[:] = []
                            continue

                        # Check if it's the plugin-simulacao Chrome extension
                        if "package.json" in files:
                            try:
                                import json

                                pkg_path = os.path.join(root, "package.json")
                                with open(pkg_path, "r") as f:
                                    pkg = json.load(f)

                                    # Check for specific Chrome extension indicators
                                    name = pkg.get("name", "")
                                    description = pkg.get("description", "").lower()
                                    dev_deps = pkg.get("devDependencies", {})

                                    # Match plugin-simulacao or similar Chrome extension projects
                                    is_chrome_extension = (
                                        "plugin" in name.lower()
                                        or (
                                            "chrome" in description
                                            and "extension" in description
                                        )
                                        or "@types/chrome" in dev_deps
                                        or "chrome-types" in dev_deps
                                    )

                                    # Also verify popup.html exists (Chrome extension specific)
                                    has_popup = "popup.html" in files

                                    if is_chrome_extension and has_popup:
                                        detected["extension_path"] = root
                                        break
                            except (json.JSONDecodeError, IOError):
                                pass
                except PermissionError:
                    pass

            # If we found everything in /home/devel, no need to search /home
            if all(detected.values()):
                break

        return detected

    @staticmethod
    def select_folder():
        """Select a folder using ranger-fm."""
        console.print("\n[info]Abrindo navegador de arquivos Ranger...[/info]")
        console.print(
            "Navegação: ↑/↓ para mover, → para entrar na pasta, ← para voltar"
        )
        console.print("Seleção: Pressione 'q' para selecionar a pasta atual e sair\n")
        questionary.press_any_key_to_continue().ask()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            choosefile_path = tmp.name

        subprocess.run(
            ["ranger", f"--choosedir={choosefile_path}", "/home/"], check=True
        )

        with open(choosefile_path, "r") as f:
            selected_dir = f.read().strip()
        os.unlink(choosefile_path)

        if selected_dir and os.path.isdir(selected_dir):
            return selected_dir

        return questionary.path("Path to config folder:").ask()

    @staticmethod
    def select_file(start_dir="/home"):
        """Select a file using ranger-fm."""
        console.print("\n[info]Abrindo navegador de arquivos Ranger...[/info]")
        console.print(
            "Navegação: ↑/↓ para mover, → para entrar na pasta, ← para voltar"
        )
        console.print("Seleção: Pressione Enter para selecionar o arquivo e sair\n")
        questionary.press_any_key_to_continue().ask()

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
            choosefile_path = tmp.name

        subprocess.run(
            ["ranger", f"--choosefile={choosefile_path}", start_dir], check=True
        )

        with open(choosefile_path, "r") as f:
            selected_file = f.read().strip()
        os.unlink(choosefile_path)

        if selected_file and os.path.isfile(selected_file):
            return selected_file

        return None

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
