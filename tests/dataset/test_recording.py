import pytest
from ygo_gym import Deck
from ygo_gym.action import ActionKind as K
from ygo_gym.dataset import Dataset, Recorder
from ygo_gym.state import Location
from ygo_gym.task import Task

from tests.duel.comparison import choose


def test_complete_transition_roundtrip_and_visibility(recorder, tmp_path):
    initial = recorder.game()["initial"]
    assert len(initial["state"]["cards"]) == 80
    for viewer, obs in enumerate(initial["observations"]):
        own = [c for c in obs["cards"] if c["location"] == int(Location.HAND) and c["controller"] == viewer]
        other = [c for c in obs["cards"] if c["location"] == int(Location.HAND) and c["controller"] != viewer]
        assert len(own) == len(other) == 5
        assert all(c["code"] for c in own)
        assert all(c["code"] == 0 for c in other)
    for kinds in [
        (K.SUMMON,),
        (K.SELECT_ZONE,),
        (K.PASS, K.END_PHASE),
        (K.PASS, K.NO, K.END_PHASE, K.SELECT_ZONE),
    ]:
        if recorder.ended:
            break
        recorder.step(choose(recorder, *kinds))
    rows = list(recorder.steps())
    path = tmp_path / "duels.duckdb"
    recorder.save(path)
    with Dataset.open(path) as dataset:
        assert dataset.game(recorder.game_id) == recorder.game()
        assert list(dataset.steps()) == rows
        assert list(dataset.snapshots()) == []
    assert all(r["action"] == r["before"]["actions"][r["action_index"]] for r in rows)
    assert rows[0]["before"] == initial
    for left, right in zip(rows, rows[1:]):
        assert left["after"] == right["before"]
    assert [p.name for p in tmp_path.iterdir()] == ["duels.duckdb"]


def test_partial_compound_selection_and_random_events(engine, deck, provenance, tmp_path):
    with Recorder.create(
        engine, Deck((100000001,) * 40), deck, 123, task=Task(max_steps=24), provenance=provenance
    ) as recorder:
        recorder.step(choose(recorder, K.ACTIVATE))
        for _ in range(16):
            if any(a.kind == K.SELECT_CARD for a in recorder.actions):
                break
            recorder.step(choose(recorder, K.SELECT_ZONE, K.PASS, K.NO))
        else:
            pytest.fail("selection not reached")
        row = recorder.step(choose(recorder, K.SELECT_CARD))
        assert row["after"]["state"]["pending_actions"]
        assert row["after"]["state"]["events"]["events"] == []
        for _ in range(12):
            if recorder.ended:
                break
            recorder.step(
                choose(recorder, K.SELECT_CARD, K.CONFIRM, K.YES, K.PASS, K.SELECT_ZONE, K.END_PHASE)
            )
        path = tmp_path / "random.duckdb"
        recorder.save(path)
        rows = list(recorder.steps())
        assert any(
            e["variant"] == "RandomEvent" for r in rows for e in r["after"]["state"]["events"]["events"]
        )
        with Dataset.open(path) as dataset:
            assert list(dataset.steps()) == rows
            report = dataset.validate_replay(engine, recorder.game_id, provenance=provenance)
            assert report.compatible, report


def test_terminal_transition_and_save_after_close(engine, deck, provenance, tmp_path):
    with Recorder.create(engine, deck, deck, 123, provenance=provenance) as recorder:
        for _ in range(800):
            if recorder.ended:
                break
            recorder.step(
                choose(recorder, K.END_PHASE, K.PASS, K.NO, K.SELECT_ZONE, K.CONFIRM, K.SELECT_CARD)
            )
        assert recorder.terminated and not recorder.truncated
        with pytest.raises(RuntimeError, match="ended"):
            recorder.step(0)
    path = tmp_path / "terminal.duckdb"
    recorder.save(path)
    with Dataset.open(path) as dataset:
        rows = list(dataset.steps(recorder.game_id))
        assert rows[-1]["after"]["engine_terminated"]
        assert rows[-1]["after"]["current_player"] is None
        assert rows[-1]["after"]["actions"] == []
        assert rows[-1]["result"]["rewards"] == list(recorder.rewards)
        assert dataset.game(recorder.game_id)["outcome"] is not None
        assert dataset.validate_replay(engine, recorder.game_id, provenance=provenance).compatible


def test_invalid_actions_and_outside_mutation(recorder):
    with pytest.raises(TypeError):
        recorder.step(True)
    with pytest.raises(IndexError):
        recorder.step(100000)
    assert list(recorder.steps()) == []
    recorder.duel.step(choose(recorder.duel, K.SUMMON))
    with pytest.raises(RuntimeError, match="outside recorder"):
        recorder.step(0)


def test_returned_records_are_owned_copies(recorder):
    row = recorder.step(choose(recorder, K.SUMMON))
    row["after"]["state"]["cards"].clear()
    assert len(next(recorder.steps())["after"]["state"]["cards"]) == 80
    game = recorder.game()
    game["initial"]["state"]["cards"].clear()
    assert len(recorder.game()["initial"]["state"]["cards"]) == 80


@pytest.mark.parametrize("frequency", [1, 50])
def test_snapshot_generation(recorder, tmp_path, frequency):
    path = tmp_path / "snapshots.duckdb"
    recorder.save(path, snapshot_every=frequency)
    with Dataset.open(path) as dataset:
        rows = list(dataset.snapshots(recorder.game_id))
        assert [row["boundary"] for row in rows] == [0]
        with dataset.restore(recorder._engine, recorder.game_id, 0) as restored:
            from ygo_gym.dataset.codec import capture

            assert capture(restored) == recorder.game()["initial"]
