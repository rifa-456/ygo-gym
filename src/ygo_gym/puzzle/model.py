from dataclasses import dataclass
from pathlib import Path

from ..setup import DuelSetup
from ..state import Player
from ..task import Task, TaskDuel
from .collection import builtin_path, list_builtin


@dataclass(frozen=True, slots=True)
class WinThisTurn:
    """Player 0 must win before the first turn ends, enforced by engine effects."""

    player: int = 0

    def __post_init__(self):
        if isinstance(self.player, Player):
            object.__setattr__(self, "player", int(self.player))
        if type(self.player) is not int or self.player != 0:
            raise ValueError(
                "the initial puzzle start supports WinThisTurn for player 0"
            )


@dataclass(frozen=True, slots=True)
class Puzzle:
    """A Python position or unchanged Lua setup, evaluated through the real engine.

    Imported scripts retain their own duel flags, opponent automation, and
    objectives. Required scripts are resolved through Engine.script_roots.
    """

    name: str
    setup: DuelSetup | None = None
    objective: WinThisTurn | None = None
    source: str | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or "\0" in self.name:
            raise ValueError("puzzle name must be a nonempty string without NUL")
        if (self.setup is None) == (self.source is None):
            raise ValueError("provide exactly one of setup or Lua source")
        if self.setup is not None and not isinstance(self.setup, DuelSetup):
            raise TypeError("setup must be a DuelSetup")
        if self.source is not None and not isinstance(self.source, str):
            raise TypeError("source must be Lua text")
        if self.objective is not None and not isinstance(self.objective, WinThisTurn):
            raise TypeError("objective must be WinThisTurn or None")
        if self.source is not None and self.objective is not None:
            raise ValueError("imported Lua scripts retain their own objectives")

    @classmethod
    def from_lua(cls, path: str | Path):
        file = Path(path)
        return cls(name=file.name, source=file.read_bytes().decode("utf-8-sig"))

    @classmethod
    def builtin(cls, name: str):
        return cls(
            name=name, source=builtin_path(name).read_bytes().decode("utf-8-sig")
        )

    @staticmethod
    def list_builtin() -> tuple[str, ...]:
        return list_builtin()

    def to_lua(self) -> str:
        if self.source is not None:
            return self.source
        source = self.setup.to_lua()
        if self.objective is not None:
            source += "aux.BeginPuzzle()\n"
        return source

    def start(self, engine, *, seed: int, task: Task | None = None) -> TaskDuel:
        duel = engine._create_scripted(self.to_lua(), self.name, seed)
        try:
            return TaskDuel(duel, task)
        except BaseException:
            duel.close()
            raise
