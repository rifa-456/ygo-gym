import json

from ..persistence import inspect_snapshot
from ..task import TaskDuel

CODEC = "ygo.engine.snapshot.v1"


def snapshot(environment, game_id: str, boundary: int, provenance) -> dict:
    payload = environment.serialize(provenance=provenance)
    return {
        "game_id": game_id,
        "boundary": boundary,
        "codec": CODEC,
        "compatibility": json.dumps(inspect_snapshot(payload).compatibility, sort_keys=True),
        "payload": payload,
    }


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
