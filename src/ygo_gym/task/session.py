from copy import deepcopy

from .model import Task, TaskContext, TaskResult, Transition, rewards


def predicate(function, transition, context) -> bool:
    result = function(transition, context)
    if type(result) is not bool:
        raise TypeError("ending functions must return bool")
    return result


class TaskSession:
    """Evaluate transitions in order; user-managed recurrent state lives in context.memory."""

    def __init__(self, task: Task, game_id: str):
        self.task = task
        self.context = TaskContext(game_id, deepcopy(task.config))
        self.step_count = 0
        self.result = TaskResult()

    def evaluate(self, transition: Transition) -> TaskResult:
        if self.result.ended:
            raise RuntimeError("task has already ended")
        if transition.game_id != self.context.game_id or transition.step_index != self.step_count:
            raise ValueError("task transitions must belong to this game and be evaluated in order")
        memory = deepcopy(self.context.memory)
        try:
            return self._evaluate(transition)
        except BaseException:
            self.context.memory = memory
            raise

    def _evaluate(self, transition: Transition) -> TaskResult:
        task, context = self.task, self.context
        value = (
            transition.after["engine_rewards"] if task.reward is None else task.reward(transition, context)
        )
        reward = rewards(value)
        ended = transition.after["engine_terminated"]
        reason = "duel_end" if ended else None
        if not ended and task.termination is not None and predicate(task.termination, transition, context):
            ended, reason = True, "task_termination"
        truncated = False
        count = self.step_count + 1
        if not ended and task.truncation is not None and predicate(task.truncation, transition, context):
            truncated, reason = True, "task_truncation"
        if not ended and not truncated and task.max_steps is not None and count >= task.max_steps:
            truncated, reason = True, "step_limit"
        self.step_count = count
        self.result = TaskResult(reward, ended, truncated, reason)
        return self.result

    def state_dict(self) -> dict:
        return deepcopy(
            {
                "config": self.context.config,
                "memory": self.context.memory,
                "step_count": self.step_count,
                "result": self.result.as_record(),
            }
        )

    def load_state_dict(self, value: dict) -> None:
        data = deepcopy(value)
        count = data["step_count"]
        if type(count) is not int or count < 0 or not isinstance(data["memory"], dict):
            raise ValueError("invalid task session state")
        result = data["result"]
        if type(result["terminated"]) is not bool or type(result["truncated"]) is not bool:
            raise ValueError("invalid task ending state")
        parsed = TaskResult(
            rewards(result["rewards"]), result["terminated"], result["truncated"], result["reason"]
        )
        self.context.config = data["config"]
        self.context.memory, self.step_count, self.result = data["memory"], count, parsed
