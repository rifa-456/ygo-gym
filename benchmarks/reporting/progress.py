from datetime import timedelta
from math import ceil
import os
import sys
from time import perf_counter

from rich.console import Console
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Column, Table
from rich.text import Text


def add_argument(parser) -> None:
    parser.add_argument("--display", choices=("auto", "rich", "plain"), default="auto",
                        help="auto uses plain logs in CI or redirected output")


class RemainingColumn(ProgressColumn):
    def __init__(self, report):
        super().__init__(table_column=Column(no_wrap=True))
        self.report = report

    def render(self, task):
        remaining = self.report.remaining if task.fields["kind"] == "suite" else task.time_remaining
        if task.finished:
            return Text("0:00:00", style="green")
        if remaining is None:
            return Text("--:--", style="dim")
        return Text(f"~{timedelta(seconds=ceil(max(remaining, 0)))}", style="cyan")


class Report:
    def __init__(self, title: str, total: int, display: str, quiet: bool = False,
                 worker_total: int | None = None):
        self.title = title
        self.total = total
        self.quiet = quiet
        self.worker_total = worker_total
        self.completed = 0
        self.worker_completed = 0
        self.calibration_runs = 0
        self.case_start = None
        self.case_label = "Preparing"
        self.case_durations = []
        self.measuring = False
        self.progress = None
        self.task = None
        self.worker_task = None
        self.rich = display == "rich" or (
            display == "auto" and sys.stderr.isatty() and sys.stdout.isatty()
            and not os.environ.get("CI") and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb"
        )
        self.console = Console(stderr=True, force_terminal=self.rich,
                               force_interactive=self.rich,
                               color_system="auto" if self.rich else None,
                               markup=False, highlight=False)

    @property
    def remaining(self):
        if self.completed >= self.total:
            return 0.0
        if not self.case_durations:
            return None
        average = sum(self.case_durations) / len(self.case_durations)
        current = perf_counter() - self.case_start if self.case_start is not None else 0.0
        return max(0.0, average - current) + average * (self.total - self.completed - 1)

    def __enter__(self):
        if not self.quiet:
            self.console.print(self.title)
            if self.rich:
                self.progress = Progress(
                    SpinnerColumn(), TextColumn("{task.description}", markup=False),
                    BarColumn(bar_width=None, complete_style="cyan", finished_style="green"),
                    TaskProgressColumn(), TextColumn("{task.fields[status]}", markup=False),
                    TextColumn("elapsed"), TimeElapsedColumn(), TextColumn("ETA"), RemainingColumn(self),
                    console=self.console, auto_refresh=True, refresh_per_second=4, transient=True,
                )
                self.task = self.progress.add_task("Suite", total=self.total,
                                                   kind="suite", status=f"0/{self.total} cases")
                if self.worker_total is not None:
                    self.worker_task = self.progress.add_task("Preparing", total=None, visible=False,
                                                              kind="workers", status="calibrating")
                self.progress.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.progress is not None:
            self.progress.stop()
        if exc_type is not None and not self.quiet:
            self.console.print(f"Stopped after {self.completed}/{self.total} completed cases",
                               style="red" if self.rich else None)

    def start(self, label: str) -> None:
        self.case_start = perf_counter()
        self.case_label = label
        self.worker_completed = 0
        self.calibration_runs = 0
        self.measuring = False
        if self.quiet:
            return
        if self.worker_task is not None:
            self.console.print(f"[{self.completed + 1}/{self.total}] {label}", style="bold cyan")
            self._worker_row(None, "preparing")
        elif self.progress is not None:
            self.progress.update(self.task, description=label, refresh=True)
        else:
            self.console.print(f"[{self.completed + 1}/{self.total}] Starting {label}")

    def _worker_row(self, total, status: str) -> None:
        self.progress.remove_task(self.worker_task)
        self.worker_task = self.progress.add_task("Current", total=total,
                                                  kind="workers", status=status)

    def begin_workers(self, calibrating: bool) -> None:
        self.measuring = not calibrating
        if self.quiet:
            return
        status = "calibrating" if calibrating else f"0/{self.worker_total} workers"
        if self.worker_task is not None:
            self._worker_row(None if calibrating else self.worker_total, status)
        else:
            self.console.print(f"  {status}")

    def worker_finished(self, measured: bool, completed: int, total: int) -> None:
        if measured:
            if not self.measuring:
                self.begin_workers(calibrating=False)
            self.worker_completed = completed
            status = f"{completed}/{total} workers"
        else:
            self.calibration_runs += 1
            status = f"calibrating ({self.calibration_runs})"
        if self.quiet:
            return
        if self.worker_task is not None:
            self.progress.update(self.worker_task, completed=completed if measured else 0,
                                 status=status, refresh=True)
        else:
            self.console.print(f"  {status}")

    def advance(self) -> None:
        if self.case_start is not None:
            self.case_durations.append(perf_counter() - self.case_start)
        self.case_start = None
        self.completed += 1
        if self.progress is not None:
            self.progress.update(self.task, completed=self.completed,
                                 status=f"{self.completed}/{self.total} cases", refresh=True)

    def output(self, text: str) -> None:
        if self.progress is not None:
            self.console.print(text, end="")
        else:
            sys.stdout.write(text)
            sys.stdout.flush()

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
