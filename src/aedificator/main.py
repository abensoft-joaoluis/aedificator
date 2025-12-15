from pathing.main import Pathing
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from easygui import diropenbox
from . import console


class Main():
    def __init__(self):
        self.console = console
        superleme_folder_auto = self.find_superleme_folder()
        self.superleme_folder = superleme_folder_auto if superleme_folder_auto else self.select_superleme_folder()
        


    def select_superleme_folder(self):
        superleme_dir = diropenbox()
        self.console.print(superleme_dir)
        return superleme_dir

    def find_superleme_folder(self):
        return None 