from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial

from ..agents import Agent
from ..deck import Deck


@dataclass(frozen=True, slots=True)
class Competitor:
    """What is rated: an agent factory piloting a deck under a stable name.

    The factory builds a fresh session for every game and seat. Puzzle
    competitors have no deck because the puzzle supplies the cards.
    """

    name: str
    agent: Callable[[], Agent]
    deck: Deck | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("competitor name must be a nonempty string")
        if not callable(self.agent):
            raise TypeError("competitor agent must be a factory")
        if self.deck is not None and not isinstance(self.deck, Deck):
            raise TypeError("competitor deck must be a Deck or None")

    @classmethod
    def product(
        cls, agents: Mapping[str, Callable[[Deck], Agent]], decks: Mapping[str, Deck]
    ) -> tuple[Competitor, ...]:
        """Every agent piloting every deck, named agent/deck, for deck-balanced comparisons."""
        return tuple(
            cls(f"{agent}/{deck}", partial(factory, decks[deck]), decks[deck])
            for agent, factory in agents.items()
            for deck in decks
        )
