from ...engine import Duel
from .actions import action
from .positions import observation, state


def capture(duel: Duel) -> dict:
    outcome = duel.outcome
    return {
        "observations": [observation(duel.observe(p)) for p in (0, 1)],
        "state": state(duel.state()),
        "actions": [action(a) for a in duel.actions],
        "current_player": None if duel.current_player is None else int(duel.current_player),
        "decision_kind": None if duel.decision is None else duel.decision.kind.name,
        "engine_terminated": duel.terminated,
        "engine_rewards": list(duel.rewards),
        "outcome": None
        if outcome is None
        else {
            "winner": None if outcome.winner is None else int(outcome.winner),
            "reason": outcome.reason,
            "rewards": list(outcome.rewards),
        },
    }
