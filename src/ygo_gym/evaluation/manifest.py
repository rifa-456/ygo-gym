import dataclasses
import enum
from collections.abc import Mapping
from datetime import datetime, timezone

from ..provenance import Provenance

FORMAT = "ygo-gym.evaluation"
VERSION = 1


def plain(value):
    """JSON values for configuration objects: dataclasses, enums, mappings, and collections."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(plain(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def manifest(run_id: str, games, provenance: Provenance, dataset: dict | None) -> dict:
    return {
        "format": FORMAT,
        "version": VERSION,
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "complete": False,
        "provenance": provenance.as_record(),
        "dataset": dataset,
        "games": [plain(game.describe()) for game in games],
    }
