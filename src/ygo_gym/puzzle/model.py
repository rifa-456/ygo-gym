from dataclasses import dataclass, field
from pathlib import Path

from ..replay import PuzzleStart
from ..setup import DuelSetup
from ..state import Player
from ..task import Task
from .collection import builtin_path, list_builtin
from .session import PuzzleDuel


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

    Every challenge requires player 0 to win this turn. Imported source keeps
    its card setup and effects; SIMPLE_AI and the turn deadline are enforced.
    Required scripts are resolved through Engine.script_roots.
    """

    name: str
    setup: DuelSetup | None = None
    objective: WinThisTurn = field(default_factory=WinThisTurn)
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
        if self.objective is None:
            object.__setattr__(self, "objective", WinThisTurn())

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
        source = self.source if self.source is not None else self.setup.to_lua()
        prefix = """local ygo_reload = Debug.ReloadFieldBegin
local ygo_begin = aux.BeginPuzzle
local ygo_begun = false
Debug.ReloadFieldBegin = function(flags, ...)
    return ygo_reload(flags | DUEL_SIMPLE_AI, ...)
end
aux.BeginPuzzle = function()
    if not ygo_begun then
        ygo_begun = true
        ygo_begin()
    end
end
local function ygo_setup()
"""
        suffix = """
end
ygo_setup()
aux.BeginPuzzle()
aux.BeginPuzzle = ygo_begin
Debug.ReloadFieldBegin = ygo_reload
"""
        return prefix + source + suffix

    def start(self, engine, *, seed: int, task: Task | None = None) -> PuzzleDuel:
        duel = PuzzleStart(self.to_lua(), self.name).create(engine, seed)
        try:
            return PuzzleDuel(duel, task)
        except BaseException:
            duel.close()
            raise
