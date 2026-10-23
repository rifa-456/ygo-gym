import random

from ..episode.runner import _play
from .controller import Match
from .model import MatchPhase, MatchStart


def play_match(match: Match, *, agents, seed=0):
    """Run a fresh match; the caller owns its lifetime.

    reset/act/end operate per duel in engine-seat coordinates. match_reset,
    side_deck, choose_first and match_end use stable match-player coordinates.
    Keep cross-duel memory separate from memory cleared by reset().
    """
    if not isinstance(match, Match) or match.closed:
        raise ValueError("play_match requires an open Match")
    if match.duels:
        raise ValueError(
            "play_match starts fresh sessions; use the Match API to resume"
        )
    agents = tuple(agents)
    if len(agents) != 2 or agents[0] is agents[1]:
        raise ValueError("provide a separate agent session per match player")
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("seed must fit uint64")
    for agent in agents:
        methods = ["reset", "act", "end", "match_reset", "match_end"]
        if match.rules.side_decking and match.rules.best_of > 1:
            methods.append("side_deck")
        if match.rules.first_player is None or match.rules.best_of > 1:
            methods.append("choose_first")
        for method in methods:
            if not callable(getattr(agent, method, None)):
                raise TypeError(f"match agent must implement {method}()")
    rng = random.Random(seed)
    for player, agent in enumerate(agents):
        agent.match_reset(
            MatchStart(
                player, match._registered[player], match.rules, rng.getrandbits(64)
            )
        )
    while not match.ended:
        if match.phase == MatchPhase.SIDE_DECKING:
            player = match.current_player
            match.submit_side(player, agents[player].side_deck(match.decision))
        elif match.phase == MatchPhase.FIRST_PLAYER:
            player = match.current_player
            match.choose_first(player, agents[player].choose_first(match.decision))
        elif match.phase == MatchPhase.DUEL:
            result = _play(
                match.duel,
                agents=tuple(agents[p] for p in match.seat_players),
                max_steps=match.rules.max_steps_per_duel,
                seed=rng.getrandbits(64),
                on_step=match._collect_match_kill,
            )
            if result.truncated:
                match.truncate(result.reason, episode=result)
            else:
                match.complete_duel(result)
        else:
            raise RuntimeError("unexpected match phase")
    errors = []
    for agent in agents:
        try:
            agent.match_end(match.result)
        except Exception as error:
            errors.append(error)
    if errors:
        raise ExceptionGroup("match end callbacks failed", errors)
    return match.result
