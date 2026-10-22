from __future__ import annotations

import hashlib
import inspect
import json
import math
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Transition:
    game_id: str
    step_index: int
    acting_player: int
    before: dict
    action_index: int
    action: dict
    after: dict


@dataclass(slots=True)
class TaskContext:
    game_id: str
    config: dict
    memory: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TaskResult:
    rewards: tuple[float, float] = (0.0, 0.0)
    terminated: bool = False
    truncated: bool = False
    reason: str | None = None

    def as_record(self) -> dict:
        return {
            "rewards": list(self.rewards),
            "terminated": self.terminated,
            "truncated": self.truncated,
            "reason": self.reason,
        }

    @property
    def ended(self) -> bool:
        return self.terminated or self.truncated


def function_id(function) -> str | None:
    if function is None:
        return None
    module = getattr(function, "__module__", type(function).__module__)
    qualname = getattr(function, "__qualname__", type(function).__qualname__)
    name = f"{module}:{qualname}"
    try:
        digest = hashlib.sha256(inspect.getsource(function).encode()).hexdigest()
    except (OSError, TypeError):
        return name
    return name + "@" + digest


@dataclass(frozen=True, slots=True)
class Task:
    name: str = "duel"
    version: str = "1"
    config: dict = field(default_factory=dict)
    reward: Callable[[Transition, TaskContext], tuple[float, float]] | None = None
    termination: Callable[[Transition, TaskContext], bool] | None = None
    truncation: Callable[[Transition, TaskContext], bool] | None = None
    max_steps: int | None = None

    def __post_init__(self):
        if not self.name or not isinstance(self.name, str) or not isinstance(self.version, str):
            raise ValueError("task name and version must be strings; name must not be empty")
        if self.max_steps is not None:
            if type(self.max_steps) is not int or self.max_steps < 1:
                raise ValueError("max_steps must be a positive integer or None")
        for function in (self.reward, self.termination, self.truncation):
            if function is not None and not callable(function):
                raise TypeError("task functions must be callable")
        if not isinstance(self.config, dict):
            raise TypeError("task config must be a dictionary")
        json.dumps(self.config, allow_nan=False)

    def describe(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "config_json": json.dumps(self.config, sort_keys=True, allow_nan=False),
            "max_steps": self.max_steps,
            "reward_function": function_id(self.reward),
            "termination_function": function_id(self.termination),
            "truncation_function": function_id(self.truncation),
        }


def rewards(value) -> tuple[float, float]:
    items = tuple(value)
    if len(items) != 2 or any(isinstance(x, bool) for x in items):
        raise ValueError("reward must contain exactly two finite numbers, indexed by player")
    result = tuple(float(x) for x in items)
    if not all(math.isfinite(x) for x in result):
        raise ValueError("reward must contain exactly two finite numbers, indexed by player")
    return result
