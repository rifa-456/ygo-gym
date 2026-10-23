from ..engine import Duel
from ..task import TaskDuel


class Environment:
    """Normalize the existing game, task, and recording APIs for the runner."""

    def __init__(self, value):
        from ..dataset import Recorder

        if isinstance(value, Duel):
            self.duel, self.session = value, None
        elif isinstance(value, TaskDuel):
            self.duel, self.session = value.duel, value
        elif isinstance(value, Recorder):
            self.duel, self.session = value.duel, value.environment
        else:
            raise TypeError("play expects a Duel, TaskDuel, or Recorder")
        if self.duel.closed:
            raise RuntimeError("cannot play a closed duel")
        if self.session is not None:
            self.session.validate_position()
        self.target = value

    @property
    def ended(self):
        return self.duel.terminated if self.session is None else self.session.ended

    @property
    def current_player(self):
        return self.target.current_player

    @property
    def actions(self):
        return tuple(self.target.actions)

    @property
    def rewards(self):
        return tuple(self.target.rewards)

    def observe(self, player):
        return self.target.observe(int(player))

    def step(self, action):
        self.target.step(action)

    def ending(self, limited):
        if self.session is None:
            terminated, truncated = self.duel.terminated, False
            reason = "duel_end" if terminated else None
        else:
            result = self.session.result
            terminated, truncated, reason = (
                result.terminated,
                result.truncated,
                result.reason,
            )
        if limited and not (terminated or truncated):
            truncated, reason = True, "step_limit"
        return terminated, truncated, reason
