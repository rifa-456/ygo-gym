from typing import TYPE_CHECKING, Protocol

from .protocol import Agent

if TYPE_CHECKING:
    from ..deck import Deck
    from ..match import FirstPlayerInput, MatchResult, MatchStart, SideDeckInput


class MatchAgent(Agent, Protocol):
    def match_reset(self, match: MatchStart) -> None:
        """Initialize cross-duel memory for this match player."""
        ...

    def side_deck(self, decision: SideDeckInput) -> Deck:
        """Return the complete resulting deck, preserving registered inventory."""
        ...

    def choose_first(self, decision: FirstPlayerInput) -> int:
        """Return the stable match player (0 or 1) who should take the first turn."""
        ...

    def match_end(self, result: MatchResult) -> None:
        """Consume the final match score and duel history."""
        ...
