from dataclasses import dataclass
from weakref import ReferenceType


@dataclass(frozen=True, slots=True)
class TaskCheckpoint:
    owner: ReferenceType
    duel: object
    frame: dict
    evaluator: dict
