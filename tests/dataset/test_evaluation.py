import pytest
from ygo_gym.dataset import Dataset, Recorder
from ygo_gym.task import Task


def reward(transition, context):
    context.memory["count"] = context.memory.get("count", 0) + 1
    count = context.memory["count"] * context.config["scale"]
    return count, -count


def goal(transition, context):
    return transition.step_index == 1


def test_live_and_offline_stateful_tasks_agree(engine, deck, provenance, tmp_path):
    task = Task(name="count", config={"scale": 2}, reward=reward, max_steps=4)
    with Recorder.create(engine, deck, deck, 123, task=task, provenance=provenance) as recorder:
        for _ in range(4):
            recorder.step(0)
        assert recorder.rewards == (8.0, -8.0)
        assert recorder.truncated and not recorder.terminated
        path = tmp_path / "labels.duckdb"
        recorder.save(path)
        with Dataset.open(path) as dataset:
            original = list(dataset.steps())
            assert list(dataset.evaluate(task).steps()) == original
            assert list(dataset.evaluate(task).steps()) == original
            view = dataset.evaluate(Task(name="puzzle", termination=goal))
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
                game = saved.game(recorder.game_id)
                assert game["task"]["name"] == "puzzle"
                assert game["recorded_task"]["name"] == "count"
                assert game["step_count"] == 2
                assert saved.validate_replay(engine, recorder.game_id, provenance=provenance).compatible
            assert list(dataset.steps()) == original
            with pytest.raises(ValueError, match="different"):
                view.save(path)


def test_later_cutoff_does_not_fabricate_unrecorded_steps(recorder, tmp_path):
    for _ in range(4):
        recorder.step(0)
    path = tmp_path / "short.duckdb"
    recorder.save(path)
    with Dataset.open(path) as dataset:
        view = dataset.evaluate(Task(max_steps=1000))
        assert len(list(view.steps())) == 4
        game = view.game(recorder.game_id)
        assert game["recording_status"] == "partial"
        assert not game["result"]["terminated"] and not game["result"]["truncated"]


def test_function_failure_marks_live_recording_unusable(engine, deck, provenance, tmp_path):
    def bad_reward(transition, context):
        raise RuntimeError("bad evaluator")

    with Recorder.create(
        engine, deck, deck, 123, task=Task(reward=bad_reward), provenance=provenance
    ) as recorder:
        with pytest.raises(RuntimeError, match="bad evaluator"):
            recorder.step(0)
        with pytest.raises(RuntimeError, match="failed"):
            recorder.save(tmp_path / "bad.duckdb")
        with pytest.raises(RuntimeError, match="failed"):
            recorder.step(0)
