from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from ..dataset import DatasetWriter
from ..engine import Engine
from ..provenance import Provenance
from ..task import Task
from .games import Game
from .manifest import manifest
from .report import Report
from .result import GameResult
from .run import RunWriter


def evaluate(
    games: Iterable[Game],
    engine: Engine,
    *,
    path: str | Path | None = None,
    dataset: str | Path | None = None,
    task: Task | None = None,
    snapshot_every: int | None = None,
    provenance: Provenance | None = None,
) -> Report:
    """Play games in order and report them.

    path writes a run folder with manifest.json and games.parquet as games
    finish. dataset also records each duel's trajectory there, from its replay,
    under task with optional snapshots; results link to it through game_id.
    """
    games = tuple(games)
    provenance = provenance or Provenance.capture(engine)
    run_id = str(uuid4())
    writer = None
    recording = None
    if dataset is not None:
        writer = DatasetWriter(dataset, engine, task=task, snapshot_every=snapshot_every, provenance=provenance)
        recording = {"path": str(dataset), "task": writer.task.describe(), "snapshot_every": snapshot_every}
    run = None if path is None else RunWriter(path, manifest(run_id, games, provenance, recording))
    results, complete = [], False
    try:
        for index, game in enumerate(games):
            rows = game.play(engine, index)
            if writer is not None:
                rows = [record(writer, row, f"{run_id}/{index}/{row.duel}") for row in rows]
            if run is not None:
                run.append(rows)
            results.extend(rows)
        complete = True
    finally:
        if run is not None:
            run.close(complete=complete)
    data = run.manifest if run is not None else manifest(run_id, games, provenance, recording)
    data["complete"] = complete
    return Report(data, tuple(results))


def record(writer: DatasetWriter, row: GameResult, game_id: str) -> GameResult:
    if row.replay is None:
        return row
    return replace(row, game_id=writer.write(row.replay, game_id=game_id))
