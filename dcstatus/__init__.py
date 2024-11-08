"""bot's main entry point"""

from .hooks import cli


def main() -> None:
    """Run the application."""
    try:
        cli.start()
    except KeyboardInterrupt:
        pass
