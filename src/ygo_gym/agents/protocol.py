from typing import Protocol

from ..state import Player
from .model import AgentEnd, AgentInput


class Agent(Protocol):
    """A separate mutable session per seat; sessions may share model weights."""

    def reset(self, *, player: Player, seed: int) -> None:
        """Start fresh memory and randomness at the supplied duel boundary."""
        ...

    def act(self, decision: AgentInput) -> int:
        """Return an index into this decision's complete legal action tuple."""
        ...

    def end(self, episode: AgentEnd) -> None:
        """Consume the remaining updates after termination or truncation."""
        ...
