from ygo_gym.agents import AgentInfo, RandomAgent
from ygo_gym.evaluation import GameResult, SeatResult

INFO = AgentInfo("synthetic", "1", {})


class CountingAgent(RandomAgent):
    """A random agent that reports how many times it acted."""

    def reset(self, *, player, seed):
        super().reset(player=player, seed=seed)
        self.calls = 0

    def act(self, decision):
        self.calls += 1
        return super().act(decision)

    def stats(self):
        return {"calls": float(self.calls)}


def seat(name):
    return SeatResult(name, INFO, None, 0, 0.0, {})


def duel(first, second, winner, *, index=0, kind="duel", match_winner=None, duel=0):
    return GameResult(index, duel, kind, None, 0, (seat(first), seat(second)), winner, match_winner,
                      "duel_end", None, (0.0, 0.0), 1, True, False, None)


def attempt(name, solved):
    return GameResult(0, 0, "puzzle", "p", 0, (seat(name),), name if solved else None, None,
                      "duel_end", solved, (0.0, 0.0), 1, True, False, None)
