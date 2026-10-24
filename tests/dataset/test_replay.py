from dataclasses import replace

from ygo_gym.dataset import Dataset
from ygo_gym.dataset.storage.writing import save

from .conftest import recorded


def test_reports_first_semantic_divergence(engine, replay, provenance, tmp_path):
    game, rows = recorded(engine, tmp_path / "source.duckdb", replay, provenance)
    rows[0]["after"]["state"]["cards"][0]["code"] = 999999999
    path = tmp_path / "divergent.duckdb"
    save(path, game, rows)
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, game["game_id"], provenance=provenance)
        assert not report.compatible
        assert report.checked_steps == 0
        assert report.path == "steps[0].after.state.cards[0].code"
        assert report.expected == 999999999
        assert report.actual != report.expected


def test_provenance_difference_does_not_automatically_reject(engine, replay, provenance, tmp_path):
    path = tmp_path / "compatible.duckdb"
    game, _ = recorded(engine, path, replay, provenance)
    changed = replace(provenance, native_sha256="different-build")
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, game["game_id"], provenance=changed)
        assert report.compatible and report.checked_steps == len(replay.actions)
        assert not report.provenance_matches


def test_initialization_and_action_corruption_are_reported(engine, replay, provenance, tmp_path):
    game, rows = recorded(engine, tmp_path / "source.duckdb", replay, provenance)
    rows[0]["action_index"] = 100000
    path = tmp_path / "invalid-action.duckdb"
    save(path, game, rows)
    with Dataset.open(path) as dataset:
        report = dataset.validate_replay(engine, game["game_id"], provenance=provenance)
        assert not report.compatible and report.path == "steps[0].action_index"
    game["game_id"] = "different"
    game["initial"]["state"]["global_state"]["turn_count"] += 1
    other = tmp_path / "bad-initial.duckdb"
    save(other, game, [])
    with Dataset.open(other) as dataset:
        report = dataset.validate_replay(engine, "different", provenance=provenance)
        assert not report.compatible and report.path.startswith("initial.state.global_state")
