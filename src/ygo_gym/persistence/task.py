import base64
import math


def encode(value):
    if value is None or type(value) in (bool, int, str):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, bytes):
        return {"type": "bytes", "value": base64.b64encode(value).decode()}
    if isinstance(value, (tuple, list)):
        return {"type": type(value).__name__, "value": [encode(item) for item in value]}
    if isinstance(value, dict):
        return {"type": "dict", "value": [[encode(k), encode(v)] for k, v in value.items()]}
    raise TypeError(f"task snapshot cannot store {type(value).__name__}")


def decode(value):
    if not isinstance(value, dict):
        return value
    kind, items = value["type"], value["value"]
    if kind == "bytes":
        return base64.b64decode(items, validate=True)
    if kind == "list":
        return [decode(item) for item in items]
    if kind == "tuple":
        return tuple(decode(item) for item in items)
    if kind == "dict":
        return {decode(k): decode(v) for k, v in items}
    raise ValueError("unsupported task snapshot value")


def serialize(environment, *, provenance=None) -> bytes:
    from .compatibility import fingerprint
    from .format import pack

    environment.validate_position()
    if environment.duel._engine is None:
        raise RuntimeError("task serialization requires the originating Engine")
    metadata = {
        "task": environment.task.describe(),
        "episode_kind": "puzzle" if getattr(environment, "solver", None) == 0 else "duel",
        "game_id": environment.game_id,
        "session": encode(environment._session.state_dict()),
    }
    return pack(
        environment.duel._native_duel.serialize(),
        fingerprint(environment.duel._engine, provenance),
        metadata,
    )


def deserialize(engine, snapshot: bytes, task, *, provenance=None):
    from ..task.runtime import TaskDuel
    from .format import SnapshotError, inspect_snapshot

    info = inspect_snapshot(snapshot)
    metadata = info.metadata
    if not isinstance(metadata, dict) or metadata.get("task") != task.describe():
        raise SnapshotError("snapshot task does not match the supplied Task")
    state = decode(metadata["session"])
    duel = engine.deserialize(snapshot, provenance=provenance)
    try:
        from ..puzzle import PuzzleDuel

        session_type = PuzzleDuel if metadata.get("episode_kind") == "puzzle" else TaskDuel
        environment = session_type(duel, task, game_id=metadata["game_id"])
        environment._session.load_state_dict(state)
        return environment
    except BaseException:
        duel.close()
        raise
