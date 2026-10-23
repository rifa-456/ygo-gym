import random

from ..state import Player
from .model import AgentEnd, AgentInput


class RandomAgent:
    """Sample uniformly from legal candidates, using a session-local RNG."""

    def __init__(self):
        self._random = random.Random(0)

    def reset(self, *, player: Player, seed: int) -> None:
        self._random.seed(seed)

    def act(self, decision: AgentInput) -> int:
        return self._random.randrange(len(decision.actions))

    def end(self, episode: AgentEnd) -> None:
        pass
