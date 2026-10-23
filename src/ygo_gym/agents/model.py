from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..action import Action
from ..state import Observation, Player

if TYPE_CHECKING:
    from ..match.model import MatchResult


@dataclass(frozen=True, slots=True)
class AgentInput:
    """One decision and the player-visible updates not previously delivered.

    The last update is observation itself. Each update owns its event-card
    reference namespace. reward sums this player's rewards since the previous
    act call; the initial value is zero for an ongoing duel.
    """

    observation: Observation
    actions: tuple[Action, ...]
    updates: tuple[Observation, ...]
    reward: float = 0.0


@dataclass(frozen=True, slots=True)
class AgentEnd:
    """Final pending updates and reward, including for a seat that never acted."""

    player: Player
    updates: tuple[Observation, ...]
    reward: float
    result: MatchResult
