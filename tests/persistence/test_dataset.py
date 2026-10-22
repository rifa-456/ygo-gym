import pytest

pytest.importorskip("duckdb")

from ygo_gym.dataset import Dataset, Recorder
from ygo_gym.dataset.codec import capture
from ygo_gym.dataset.initialization import Provenance
from ygo_gym.task import Task


@pytest.mark.parametrize("interval", [1, 2, 50])
def test_snapshot_intervals(engine, deck, tmp_path, interval):
    provenance = Provenance.capture(engine)
    path = tmp_path / "games.duckdb"
    task = Task(max_steps=5)
    with Recorder.create(engine, deck, deck, seed=123, task=task, provenance=provenance) as recorder:
        for _ in range(5):
            recorder.step(0)
        recorder.close()
        recorder.save(path, snapshot_every=interval)
        expected = [recorder.game()["initial"], *[step["after"] for step in recorder.steps()]]
        with Dataset.open(path) as dataset:
            rows = list(dataset.snapshots(recorder.game_id))
            assert [row["boundary"] for row in rows] == list(range(0, 6, interval))
            for row in rows:
                boundary = row["boundary"]
                with dataset.restore(engine, recorder.game_id, boundary, provenance=provenance) as loaded:
                    assert capture(loaded) == expected[boundary]
                with dataset.restore(engine, recorder.game_id, boundary, task=task, provenance=provenance) as loaded:
                    assert loaded.step_count == boundary
            with pytest.raises(KeyError):
                dataset.restore(engine, recorder.game_id, 100, provenance=provenance)
    assert list(tmp_path.iterdir()) == [path]
