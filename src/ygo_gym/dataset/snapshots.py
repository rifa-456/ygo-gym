import json

from ..persistence import inspect_snapshot
from ..task import TaskDuel
from .codec import capture
from .initialization import Provenance, create_duel

CODEC = "ygo.engine.snapshot.v1"


def generate(recorder, frequency: int):
    provenance = Provenance(**recorder._provenance)
    with create_duel(recorder._engine, recorder._setup) as duel:
        expected = recorder._initial
        for boundary in range(len(recorder._steps) + 1):
            if capture(duel) != expected:
                raise RuntimeError(f"snapshot replay diverged at boundary {boundary}")
            if boundary % frequency == 0 and not duel.terminated:
                environment = TaskDuel(duel, recorder.task, game_id=recorder.game_id)
                state = recorder._initial_task_state if boundary == 0 else recorder._task_states[boundary - 1]
                environment._session.load_state_dict(state)
                payload = environment.serialize(provenance=provenance)
                info = inspect_snapshot(payload)
                yield {
                    "game_id": recorder.game_id,
                    "boundary": boundary,
                    "codec": CODEC,
                    "compatibility": json.dumps(info.compatibility, sort_keys=True),
                    "payload": payload,
                }
            if boundary < len(recorder._steps):
                step = recorder._steps[boundary]
                duel.step(step["action_index"])
                expected = step["after"]


def restore(dataset, engine, game_id: str, boundary: int, *, task=None, provenance=None):
    if type(boundary) is not int or boundary < 0:
        raise ValueError("boundary must be a nonnegative integer")
    rows = dataset.snapshots(game_id)
    try:
        row = next((row for row in rows if row["boundary"] == boundary), None)
    finally:
        rows.close()
    if row is None:
        raise KeyError((game_id, boundary))
    if row["codec"] != CODEC:
        raise ValueError("unsupported dataset snapshot codec")
    if task is None:
        return engine.deserialize(row["payload"], provenance=provenance)
    return TaskDuel.deserialize(engine, row["payload"], task, provenance=provenance)
