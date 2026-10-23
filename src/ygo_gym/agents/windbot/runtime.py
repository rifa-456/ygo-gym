from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from ...assets.location import directory, source_checkout
from .source import build, checkout
from .transport import WindBotError, Worker

__all__ = ["WindBotError", "Worker", "build", "checkout", "resolve"]


@dataclass(frozen=True, slots=True)
class Runtime:
    command: tuple[str, ...]
    assets: Path
    root: Path | None


def resolve(root: str | Path | None = None, *, dotnet: str = "dotnet") -> Runtime:
    if root is not None or source_checkout() is not None:
        project = checkout(root)
        return Runtime(
            (dotnet, str(build(project, dotnet=dotnet))),
            project / "third_party/WindBot",
            project,
        )
    assets = directory("windbot", "WindBot")
    executable = assets / "runtime" / ("Host.exe" if sys.platform == "win32" else "Host")
    if not executable.is_file():
        raise WindBotError("bundled WindBot worker is missing; reinstall a complete ygo-gym wheel")
    return Runtime((str(executable),), assets, None)
