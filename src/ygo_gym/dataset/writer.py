from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..engine import Engine
from ..provenance import Provenance
from ..replay import Replay
from ..task import Task
from .schema.tables import SCHEMA_VERSION
from .snapshots import snapshot
from .storage.writing import save


def setup(replay: Replay, initial: dict) -> dict:
    record = replay.start.record()
    record.pop("kind")
    return {**record, "seed": replay.seed, "duel_options": initial["state"]["duel_options"]}


class DatasetWriter:
    """Materialize replays into a dataset file, one transaction per game.

    Each replay is played again on the engine under the task, so the same path
    serves recording during play and building a dataset from saved replays.
    """

    def __init__(
        self,
        path: str | Path,
        engine: Engine,
        *,
        task: Task | None = None,
        snapshot_every: int | None = None,
        provenance: Provenance | None = None,
        append: bool = True,
    ):
        if snapshot_every is not None and (type(snapshot_every) is not int or snapshot_every < 1):
            raise ValueError("snapshot_every must be a positive integer or None")
        self.path = Path(path)
        self.engine = engine
        self.task = Task() if task is None else task
        self.snapshot_every = snapshot_every
        self.provenance = provenance or Provenance.capture(engine)
        self._append = append

    def write(self, replay: Replay, *, game_id: str | None = None) -> str:
        """Record one game; a task that ends before the replay ends the recording there."""
        game_id = str(uuid4()) if game_id is None else game_id
        if not isinstance(game_id, str) or not game_id:
            raise ValueError("game_id must be a nonempty string")
        duel = replay.start.create(self.engine, replay.seed)
        try:
            episode = replay.start.episode(duel, self.task, game_id)
        except BaseException:
            duel.close()
            raise
        with episode:
            initial = episode.frame()
            steps, snapshots = [], []
            self._snapshot(episode, game_id, 0, snapshots)
            for index in replay.actions:
                if episode.ended:
                    break
                row = asdict(episode.step(index))
                row["result"] = episode.result.as_record()
                row["recorded_result"] = deepcopy(row["result"])
                steps.append(row)
                self._snapshot(episode, game_id, len(steps), snapshots)
            game = {
                "game_id": game_id,
                "schema_version": SCHEMA_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "setup": setup(replay, initial),
                "provenance": self.provenance.as_record(),
                "task": self.task.describe(),
                "recorded_task": self.task.describe(),
                "initial": initial,
                "step_count": len(steps),
                "recording_status": "complete" if episode.ended else "partial",
                "result": episode.result.as_record(),
                "outcome": steps[-1]["after"]["outcome"] if steps else initial["outcome"],
            }
        save(self.path, game, steps, append=self._append, snapshots=snapshots)
        self._append = True
        return game_id

    def _snapshot(self, episode, game_id, boundary, snapshots):
        every = self.snapshot_every
        if every is not None and boundary % every == 0 and not episode.duel.terminated:
            snapshots.append(snapshot(episode, game_id, boundary, self.provenance))
