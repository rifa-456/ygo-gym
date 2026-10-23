from ..task import TaskDuel


class PuzzleDecisionError(RuntimeError):
    """A puzzle requested an unsupported external opposing decision."""


class PuzzleDuel(TaskDuel):
    """A win-this-turn episode with one externally controlled solver, player 0.

    Core SIMPLE_AI handles opposing responses and mandatory choices. This is
    engine automation, not a second supplied agent. Unsupported opposing
    prompts are errors rather than invitations for another policy to act.
    """

    solver = 0

    def __init__(self, duel, task=None, *, game_id=None):
        super().__init__(duel, task, game_id=game_id)
        self._validate_solver()

    @property
    def solved(self):
        if not self.terminated:
            return None
        winner = self.duel.outcome.winner if self.duel.outcome else None
        return winner is not None and int(winner) == self.solver

    def _validate_solver(self):
        player = self.current_player
        if player is not None and int(player) != self.solver:
            self._failed = True
            raise PuzzleDecisionError("puzzle requires an external opposing decision")

    def step(self, action_index):
        transition = super().step(action_index)
        self._validate_solver()
        return transition
