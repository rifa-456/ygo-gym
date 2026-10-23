import operator
import random

from ..agents import AgentEnd, AgentInput
from ..state import Player
from .environment import Environment
from .model import EpisodeResult

PLAYERS = (Player.PLAYER_0, Player.PLAYER_1)


def _validate(agents, max_steps, seed):
    if len(agents) not in (1, 2):
        raise ValueError("agents must contain one session per player")
    if len(agents) == 2 and agents[0] is agents[1]:
        raise ValueError("each seat requires a separate agent session")
    for agent in agents:
        for method in ("reset", "act", "end"):
            if not callable(getattr(agent, method, None)):
                raise TypeError(f"agent must implement {method}()")
    if max_steps is not None and (type(max_steps) is not int or max_steps < 1):
        raise ValueError("max_steps must be a positive integer or None")
    if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFFFFFFFFFF:
        raise ValueError("seed must be an integer fitting uint64")


def _action_index(value, count, player):
    if isinstance(value, bool):
        raise TypeError(f"player {player} returned bool instead of an action index")
    try:
        index = operator.index(value)
    except TypeError as error:
        raise TypeError(
            f"player {player} must return an integer action index"
        ) from error
    if not 0 <= index < count:
        raise IndexError(
            f"player {player} returned action index {index}; expected 0 <= index < {count}"
        )
    return index


def _finish(agents, updates, rewards, result):
    """Notify both sessions and report every callback failure."""
    errors = []
    for index, player in enumerate(PLAYERS[: len(agents)]):
        try:
            agents[index].end(
                AgentEnd(player, tuple(updates[index]), rewards[index], result)
            )
        except Exception as error:
            errors.append(error)
    if errors:
        raise ExceptionGroup("agent end callbacks failed", errors)


def _play(
    duel,
    *,
    agents=None,
    agent=None,
    max_steps: int | None = None,
    seed: int = 0,
    on_step=None,
) -> EpisodeResult:
    """Run fresh agent sessions from the supplied position without closing it.

    Each player receives the initial observation and one masked observation
    after every step, exactly once through act() or end(). History before this
    call is not reconstructed. Action indices refer to the current observation;
    event-card IDs remain local to their original update.

    seed controls agent-session RNG seeds, independently of the duel's RNG.
    max_steps is an external episode budget, counting compound-selection steps
    too. For recorded task truncation, configure Task.max_steps instead.
    Agent errors propagate without manufacturing a game result.
    """
    environment = Environment(duel)
    if (agents is None) == (agent is None):
        raise ValueError("provide agents for a duel or agent for a puzzle")
    if environment.solver is not None:
        if agent is None:
            raise ValueError("puzzles take one solver through agent=")
        agents = (agent,)
    elif agents is None:
        raise ValueError("two-player duels require agents=")
    agents = tuple(agents)
    _validate(agents, max_steps, seed)
    if environment.solver is None and len(agents) != 2:
        raise ValueError("duels require two agent sessions")
    random_source = random.Random(seed)
    for player, agent in zip(PLAYERS[: len(agents)], agents, strict=True):
        agent.reset(player=player, seed=random_source.getrandbits(64))
    updates = [[environment.observe(player)] for player in PLAYERS]
    initial = environment.rewards if environment.ended else (0.0, 0.0)
    pending_rewards = list(initial)
    returns = list(initial)
    player_steps = [0, 0]
    step_count = 0
    while not environment.ended and (max_steps is None or step_count < max_steps):
        player = environment.current_player
        if player not in PLAYERS:
            raise RuntimeError("ongoing duel has no acting player")
        seat = int(player)
        if seat >= len(agents):
            raise RuntimeError("puzzle requested an opposing agent decision")
        actions = environment.actions
        if not actions:
            raise RuntimeError("ongoing duel has no legal actions")
        decision = AgentInput(
            updates[seat][-1], actions, tuple(updates[seat]), pending_rewards[seat]
        )
        index = _action_index(agents[seat].act(decision), len(actions), seat)
        updates[seat].clear()
        pending_rewards[seat] = 0.0
        environment.step(index)
        if on_step is not None:
            on_step()
        step_count += 1
        player_steps[seat] += 1
        rewards = environment.rewards
        for seat, viewer in enumerate(PLAYERS):
            updates[seat].append(environment.observe(viewer))
            pending_rewards[seat] += rewards[seat]
            returns[seat] += rewards[seat]
    limited = max_steps is not None and step_count >= max_steps
    terminated, truncated, reason = environment.ending(limited)
    result = EpisodeResult(
        tuple(returns),
        step_count,
        tuple(player_steps),
        terminated,
        truncated,
        reason,
        environment.duel.outcome,
    )
    _finish(agents, updates, pending_rewards, result)
    return result


def play(duel, *, agents=None, agent=None, max_steps=None, seed=0) -> EpisodeResult:
    """Run one caller-owned episode: agents=(p0, p1) or agent=solver.

    Callbacks receive each player's masked updates, local legal actions, and
    accumulated rewards. seed controls agent randomness. max_steps truncates
    this run without changing the underlying episode's termination semantics.
    """
    return _play(duel, agents=agents, agent=agent, max_steps=max_steps, seed=seed)
