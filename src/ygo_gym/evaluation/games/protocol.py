from typing import Protocol

from ...engine import Engine
from ..competitor import Competitor
from ..result import GameResult


class Game(Protocol):
    """A scheduled game that plays itself and reports one result per duel."""

    kind: str

    @property
    def competitors(self) -> tuple[Competitor, ...]: ...

    def play(self, engine: Engine, index: int) -> list[GameResult]: ...

    def describe(self) -> dict: ...
