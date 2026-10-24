from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Protocol

from .deck import Deck
from .rules import DuelConfig

if TYPE_CHECKING:
    from .engine import Duel, Engine
    from .task import Task, TaskDuel


class ReplayUnavailableError(RuntimeError):
    """The duel's history cannot be reproduced from its start, seed, and actions."""


class Start(Protocol):
    def create(self, engine: Engine, seed: int) -> Duel: ...

    def episode(self, duel: Duel, task: Task, game_id: str) -> TaskDuel: ...

    def record(self) -> dict: ...


def task_episode(duel: Duel, task: Task, game_id: str) -> TaskDuel:
    from .task import TaskDuel

    return TaskDuel(duel, task, game_id=game_id)


@dataclass(frozen=True, slots=True)
class DeckStart:
    """A duel created from two decks and an optional configuration."""

    players: tuple[Deck, Deck]
    config: DuelConfig | None = None

    def create(self, engine: Engine, seed: int) -> Duel:
        return engine.create_duel(*self.players, seed=seed, config=self.config)

    def episode(self, duel: Duel, task: Task, game_id: str) -> TaskDuel:
        return task_episode(duel, task, game_id)

    def record(self) -> dict:
        return {
            "kind": "deck",
            "players": [
                {"main": list(deck.main), "extra": list(deck.extra), "side": list(deck.side)}
                for deck in self.players
            ],
            "config_json": None if self.config is None else json.dumps(asdict(self.config)),
            "source": None,
            "source_name": None,
        }


@dataclass(frozen=True, slots=True)
class ScriptStart:
    """A duel created by Lua setup source, such as a DuelSetup position."""

    source: str
    name: str

    def create(self, engine: Engine, seed: int) -> Duel:
        return engine._create_scripted(self.source, self.name, seed, self)

    def episode(self, duel: Duel, task: Task, game_id: str) -> TaskDuel:
        return task_episode(duel, task, game_id)

    def record(self) -> dict:
        return {"kind": "script", "players": [], "config_json": None, "source": self.source, "source_name": self.name}


@dataclass(frozen=True, slots=True)
class PuzzleStart:
    """A puzzle's prepared Lua source, played by a single solver."""

    source: str
    name: str

    def create(self, engine: Engine, seed: int) -> Duel:
        return engine._create_scripted(self.source, self.name, seed, self)

    def episode(self, duel: Duel, task: Task, game_id: str) -> TaskDuel:
        from .puzzle import PuzzleDuel

        return PuzzleDuel(duel, task, game_id=game_id)

    def record(self) -> dict:
        return {"kind": "puzzle", "players": [], "config_json": None, "source": self.source, "source_name": self.name}


def start_from_record(record: dict) -> DeckStart | ScriptStart | PuzzleStart:
    """Rebuild a start; records without a kind, such as dataset setups, are deck or script starts."""
    if record.get("kind") == "puzzle":
        return PuzzleStart(record["source"], record["source_name"])
    if record.get("source") is not None:
        return ScriptStart(record["source"], record["source_name"])
    players = tuple(Deck(p["main"], p["extra"], p["side"]) for p in record["players"])
    config = record.get("config_json")
    return DeckStart(players, None if config is None else DuelConfig(**json.loads(config)))


@dataclass(frozen=True, slots=True)
class Replay:
    """Everything needed to reproduce a duel on an engine with matching provenance."""

    start: DeckStart | ScriptStart | PuzzleStart
    seed: int
    actions: tuple[int, ...]

    def play(self, engine: Engine) -> Duel:
        duel = self.start.create(engine, self.seed)
        try:
            for index in self.actions:
                duel.step(index)
        except BaseException:
            duel.close()
            raise
        return duel

    def record(self) -> dict:
        return {**self.start.record(), "seed": self.seed, "actions": list(self.actions)}

    @classmethod
    def from_record(cls, record: dict) -> Replay:
        return cls(start_from_record(record), record["seed"], tuple(record["actions"]))
