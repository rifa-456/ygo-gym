import pytest
from ygo_gym import Deck
from ygo_gym.action import ActionKind as K
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.dataset.codec import capture
from ygo_gym.state import Location
from ygo_gym.task import Task

from tests.duel.comparison import choose

from .conftest import recorded


def test_complete_transition_roundtrip_and_visibility(engine, deck, provenance, tmp_path):
    with engine.create_duel(deck, deck, seed=123) as duel:
        initial = capture(duel)
        for kinds in [
            (K.SUMMON,),
            (K.SELECT_ZONE,),
            (K.PASS, K.END_PHASE),
            (K.PASS, K.NO, K.END_PHASE, K.SELECT_ZONE),
        ]:
            duel.step(choose(duel, *kinds))
        replay, final = duel.replay(), capture(duel)
    assert len(initial["state"]["cards"]) == 80
    for viewer, obs in enumerate(initial["observations"]):
        own = [c for c in obs["cards"] if c["location"] == int(Location.HAND) and c["controller"] == viewer]
        other = [c for c in obs["cards"] if c["location"] == int(Location.HAND) and c["controller"] != viewer]
        assert len(own) == len(other) == 5
        assert all(c["code"] for c in own)
        assert all(c["code"] == 0 for c in other)
    path = tmp_path / "duels.duckdb"
    game, rows = recorded(engine, path, replay, provenance)
    assert game["initial"] == initial
    assert rows[-1]["after"] == final
    assert [row["action_index"] for row in rows] == list(replay.actions)
    assert game["recording_status"] == "partial"
    assert all(r["action"] == r["before"]["actions"][r["action_index"]] for r in rows)
    for left, right in zip(rows, rows[1:]):
        assert left["after"] == right["before"]
    with Dataset.open(path) as dataset:
        assert list(dataset.snapshots()) == []
    assert [p.name for p in tmp_path.iterdir()] == ["duels.duckdb"]


def test_partial_compound_selection_and_random_events(engine, deck, provenance, tmp_path):
    with engine.create_duel(Deck((100000001,) * 40), deck, seed=123) as duel:
        duel.step(choose(duel, K.ACTIVATE))
        for _ in range(16):
            if any(a.kind == K.SELECT_CARD for a in duel.actions):
                break
            duel.step(choose(duel, K.SELECT_ZONE, K.PASS, K.NO))
        else:
            pytest.fail("selection not reached")
        selected = len(duel.replay().actions)
        duel.step(choose(duel, K.SELECT_CARD))
        for _ in range(12):
            if duel.terminated:
                break
            duel.step(choose(duel, K.SELECT_CARD, K.CONFIRM, K.YES, K.PASS, K.SELECT_ZONE, K.END_PHASE))
        replay = duel.replay()
    path = tmp_path / "random.duckdb"
    game, rows = recorded(engine, path, replay, provenance, task=Task(max_steps=24))
    assert rows[selected]["after"]["state"]["pending_actions"]
    assert rows[selected]["after"]["state"]["events"]["events"] == []
    assert any(e["variant"] == "RandomEvent" for r in rows for e in r["after"]["state"]["events"]["events"])
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, game["game_id"], provenance=provenance)
        assert report.compatible, report


def test_terminal_transition(engine, deck, provenance, tmp_path):
    with engine.create_duel(deck, deck, seed=123) as duel:
        for _ in range(800):
            if duel.terminated:
                break
            duel.step(choose(duel, K.END_PHASE, K.PASS, K.NO, K.SELECT_ZONE, K.CONFIRM, K.SELECT_CARD))
        assert duel.terminated
        replay, rewards = duel.replay(), list(duel.rewards)
    path = tmp_path / "terminal.duckdb"
    game, rows = recorded(engine, path, replay, provenance)
    assert rows[-1]["after"]["engine_terminated"]
    assert rows[-1]["after"]["current_player"] is None
    assert rows[-1]["after"]["actions"] == []
    assert rows[-1]["result"]["rewards"] == rewards
    assert game["outcome"] is not None and game["recording_status"] == "complete"
    with Dataset.open(path) as dataset:
        assert dataset.validate_replay(engine, game["game_id"], provenance=provenance).compatible


def test_task_ending_before_the_replay_ends_the_recording(engine, replay, provenance, tmp_path):
    game, rows = recorded(engine, tmp_path / "short.duckdb", replay, provenance, task=Task(max_steps=2))
    assert len(rows) == game["step_count"] == 2
    assert game["recording_status"] == "complete"
    assert game["result"]["truncated"] and game["result"]["reason"] == "step_limit"


def test_invalid_replay_writes_nothing(engine, replay, provenance, tmp_path):
    broken = type(replay)(replay.start, replay.seed, (*replay.actions, 100000))
    with pytest.raises(IndexError):
        DatasetWriter(tmp_path / "broken.duckdb", engine, provenance=provenance).write(broken)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("frequency", [1, 50])
def test_snapshot_generation(engine, replay, provenance, tmp_path, frequency):
    start = type(replay)(replay.start, replay.seed, ())
    path = tmp_path / "snapshots.duckdb"
    game, _ = recorded(engine, path, start, provenance, snapshot_every=frequency)
    with Dataset.open(path) as dataset:
        rows = list(dataset.snapshots(game["game_id"]))
        assert [row["boundary"] for row in rows] == [0]
        with dataset.restore(engine, game["game_id"], 0) as restored:
            assert capture(restored) == game["initial"]
