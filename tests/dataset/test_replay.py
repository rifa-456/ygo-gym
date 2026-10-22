from dataclasses import replace

from ygo_gym.dataset import Dataset
from ygo_gym.dataset.storage.writing import save


def test_reports_first_semantic_divergence(recorder, engine, provenance, tmp_path):
    recorder.step(0)
    rows = list(recorder.steps())
    rows[0]["after"]["state"]["cards"][0]["code"] = 999999999
    path = tmp_path / "divergent.duckdb"
    save(path, recorder.game(), rows)
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, recorder.game_id, provenance=provenance)
        assert not report.compatible
        assert report.checked_steps == 0
        assert report.path == "steps[0].after.state.cards[0].code"
        assert report.expected == 999999999
        assert report.actual != report.expected


def test_provenance_difference_does_not_automatically_reject(recorder, engine, provenance, tmp_path):
    recorder.step(0)
    path = tmp_path / "compatible.duckdb"
    recorder.save(path)
    changed = replace(provenance, native_sha256="different-build")
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, recorder.game_id, provenance=changed)
        assert report.compatible and report.checked_steps == 1
        assert not report.provenance_matches


def test_initialization_and_action_corruption_are_reported(recorder, engine, provenance, tmp_path):
    recorder.step(0)
    rows = list(recorder.steps())
    rows[0]["action_index"] = 100000
    path = tmp_path / "invalid-action.duckdb"
    save(path, recorder.game(), rows)
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, recorder.game_id, provenance=provenance)
        assert not report.compatible and report.path == "steps[0].action_index"
    game = recorder.game()
    game["game_id"] = "different"
    game["initial"]["state"]["global_state"]["turn_count"] += 1
    other = tmp_path / "bad-initial.duckdb"
    save(other, game, [])
    with Dataset.open(other) as dataset:
        report = dataset.validate_replay(engine, "different", provenance=provenance)
        assert not report.compatible and report.path.startswith("initial.state.global_state")
