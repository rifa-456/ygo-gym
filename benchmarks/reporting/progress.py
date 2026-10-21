import os
import sys

from rich.console import Console
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text


def add_argument(parser) -> None:
    parser.add_argument("--display", choices=("auto", "rich", "plain"), default="auto",
                        help="auto uses plain logs in CI or redirected output")


class Report:
    def __init__(self, title: str, total: int, display: str, quiet: bool = False):
        self.title = title
        self.total = total
        self.quiet = quiet
        self.completed = 0
        self.progress = None
        self.task = None
        self.rich = display == "rich" or (
            display == "auto" and sys.stderr.isatty() and sys.stdout.isatty()
            and not os.environ.get("CI") and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb"
        )
        self.console = Console(stderr=True, force_terminal=self.rich,
                               color_system="auto" if self.rich else None,
                               markup=False, highlight=False)

    def __enter__(self):
        if not self.quiet:
            self.console.print(self.title)
            if self.rich:
                self.progress = Progress(
                    TextColumn("{task.description}"), BarColumn(), TaskProgressColumn(),
                    TextColumn("{task.completed:.0f}/{task.total:.0f}"), TimeElapsedColumn(),
                    console=self.console, auto_refresh=False, transient=True,
                )
                self.task = self.progress.add_task("Preparing", total=self.total)
                self.progress.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.progress is not None:
            self.progress.stop()
        if exc_type is not None and not self.quiet:
            self.console.print(f"Stopped after {self.completed}/{self.total} completed measurements",
                               style="red" if self.rich else None)

    def start(self, label: str) -> None:
        if self.quiet:
            return
        if self.progress is not None:
            self.progress.update(self.task, description=label, refresh=True)
        else:
            self.console.print(f"[{self.completed + 1}/{self.total}] {label}")

    def advance(self) -> None:
        self.completed += 1
        if self.progress is not None:
            self.progress.update(self.task, completed=self.completed, refresh=True)

    def summary(self, title: str, columns, rows) -> None:
        if self.quiet:
            return
        if self.rich:
            table = Table(title=Text(title), header_style="bold cyan")
            for column in columns:
                table.add_column(column)
            for row in rows:
                table.add_row(*(Text(str(value)) for value in row))
            self.console.print(table)
        else:
            self.console.print(title)
            for row in rows:
                self.console.print(" | ".join(f"{column}: {value}" for column, value in zip(columns, row)))

    def saved(self, path) -> None:
        if not self.quiet:
            self.console.print(f"Results saved to {path}", style="green" if self.rich else None)
