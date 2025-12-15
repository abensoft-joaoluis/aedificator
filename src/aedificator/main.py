from pathing.main import Pathing
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from . import console
from .memory import initialize_database, Paths
from .menu import Menu

class Main():
    def __init__(self):
        self.console = console
        # Initialize database and create tables
        db = initialize_database()
        db.create_tables([Paths])

        selected = Pathing.find_folders()

        # Try auto-detection if not in database
        auto_detected = None
        if not selected or not all([selected.superleme_path, selected.sl_phoenix_path, selected.extension_path]):
            self.console.print("[info]Detectando pastas do projeto automaticamente...[/info]")
            auto_detected = Pathing.auto_detect_folders()
            detected_count = sum(1 for v in auto_detected.values() if v)
            if detected_count > 0:
                self.console.print(f"[success]Detectadas {detected_count} pastas[/success]")
                if auto_detected["superleme_path"]:
                    self.console.print(f"Superleme: {auto_detected['superleme_path']}")
                if auto_detected["sl_phoenix_path"]:
                    self.console.print(f"SL Phoenix: {auto_detected['sl_phoenix_path']}")
                if auto_detected["extension_path"]:
                    self.console.print(f"Extensão: {auto_detected['extension_path']}")
            else:
                self.console.print("[warning]Nenhuma pasta detectada automaticamente[/warning]")

        # Use database > auto-detection > user selection (in that priority order)
        self.superleme_folder = (
            (selected.superleme_path if selected else None) or
            (auto_detected["superleme_path"] if auto_detected else None) or
            Pathing.select_folder()
        )
        self.sl_phoenix_folder = (
            (selected.sl_phoenix_path if selected else None) or
            (auto_detected["sl_phoenix_path"] if auto_detected else None) or
            Pathing.select_folder()
        )
        self.extension_folder = (
            (selected.extension_path if selected else None) or
            (auto_detected["extension_path"] if auto_detected else None) or
            Pathing.select_folder()
        )

        # Update existing row or create new one (no duplicates)
        if selected:
            selected.superleme_path = self.superleme_folder
            selected.sl_phoenix_path = self.sl_phoenix_folder
            selected.extension_path = self.extension_folder
            selected.save()
            paths_memory = selected
        else:
            paths_memory = Paths.create(
                superleme_path=self.superleme_folder,
                sl_phoenix_path=self.sl_phoenix_folder,
                extension_path=self.extension_folder,
            )


        # Initialize and show menu
        menu = Menu(
            superleme_path=self.superleme_folder,
            sl_phoenix_path=self.sl_phoenix_folder,
            extension_path=self.extension_folder
        )
        menu.show_main_menu()

    