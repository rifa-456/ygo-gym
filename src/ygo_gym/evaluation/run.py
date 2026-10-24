import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .manifest import FORMAT, VERSION
from .result import GameResult

MANIFEST = "manifest.json"
GAMES = "games.parquet"
DECK = pa.struct([("main", pa.list_(pa.uint32())), ("extra", pa.list_(pa.uint32())), ("side", pa.list_(pa.uint32()))])
SEAT = pa.struct([
    ("competitor", pa.string()), ("agent", pa.string()), ("agent_version", pa.string()),
    ("agent_config", pa.string()), ("deck", DECK), ("decisions", pa.int64()), ("seconds", pa.float64()),
    ("stats", pa.map_(pa.string(), pa.float64())),
])
REPLAY = pa.struct([
    ("kind", pa.string()), ("players", pa.list_(DECK)), ("config_json", pa.string()), ("source", pa.string()),
    ("source_name", pa.string()), ("seed", pa.uint64()), ("actions", pa.list_(pa.uint32())),
])
SCHEMA = pa.schema([
    ("index", pa.int64()), ("duel", pa.int64()), ("kind", pa.string()), ("scenario", pa.string()),
    ("seed", pa.uint64()), ("seats", pa.list_(SEAT)), ("winner", pa.string()), ("match_winner", pa.string()),
    ("reason", pa.string()), ("solved", pa.bool_()), ("returns", pa.list_(pa.float64())), ("steps", pa.int64()),
    ("terminated", pa.bool_()), ("truncated", pa.bool_()), ("replay", REPLAY), ("game_id", pa.string()),
])


class RunWriter:
    """A run folder: manifest.json plus games.parquet, written as games finish."""

    def __init__(self, path: str | Path, manifest: dict, *, flush_every: int = 64):
        self.path = Path(path)
        if self.path.exists() and any(self.path.iterdir()):
            raise FileExistsError(self.path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.manifest = manifest
        self._write_manifest()
        self._parquet = pq.ParquetWriter(self.path / GAMES, SCHEMA, compression="zstd")
        self._pending: list[dict] = []
        self._flush_every = flush_every

    def append(self, results: list[GameResult]) -> None:
        self._pending.extend(result.record() for result in results)
        if len(self._pending) >= self._flush_every:
            self._flush()

    def close(self, *, complete: bool) -> None:
        self._flush()
        self._parquet.close()
        self.manifest["complete"] = complete
        self._write_manifest()

    def _flush(self) -> None:
        if self._pending:
            self._parquet.write_table(pa.Table.from_pylist(self._pending, schema=SCHEMA))
            self._pending.clear()

    def _write_manifest(self) -> None:
        text = json.dumps(self.manifest, indent=2, sort_keys=True)
        (self.path / MANIFEST).write_text(text + "\n", encoding="utf-8")


def read_run(path: str | Path) -> tuple[dict, tuple[GameResult, ...]]:
    folder = Path(path)
    manifest = json.loads((folder / MANIFEST).read_text(encoding="utf-8"))
    if manifest.get("format") != FORMAT or manifest.get("version") != VERSION:
        raise ValueError("unsupported evaluation run format")
    rows = pq.read_table(folder / GAMES).to_pylist()
    for row in rows:
        for seat in row["seats"]:
            seat["stats"] = dict(seat["stats"])
    return manifest, tuple(GameResult.from_record(row) for row in rows)
