from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from ..deck import Deck
from ..engine import Engine
from ..task import Task, TaskDuel
from .initialization import Provenance, setup as describe_setup
from .records import StepRecord
from .schema.tables import SCHEMA_VERSION


class Recorder:
    """Own a fresh duel and its recording; direct mutation of duel bypasses the recorder."""

    @classmethod
    def create(cls, engine: Engine, player1: Deck | None = None, player2: Deck | None = None, seed: int = 0, **options):
        return cls(engine, player1, player2, seed, **options)

    def __init__(
        self,
        engine: Engine,
        player1: Deck | None = None,
        player2: Deck | None = None,
        seed: int = 0,
        *,
        task: Task | None = None,
        setup=None,
        puzzle=None,
        game_id: str | None = None,
        provenance: Provenance | None = None,
    ):
        if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("seed must be an integer fitting uint64")
        self.game_id = str(uuid4()) if game_id is None else game_id
        if not isinstance(self.game_id, str) or not self.game_id:
            raise ValueError("game_id must be a nonempty string")
        self.task = Task() if task is None else task
        self._task_metadata = self.task.describe()
        self._provenance = (provenance or Provenance.capture(engine)).as_record()
        self._created_at = datetime.now(timezone.utc).isoformat()
        if puzzle is not None and (setup is not None or player1 is not None or player2 is not None):
            raise ValueError("puzzle, setup, and decks cannot be combined")
        source = source_name = None
        if puzzle is not None:
            from ..puzzle import Puzzle

            if not isinstance(puzzle, Puzzle):
                raise TypeError("puzzle must be a Puzzle")
            source, source_name = puzzle.to_lua(), puzzle.name
        elif setup is not None:
            from ..setup import DuelSetup

            if player1 is not None or player2 is not None:
                raise ValueError("setup and decks cannot be combined")
            if not isinstance(setup, DuelSetup):
                raise TypeError("setup must be a DuelSetup")
            source, source_name = setup.to_lua(), "ygo-gym.setup"
        self.duel = (
            engine._create_scripted(source, source_name, seed) if source is not None
            else engine.create_duel(player1, player2, seed=seed)
        )
        try:
            self.environment = TaskDuel(self.duel, self.task, game_id=self.game_id)
            self._initial = self.environment.frame()
        except BaseException:
            self.duel.close()
            raise
        self._setup = describe_setup(
            player1, player2, seed, self._initial["state"]["duel_options"],
            source=source, source_name=source_name,
        )
        self._last = self._initial
        self._steps = []
        self._engine = engine
        self._initial_task_state = self.environment._session.state_dict()
        self._task_states = []
        self._closed = False

    @property
    def actions(self):
        return () if self.ended else self.duel.actions

    @property
    def current_player(self):
        return None if self.ended else self.duel.current_player

    @property
    def rewards(self):
        return self.environment.result.rewards

    @property
    def terminated(self):
        return self.environment.result.terminated

    @property
    def truncated(self):
        return self.environment.result.truncated

    @property
    def ended(self):
        return self.environment.result.ended

    def observe(self, player):
        return self.duel.observe(player)

    def step(self, action_index: int) -> StepRecord:
        if self._closed:
            raise RuntimeError("recording is closed")
        self._validate_history()
        transition = self.environment.step(action_index)
        row = asdict(transition)
        result = self.environment.result.as_record()
        row["result"] = result
        row["recorded_result"] = deepcopy(result)
        self._steps.append(row)
        self._task_states.append(self.environment._session.state_dict())
        self._last = row["after"]
        return deepcopy(row)

    def _validate_history(self):
        if self.environment.step_count != len(self._steps) or self.environment.frame() != self._last:
            raise RuntimeError("task changed outside recorder; trajectory cannot be recorded")

    def steps(self):
        for row in self._steps:
            yield deepcopy(row)

    def game(self) -> dict:
        return deepcopy(
            {
                "game_id": self.game_id,
                "schema_version": SCHEMA_VERSION,
                "created_at": self._created_at,
                "setup": self._setup,
                "provenance": self._provenance,
                "task": self._task_metadata,
                "recorded_task": self._task_metadata,
                "initial": self._initial,
                "step_count": len(self._steps),
                "recording_status": "complete" if self.ended else "partial",
                "result": self.environment.result.as_record(),
                "outcome": self._last["outcome"],
            }
        )

    def save(self, path: str | Path, *, snapshot_every: int | None = None, append: bool = True) -> None:
        if snapshot_every is not None:
            if type(snapshot_every) is not int or snapshot_every < 1:
                raise ValueError("snapshot_every must be a positive integer or None")

        self._validate_history()
        if not self._closed:
            self.environment.validate_position()
        if self.environment.failed:
            raise RuntimeError("cannot save a failed recording")
        from .snapshots import generate
        from .storage.writing import save

        snapshots = () if snapshot_every is None else generate(self, snapshot_every)
        save(path, self.game(), self.steps(), append=append, snapshots=snapshots)

    def close(self):
        self.duel.close()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
