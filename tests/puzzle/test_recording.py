import pytest
from ygo_gym import CardSetup, DuelSetup, Location, PlayerSetup, Provenance, Puzzle, WinThisTurn
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.dataset.codec import capture as snapshot


@pytest.mark.parametrize("kind", ["setup", "python", "lua"])
def test_replay_and_snapshot_keep_initialization(engine, tmp_path, kind):
    setup = DuelSetup(
        players=(PlayerSetup(), PlayerSetup()),
        cards=(CardSetup(69247929, 0, 0, Location.HAND, 0),),
    )
    puzzle = Puzzle("test-position", setup=setup, objective=WinThisTurn())
    if kind == "lua":
        puzzle = Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua")
    provenance = Provenance.capture(engine)
    path = tmp_path / "puzzles.duckdb"
    game = engine.create_duel(setup=setup, seed=17) if kind == "setup" else puzzle.start(engine, seed=17)
    with game:
        game.step(0)
        duel = game if kind == "setup" else game.duel
        game_id = DatasetWriter(path, engine, snapshot_every=1, provenance=provenance).write(duel.replay())
        with Dataset.open(path) as dataset:
            assert dataset.game(game_id)["setup"]["source"]
            assert dataset.validate_replay(engine, game_id, provenance=provenance).compatible
            with dataset.restore(engine, game_id, 1, provenance=provenance) as branch:
                assert snapshot(branch) == snapshot(duel)
