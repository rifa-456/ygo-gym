import time

from ..agents import Describable, Reporting
from .competitor import Competitor
from .result import SeatResult


class Seat:
    """A competitor's fresh agent session, timed and summarized once per duel it plays."""

    def __init__(self, competitor: Competitor):
        self.competitor = competitor
        self.agent = competitor.agent()
        if not isinstance(self.agent, Describable):
            self.close()
            raise TypeError(f"agent of {competitor.name!r} must implement describe() for evaluation")
        self.info = self.agent.describe()
        self.results: list[SeatResult] = []
        self.deck = competitor.deck
        self._decisions = 0
        self._seconds = 0.0

    def reset(self, *, player, seed):
        self._decisions, self._seconds = 0, 0.0
        self.agent.reset(player=player, seed=seed)

    def act(self, decision):
        start = time.perf_counter()
        try:
            return self.agent.act(decision)
        finally:
            self._seconds += time.perf_counter() - start
            self._decisions += 1

    def end(self, episode):
        self.agent.end(episode)
        stats = dict(self.agent.stats()) if isinstance(self.agent, Reporting) else {}
        self.results.append(
            SeatResult(self.competitor.name, self.info, self.deck, self._decisions, self._seconds, stats)
        )

    def match_reset(self, match):
        self.deck = match.deck
        self.agent.match_reset(match)

    def side_deck(self, decision):
        self.deck = self.agent.side_deck(decision)
        return self.deck

    def choose_first(self, decision):
        return self.agent.choose_first(decision)

    def match_end(self, result):
        self.agent.match_end(result)

    def close(self):
        close = getattr(self.agent, "close", None)
        if callable(close):
            close()
