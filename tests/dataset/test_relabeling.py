import pytest
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.task import Task

from .conftest import recorded


def reward(transition, context):
    context.memory["count"] = context.memory.get("count", 0) + 1
    count = context.memory["count"] * context.config["scale"]
    return count, -count


def goal(transition, context):
    return transition.step_index == 1


def test_recorded_and_relabeled_stateful_tasks_agree(engine, replay, provenance, tmp_path):
    task = Task(name="count", config={"scale": 2}, reward=reward, max_steps=4)
    path = tmp_path / "labels.duckdb"
    game, original = recorded(engine, path, replay, provenance, task=task)
    assert game["result"]["rewards"] == [8.0, -8.0]
    assert game["result"]["truncated"] and not game["result"]["terminated"]
    with Dataset.open(path) as dataset:
        assert list(dataset.relabel(task).steps()) == original
        assert list(dataset.relabel(task).steps()) == original
        view = dataset.relabel(Task(name="puzzle", termination=goal))
        derived = list(view.steps())
        assert len(derived) == 2
        assert derived[-1]["result"]["terminated"]
        assert not derived[-1]["result"]["truncated"]
        assert derived[-1]["result"]["rewards"] == [0.0, 0.0]
        assert derived[-1]["recorded_result"] == original[1]["recorded_result"]
        target = tmp_path / "derived.duckdb"
        view.save(target)
        with Dataset.open(target) as saved:
            assert list(saved.steps()) == derived
            relabeled = saved.game(game["game_id"])
            assert relabeled["task"]["name"] == "puzzle"
            assert relabeled["recorded_task"]["name"] == "count"
            assert relabeled["step_count"] == 2
            assert saved.validate_replay(engine, game["game_id"], provenance=provenance).compatible
        assert list(dataset.steps()) == original
        with pytest.raises(ValueError, match="different"):
            view.save(path)


def test_later_cutoff_does_not_fabricate_unrecorded_steps(engine, replay, provenance, tmp_path):
    path = tmp_path / "short.duckdb"
    game, _ = recorded(engine, path, replay, provenance)
    with Dataset.open(path) as dataset:
        view = dataset.relabel(Task(max_steps=1000))
        assert len(list(view.steps())) == 4
        relabeled = view.game(game["game_id"])
        assert relabeled["recording_status"] == "partial"
        assert not relabeled["result"]["terminated"] and not relabeled["result"]["truncated"]


def test_task_failure_writes_nothing(engine, replay, provenance, tmp_path):
    def bad_reward(transition, context):
        raise RuntimeError("bad evaluator")

    writer = DatasetWriter(tmp_path / "bad.duckdb", engine, task=Task(reward=bad_reward), provenance=provenance)
    with pytest.raises(RuntimeError, match="bad evaluator"):
        writer.write(replay)
    assert list(tmp_path.iterdir()) == []
