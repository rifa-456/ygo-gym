import duckdb
import pytest
from ygo_gym.dataset import Dataset, DatasetFormatError, DatasetWriter
from ygo_gym.dataset.storage.writing import save

from .conftest import recorded


def test_multiple_games_and_duplicate_transaction_rollback(engine, deck, provenance, tmp_path):
    path = tmp_path / "shard.duckdb"
    writer = DatasetWriter(path, engine, provenance=provenance)
    expected = []
    for seed in (1, 2):
        with engine.create_duel(deck, deck, seed=seed) as duel:
            duel.step(0)
            game_id = writer.write(duel.replay(), game_id=f"game-{seed}")
            expected.append(game_id)
            with pytest.raises(duckdb.ConstraintException):
                writer.write(duel.replay(), game_id=game_id)
    with Dataset.open(path) as dataset:
        assert sorted(g["game_id"] for g in dataset.games()) == expected
        assert len(list(dataset.steps())) == 2


def test_new_file_failure_is_atomic(engine, replay, provenance, tmp_path):
    game, rows = recorded(engine, tmp_path / "source.duckdb", replay, provenance)
    path = tmp_path / "failed" / "failed.duckdb"
    with pytest.raises(duckdb.ConstraintException):
        save(path, game, rows + rows)
    assert list(path.parent.iterdir()) == []


def test_direct_typed_sql_and_arrow_access(engine, replay, provenance, tmp_path):
    path = tmp_path / "typed.duckdb"
    recorded(engine, path, type(replay)(replay.start, replay.seed, replay.actions[:1]), provenance)
    with duckdb.connect(str(path), read_only=True) as connection:
        names = connection.execute("SHOW TABLES").fetchall()
        assert names == [("games",), ("snapshots",), ("steps",)]
        assert connection.execute('SELECT len("before".state.cards) FROM steps').fetchone() == (80,)
        assert connection.execute('SELECT len("before".actions) FROM steps').fetchone()[0] > 0
        assert "STRUCT" in connection.execute("DESCRIBE steps").fetchall()[3][1]
    with Dataset.open(path) as dataset:
        batches = list(dataset.arrow_batches("steps", batch_size=1))
        assert len(batches) == 1 and batches[0].num_rows == 1
        assert batches[0].to_pylist() == list(dataset.steps())
        with pytest.raises(ValueError):
            list(dataset.arrow_batches("DROP TABLE games"))


def test_uint64_and_nullable_components_remain_typed(engine, replay, provenance, tmp_path):
    game, rows = recorded(engine, tmp_path / "source.duckdb", replay, provenance)
    rows[0]["action"]["number"] = 2**64 - 1
    rows[0]["before"]["state"]["cards"][0]["properties"]["race"] = 2**63
    path = tmp_path / "wide.duckdb"
    save(path, game, rows)
    with Dataset.open(path) as dataset:
        actual = next(dataset.steps())
        assert actual["action"]["number"] == 2**64 - 1
        assert actual["before"]["state"]["cards"][0]["properties"]["race"] == 2**63
        assert actual == rows[0]


def test_unsupported_schema_and_reader_lifecycle(engine, replay, provenance, tmp_path):
    path = tmp_path / "schema.duckdb"
    recorded(engine, path, replay, provenance)
    with Dataset.open(path) as dataset:
        with pytest.raises(KeyError):
            dataset.game("not-a-game")
    with pytest.raises(RuntimeError, match="closed"):
        list(dataset.games())
    with duckdb.connect(str(path)) as connection:
        connection.execute(
            """COMMENT ON TABLE games IS '{"format":"ygo-gym.dataset","schema_version":999}'"""
        )
    with pytest.raises(DatasetFormatError, match="unsupported"):
        Dataset.open(path)


def test_refuse_overwrite(engine, replay, provenance, tmp_path):
    path = tmp_path / "existing.duckdb"
    recorded(engine, path, replay, provenance)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        DatasetWriter(path, engine, provenance=provenance, append=False).write(replay)
    assert path.read_bytes() == before
