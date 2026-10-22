import pytest
from ygo_gym.dataset import Dataset, DatasetFormatError, Recorder
from ygo_gym.dataset.storage.writing import save
from ygo_gym.task import Task


def test_multiple_games_and_duplicate_transaction_rollback(engine, deck, provenance, tmp_path):
    import duckdb

    path = tmp_path / "shard.duckdb"
    expected = []
    for seed in (1, 2):
        with Recorder.create(
            engine, deck, deck, seed, task=Task(max_steps=2), provenance=provenance
        ) as recorder:
            recorder.step(0)
            recorder.save(path)
            expected.append(recorder.game())
            with pytest.raises(duckdb.ConstraintException):
                recorder.save(path)
    with Dataset.open(path) as dataset:
        assert {g["game_id"] for g in dataset.games()} == {g["game_id"] for g in expected}
        assert len(list(dataset.steps())) == 2
        for game in expected:
            assert dataset.game(game["game_id"]) == game


def test_new_file_failure_is_atomic(recorder, tmp_path):
    import duckdb

    recorder.step(0)
    path = tmp_path / "failed.duckdb"
    rows = list(recorder.steps())
    with pytest.raises(duckdb.ConstraintException):
        save(path, recorder.game(), rows + rows)
    assert list(tmp_path.iterdir()) == []


def test_direct_typed_sql_and_arrow_access(recorder, tmp_path):
    import duckdb

    pytest.importorskip("pyarrow")
    recorder.step(0)
    path = tmp_path / "typed.duckdb"
    recorder.save(path)
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


def test_uint64_and_nullable_components_remain_typed(recorder, tmp_path):
    recorder.step(0)
    rows = list(recorder.steps())
    rows[0]["action"]["number"] = 2**64 - 1
    rows[0]["before"]["state"]["cards"][0]["properties"]["race"] = 2**63
    path = tmp_path / "wide.duckdb"
    save(path, recorder.game(), rows)
    with Dataset.open(path) as dataset:
        actual = next(dataset.steps())
        assert actual["action"]["number"] == 2**64 - 1
        assert actual["before"]["state"]["cards"][0]["properties"]["race"] == 2**63
        assert actual == rows[0]


def test_unsupported_schema_and_reader_lifecycle(recorder, tmp_path):
    import duckdb

    path = tmp_path / "schema.duckdb"
    recorder.save(path)
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


def test_refuse_overwrite(recorder, tmp_path):
    path = tmp_path / "existing.duckdb"
    recorder.save(path)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        recorder.save(path, append=False)
    assert path.read_bytes() == before
