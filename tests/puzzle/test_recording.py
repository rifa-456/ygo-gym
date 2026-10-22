import pytest

pytest.importorskip("duckdb")

from ygo_gym import CardSetup, DuelSetup, Location, PlayerSetup, Puzzle, WinThisTurn
from ygo_gym.dataset import Dataset, Recorder
from ygo_gym.dataset.codec import capture as snapshot
from ygo_gym.dataset.initialization import Provenance


@pytest.mark.parametrize("kind", ["setup", "python", "lua"])
def test_replay_and_snapshot_keep_initialization(engine, tmp_path, kind):
    setup = DuelSetup(
        players=(PlayerSetup(), PlayerSetup()),
        cards=(CardSetup(69247929, 0, 0, Location.HAND, 0),),
    )
    puzzle = Puzzle("test-position", setup=setup, objective=WinThisTurn())
    if kind == "lua":
        puzzle = Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua")
    options = {"setup": setup} if kind == "setup" else {"puzzle": puzzle}
    provenance = Provenance.capture(engine)
    path = tmp_path / "puzzles.duckdb"
    with Recorder.create(engine, seed=17, provenance=provenance, **options) as recorder:
        recorder.step(0)
        recorder.save(path, snapshot_every=1)
        with Dataset.open(path) as dataset:
            assert dataset.game(recorder.game_id)["setup"]["source"]
            assert dataset.validate_replay(
                engine, recorder.game_id, provenance=provenance
            ).compatible
            with dataset.restore(
                engine, recorder.game_id, 1, provenance=provenance
            ) as branch:
                assert snapshot(branch) == snapshot(recorder.duel)
