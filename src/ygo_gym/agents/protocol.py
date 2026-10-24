from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from ..state import Player
from .model import AgentEnd, AgentInfo, AgentInput


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


@runtime_checkable
class Describable(Protocol):
    def describe(self) -> AgentInfo:
        """Name, version, and configuration recorded with every evaluated game."""
        ...


@runtime_checkable
class Reporting(Protocol):
    def stats(self) -> Mapping[str, float]:
        """Counters for the episode that just ended, read after end()."""
        ...
