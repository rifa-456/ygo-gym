from .actions import ACTION
from .positions import FRAME
from .types import OUTCOME, RESULT, struct

SCHEMA_VERSION = 1
FORMAT = "ygo-gym.dataset"
DECK = struct({"main": "BIGINT[]", "extra": "BIGINT[]", "side": "BIGINT[]"})
SETUP = struct({"seed": "UBIGINT", "players": DECK + "[]", "duel_options": "UBIGINT"})
PROVENANCE = struct(
    {
        "package_version": "VARCHAR",
        "core_major": "BIGINT",
        "core_minor": "BIGINT",
        "native_sha256": "VARCHAR",
        "database_sha256": "VARCHAR",
        "scripts_sha256": "VARCHAR[]",
    }
)
TASK = struct(
    {
        "name": "VARCHAR",
        "version": "VARCHAR",
        "config_json": "VARCHAR",
        "max_steps": "BIGINT",
        "reward_function": "VARCHAR",
        "termination_function": "VARCHAR",
        "truncation_function": "VARCHAR",
    }
)
TABLES = {
    "games": {
        "game_id": "VARCHAR PRIMARY KEY",
        "schema_version": "INTEGER NOT NULL",
        "created_at": "VARCHAR NOT NULL",
        "setup": SETUP + " NOT NULL",
        "provenance": PROVENANCE + " NOT NULL",
        "task": TASK + " NOT NULL",
        "recorded_task": TASK + " NOT NULL",
        "initial": FRAME + " NOT NULL",
        "step_count": "BIGINT NOT NULL CHECK (step_count >= 0)",
        "recording_status": "VARCHAR NOT NULL",
        "result": RESULT + " NOT NULL",
        "outcome": OUTCOME,
    },
    "steps": {
        "game_id": "VARCHAR NOT NULL REFERENCES games(game_id)",
        "step_index": "BIGINT NOT NULL CHECK (step_index >= 0)",
        "acting_player": "BIGINT NOT NULL",
        "before": FRAME + " NOT NULL",
        "action_index": "BIGINT NOT NULL CHECK (action_index >= 0)",
        "action": ACTION + " NOT NULL",
        "after": FRAME + " NOT NULL",
        "result": RESULT + " NOT NULL",
        "recorded_result": RESULT + " NOT NULL",
    },
    "snapshots": {
        "game_id": "VARCHAR NOT NULL REFERENCES games(game_id)",
        "boundary": "BIGINT NOT NULL CHECK (boundary >= 0)",
        "codec": "VARCHAR NOT NULL",
        "compatibility": "VARCHAR NOT NULL",
        "payload": "BLOB NOT NULL",
    },
}


def create_sql(name: str) -> str:
    fields = [f'"{key}" {kind}' for key, kind in TABLES[name].items()]
    if name in ("steps", "snapshots"):
        key = "step_index" if name == "steps" else "boundary"
        fields.append(f"PRIMARY KEY (game_id, {key})")
    return f'CREATE TABLE "{name}" (' + ", ".join(fields) + ")"
