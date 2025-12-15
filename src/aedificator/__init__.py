from rich.console import Console
from rich.theme import Theme
from rich.pretty import install as _install_pretty

# Theme colors for nicer console output
_theme = Theme({
	"info": "cyan",
	"warning": "yellow",
	"error": "bold red",
	"success": "green",
	"muted": "dim"
})

# Shared, configured Console for the package
console = Console(theme=_theme, markup=True, emoji=True, highlight=True)

# Install pretty reprs to use the configured console
_install_pretty(console=console)

from .executor import Executor
from .menu import Menu

__all__ = ["console", "Executor", "Menu"]
