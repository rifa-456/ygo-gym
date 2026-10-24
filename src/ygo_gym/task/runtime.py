from copy import deepcopy
from uuid import uuid4
from weakref import ref

from .checkpoint import TaskCheckpoint
from .model import Task, TaskResult, Transition
from .session import TaskSession


def capture(duel):
    from ..dataset.codec import capture as encode

    return encode(duel)


class TaskDuel:
    """Optional live task wrapper. Ordinary Duel operations do not run this evaluator."""

    def __init__(self, duel, task: Task | None = None, *, game_id: str | None = None):
        self.duel = duel
        self.task = Task() if task is None else task
        self.game_id = str(uuid4()) if game_id is None else game_id
        self._session = TaskSession(self.task, self.game_id)
        self._frame = capture(duel)
        self._failed = False
        if duel.terminated:
            self._session.result = TaskResult(tuple(duel.rewards), True, False, "duel_end")

    @property
    def step_count(self):
        return self._session.step_count

    @property
    def failed(self):
        return self._failed

    @property
    def result(self):
        return self._session.result

    @property
    def ended(self):
        return self.result.ended

    @property
    def rewards(self):
        return self.result.rewards

    @property
    def terminated(self):
        return self.result.terminated

    @property
    def truncated(self):
        return self.result.truncated

    @property
    def current_player(self):
        return None if self.ended else self.duel.current_player

    @property
    def actions(self):
        return () if self.ended else self.duel.actions

    def observe(self, player):
        return self.duel.observe(player)

    def state(self):
        return self.duel.state()

    def frame(self):
        return deepcopy(self._frame)

    def validate_position(self):
        if self._failed:
            raise RuntimeError("task execution failed")
        if capture(self.duel) != self._frame:
            self._failed = True
            raise RuntimeError("duel changed outside the task wrapper")

    def step(self, action_index: int) -> Transition:
        if self._failed or self.duel.closed or self.ended:
            raise RuntimeError("task duel is closed, failed, or ended")
        if type(action_index) is not int:
            raise TypeError("action index must be an integer")
        self.validate_position()
        if not 0 <= action_index < len(self._frame["actions"]):
            raise IndexError("action index is out of range")
        before = self._frame
        try:
            self.duel.step(action_index)
            after = capture(self.duel)
            transition = Transition(
                self.game_id,
                self._session.step_count,
                before["current_player"],
                before,
                action_index,
                before["actions"][action_index],
                after,
            )
            self._session.evaluate(deepcopy(transition))
        except BaseException:
            self._failed = True
            raise
        self._frame = after
        return deepcopy(transition)

    def serialize(self, *, provenance=None) -> bytes:
        from ..persistence.task import serialize

        return serialize(self, provenance=provenance)

    @classmethod
    def deserialize(cls, engine, snapshot: bytes, task: Task, *, provenance=None):
        from ..persistence.task import deserialize

        return deserialize(engine, snapshot, task, provenance=provenance)

    def clone(self, *, preserve_rng: bool = False, seed: int | None = None):
        self.validate_position()
        branch = self.duel.clone(preserve_rng=preserve_rng, seed=seed)
        try:
            result = type(self)(branch, self.task, game_id=self.game_id)
            result._session.load_state_dict(self._session.state_dict())
            return result
        except BaseException:
            branch.close()
            raise

    def checkpoint(self):
        self.validate_position()
        return TaskCheckpoint(ref(self), self.duel.checkpoint(), self.frame(), self._session.state_dict())

    def restore(self, checkpoint, *, preserve_rng: bool = False, seed: int | None = None):
        if not isinstance(checkpoint, TaskCheckpoint) or checkpoint.owner() is not self:
            raise ValueError("task checkpoint belongs to a different task duel")
        self.duel.restore(checkpoint.duel, preserve_rng=preserve_rng, seed=seed)
        try:
            self._session.load_state_dict(checkpoint.evaluator)
            self._frame = deepcopy(checkpoint.frame)
            self._failed = False
        except BaseException:
            self.close()
            raise

    def close(self):
        self.duel.close()

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
