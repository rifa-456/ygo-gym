import random

from ..database import load_card_definitions
from ..deck import Deck
from ..engine import Engine
from ..event import MatchKillEvent
from .model import DuelResult, FirstPlayerInput, MatchPhase, MatchResult, SideDeckInput
from .rules import DrawPolicy, MatchRules


def player_id(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError("match player must be 0 or 1")
    return value


class Match:
    """Own a series of fresh duels and private between-duel decisions.

    Use step() for in-duel actions. Observations and actions retain the current
    duel's coordinates; seat_players maps those seats to stable match players.
    The previous duel stays inspectable until the next one starts or close().
    """

    def __init__(self, engine: Engine, decks, *, rules=None, seed=0):
        if not isinstance(engine, Engine):
            raise TypeError("engine must be an Engine")
        decks = tuple(decks)
        if len(decks) != 2 or not all(isinstance(d, Deck) for d in decks):
            raise ValueError("decks must contain two Deck values")
        if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("seed must fit uint64")
        self.engine = engine
        self.rules = MatchRules() if rules is None else rules
        if not isinstance(self.rules, MatchRules):
            raise TypeError("rules must be MatchRules")
        self._cards = {
            c.code: c
            for path in engine.card_databases
            for c in load_card_definitions(path)
        }
        for deck in decks:
            self.rules.decks.validate(deck, self._cards)
        self.seed = seed
        self._registered = decks
        self._decks = decks
        self._submitted = {}
        self._random = random.Random(seed)
        self._chooser = self.rules.initial_chooser
        if self._chooser is None:
            self._chooser = self._random.randrange(2)
        self._duel = None
        self._seat_players = (0, 1)
        self._duels = []
        self._scores = [0, 0]
        self._draws = 0
        self._result = None
        self._closed = False
        self._match_kill = None
        self._phase = MatchPhase.FIRST_PLAYER
        if self.rules.first_player is not None:
            self.choose_first(self._chooser, self.rules.first_player)

    @property
    def phase(self):
        return self._phase

    @property
    def duel(self):
        return self._duel

    @property
    def seat_players(self):
        return self._seat_players

    @property
    def scores(self):
        return tuple(self._scores)

    @property
    def duels(self):
        return tuple(self._duels)

    @property
    def result(self):
        return self._result

    @property
    def ended(self):
        return self._result is not None

    @property
    def terminated(self):
        return self.result is not None and self.result.terminated

    @property
    def truncated(self):
        return self.result is not None and self.result.truncated

    @property
    def rewards(self):
        return (0.0, 0.0) if self.result is None else self.result.returns

    @property
    def closed(self):
        return self._closed

    @property
    def current_player(self):
        if self.closed or self.ended:
            return None
        if self.phase == MatchPhase.DUEL:
            seat = self.duel.current_player
            return None if seat is None else self.seat_players[int(seat)]
        if self.phase == MatchPhase.FIRST_PLAYER:
            return self._chooser
        return next(p for p in (0, 1) if p not in self._submitted)

    @property
    def decision(self):
        if self.phase == MatchPhase.SIDE_DECKING:
            return self.side_deck_input(self.current_player)
        if self.phase == MatchPhase.FIRST_PLAYER:
            return FirstPlayerInput(self._chooser, self.scores, self.duels)
        if self.phase == MatchPhase.DUEL:
            return self.duel.decision
        return None

    @property
    def actions(self):
        return self.duel.actions if self.phase == MatchPhase.DUEL else ()

    def observe(self, player):
        player_id(player)
        if self.closed or self.duel is None:
            raise RuntimeError("no open duel to observe")
        return self.duel.observe(self.seat_players.index(player))

    def side_deck_input(self, player):
        player_id(player)
        if self.closed or self.phase != MatchPhase.SIDE_DECKING:
            raise RuntimeError("match is not accepting side decks")
        return SideDeckInput(
            player, self._decks[player], self.scores, self.duels, self.rules
        )

    def submit_side(self, player, deck):
        self.side_deck_input(player)
        if player in self._submitted:
            raise RuntimeError("this player has already submitted a side deck")
        self.rules.decks.validate_side(self._registered[player], deck, self._cards)
        self._submitted[player] = deck
        if len(self._submitted) == 2:
            self._decks = tuple(self._submitted[p] for p in (0, 1))
            self._submitted.clear()
            self._phase = MatchPhase.FIRST_PLAYER

    def choose_first(self, player, first_player):
        player_id(player)
        player_id(first_player)
        if (
            self.closed
            or self.phase != MatchPhase.FIRST_PLAYER
            or player != self._chooser
        ):
            raise RuntimeError("this player is not choosing who goes first")
        seats = (first_player, 1 - first_player)
        config = self.rules.duel.for_seats(seats)
        duel_seed = self._random.getrandbits(64)
        duel = self.engine.create_duel(
            *(self._decks[p] for p in seats), seed=duel_seed, config=config
        )
        if self.duel is not None:
            self.duel.close()
        self._duel = duel
        self._seat_players, self._duel_seed = seats, duel_seed
        self._match_kill = None
        self._phase = MatchPhase.DUEL

    def step(self, action_index):
        if type(action_index) is not int:
            raise TypeError("action index must be an integer")
        if self.closed or self.phase != MatchPhase.DUEL:
            raise RuntimeError("match is not awaiting a duel action")
        self.duel.step(action_index)
        self._collect_match_kill()
        if self.duel.terminated:
            self.complete_duel()

    def _collect_match_kill(self):
        observation = (
            self.duel.observe(0) if self.duel.terminated else self.duel.observation
        )
        for event in observation.events:
            if isinstance(event, MatchKillEvent):
                self._match_kill = event.code

    def complete_duel(self, episode=None):
        if self.closed or self.phase != MatchPhase.DUEL or not self.duel.terminated:
            raise RuntimeError("no completed duel to collect")
        self._collect_match_kill()
        winner = self.duel.outcome.winner
        winner = None if winner is None else self.seat_players[int(winner)]
        self._record(winner, "duel_end", episode)

    def _record(self, winner, reason, episode=None):
        result = DuelResult(
            len(self._duels),
            self._duel_seed,
            self.seat_players,
            winner,
            reason,
            episode,
            self._match_kill,
        )
        self._duels.append(result)
        if winner is None:
            self._draws += 1
        else:
            self._scores[winner] += 1
            self._chooser = 1 - winner
        if (
            self._match_kill is not None
            and winner is not None
            and self.rules.match_kill
        ):
            self._finish(winner, "match_kill")
            return
        if winner is not None and self._scores[winner] >= (self.rules.best_of + 1) // 2:
            self._finish(winner, "wins")
            return
        counted = len(self._duels)
        if self.rules.draw_policy == DrawPolicy.REPLAY:
            counted -= self._draws
        if counted >= self.rules.best_of or (
            self.rules.max_duels is not None
            and len(self._duels) >= self.rules.max_duels
        ):
            winner = (
                None
                if self._scores[0] == self._scores[1]
                else int(self._scores[1] > self._scores[0])
            )
            self._finish(winner, "duel_limit")
            return
        self._phase = (
            MatchPhase.SIDE_DECKING
            if self.rules.side_decking
            else MatchPhase.FIRST_PLAYER
        )

    def _finish(self, winner, reason, *, truncated=False):
        self._result = MatchResult(
            winner,
            self.scores,
            self._draws,
            self.duels,
            not truncated,
            truncated,
            reason,
        )
        self._phase = MatchPhase.FINISHED

    def truncate(self, reason="step_limit", *, episode=None):
        if self.closed or self.ended:
            raise RuntimeError("match is closed or ended")
        if episode is not None:
            self._duels.append(
                DuelResult(
                    len(self._duels),
                    self._duel_seed,
                    self.seat_players,
                    None,
                    reason,
                    episode,
                    self._match_kill,
                )
            )
        self._finish(None, reason, truncated=True)

    def surrender(self, player, *, entire_match=False):
        if type(entire_match) is not bool:
            raise TypeError("entire_match must be bool")
        player_id(player)
        if self.closed or self.ended:
            raise RuntimeError("match is closed or ended")
        if entire_match:
            self._finish(1 - player, "surrender")
        elif self.phase == MatchPhase.DUEL and not self.duel.terminated:
            self._record(1 - player, "surrender")
        else:
            raise RuntimeError("no active duel to surrender")

    def close(self):
        if self.duel is not None:
            self.duel.close()
        self._closed = True
        if not self.ended:
            self._phase = MatchPhase.CLOSED

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
