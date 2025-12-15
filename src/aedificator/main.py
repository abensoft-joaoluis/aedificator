from pathing.main import Pathing
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from . import console
from .memory import initialize_database, Paths

class Main():
    def __init__(self):
        self.console = console
        # Initialize database and create tables
        db = initialize_database()
        db.create_tables([Paths])

        selected = Pathing.find_folders()
        # Prompt for each path if not stored in memory
        self.superleme_folder = selected.superleme_path if (selected and selected.superleme_path) else Pathing.select_folder()
        self.sl_phoenix_folder = selected.sl_phoenix_path if (selected and selected.sl_phoenix_path) else Pathing.select_folder()
        self.extension_folder = selected.extension_path if (selected and selected.extension_path) else Pathing.select_folder()

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


        self.console.print(self.superleme_folder)
        


    