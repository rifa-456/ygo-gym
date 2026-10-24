from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..action import Action
from ..state import Observation, Player

if TYPE_CHECKING:
    from ..episode.model import EpisodeResult


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

    def expand(self, actions: Sequence[Action]) -> tuple[int, ...]:
        """Expand a whole choice into the action indices to return from successive act() calls.

        Each action is matched by identity (the same card, zone, or option) against
        the legal actions after the previous ones, so a selection lists actions taken
        from this decision's actions. When the actions end before the decision
        completes and CONFIRM is legal, it is implied. InvalidChoiceError.step names
        the first action that is not legal, or len(actions) when the decision is
        still incomplete.
        """
        return tuple(self.observation._expand(list(actions)))


@dataclass(frozen=True, slots=True)
class AgentEnd:
    """Final pending updates and reward, including for a seat that never acted."""

    player: Player
    updates: tuple[Observation, ...]
    reward: float
    result: EpisodeResult


@dataclass(frozen=True, slots=True)
class AgentInfo:
    """Identity of an agent build; config holds JSON values that affect its play."""

    name: str
    version: str
    config: Mapping[str, object]
