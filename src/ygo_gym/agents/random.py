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

    def match_reset(self, match) -> None:
        self._match_random = random.Random(match.seed)

    def side_deck(self, decision):
        return decision.deck

    def choose_first(self, decision) -> int:
        return self._match_random.randrange(2)

    def match_end(self, result) -> None:
        pass
