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

        superleme_folder_auto = Pathing.find_superleme_folder()
        self.superleme_folder = superleme_folder_auto if superleme_folder_auto else Pathing.select_superleme_folder()
        self.console.print(self.superleme_folder)
        


    