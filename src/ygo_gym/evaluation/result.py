from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass

from ..agents import AgentInfo
from ..deck import Deck
from ..replay import Replay


def deck_record(deck: Deck | None) -> dict | None:
    if deck is None:
        return None
    return {"main": list(deck.main), "extra": list(deck.extra), "side": list(deck.side)}


def deck_from_record(record: dict | None) -> Deck | None:
    return None if record is None else Deck(record["main"], record["extra"], record["side"])


@dataclass(frozen=True, slots=True)
class SeatResult:
    """One competitor's side of a played duel or puzzle."""

    competitor: str
    agent: AgentInfo
    deck: Deck | None
    decisions: int
    seconds: float
    stats: Mapping[str, float]

    def record(self) -> dict:
        return {
            "competitor": self.competitor,
            "agent": self.agent.name,
            "agent_version": self.agent.version,
            "agent_config": json.dumps(dict(self.agent.config), sort_keys=True),
            "deck": deck_record(self.deck),
            "decisions": self.decisions,
            "seconds": self.seconds,
            "stats": dict(self.stats),
        }

    @classmethod
    def from_record(cls, record: dict) -> SeatResult:
        info = AgentInfo(record["agent"], record["agent_version"], json.loads(record["agent_config"]))
        return cls(
            record["competitor"], info, deck_from_record(record["deck"]), record["decisions"],
            record["seconds"], dict(record["stats"]),
        )


@dataclass(frozen=True, slots=True)
class GameResult:
    """One played duel: a puzzle attempt, a duel, or one duel of a match.

    seats follow engine seats. index identifies the scheduled game, so the duels
    of one match share it and differ by duel. winner and match_winner are
    competitor names; game_id links to the dataset when one was recorded.
    """

    index: int
    duel: int
    kind: str
    scenario: str | None
    seed: int
    seats: tuple[SeatResult, ...]
    winner: str | None
    match_winner: str | None
    reason: str | None
    solved: bool | None
    returns: tuple[float, ...]
    steps: int
    terminated: bool
    truncated: bool
    replay: Replay | None
    game_id: str | None = None

    @property
    def competitors(self) -> tuple[str, ...]:
        return tuple(seat.competitor for seat in self.seats)

    def record(self) -> dict:
        return {
            "index": self.index,
            "duel": self.duel,
            "kind": self.kind,
            "scenario": self.scenario,
            "seed": self.seed,
            "seats": [seat.record() for seat in self.seats],
            "winner": self.winner,
            "match_winner": self.match_winner,
            "reason": self.reason,
            "solved": self.solved,
            "returns": list(self.returns),
            "steps": self.steps,
            "terminated": self.terminated,
            "truncated": self.truncated,
            "replay": None if self.replay is None else self.replay.record(),
            "game_id": self.game_id,
        }

    @classmethod
    def from_record(cls, record: dict) -> GameResult:
        replay = record["replay"]
        return cls(
            record["index"], record["duel"], record["kind"], record["scenario"], record["seed"],
            tuple(SeatResult.from_record(seat) for seat in record["seats"]), record["winner"],
            record["match_winner"], record["reason"], record["solved"], tuple(record["returns"]),
            record["steps"], record["terminated"], record["truncated"],
            None if replay is None else Replay.from_record(replay), record["game_id"],
        )
