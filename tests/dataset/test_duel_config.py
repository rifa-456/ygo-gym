from ygo_gym import Deck, DuelConfig, DuelRule, DuelSetup, PlayerSetup
from ygo_gym.dataset import Dataset, DatasetWriter
from ygo_gym.dataset.codec import capture


def test_configured_decks_record_replay_and_restore(engine, tmp_path):
    config = DuelConfig(
        flags=DuelRule.MODE_MR3,
        life_points=(1234, 5678),
        opening_hand=(1, 2),
        draw_count=(0, 0),
        shuffle=False,
    )
    deck = Deck((69247929, 89631139, 46986414, 69247929, 89631139))
    path = tmp_path / "configured.duckdb"
    with engine.create_duel(deck, deck, config=config) as duel:
        duel.step(0)
        game_id = DatasetWriter(path, engine, snapshot_every=1).write(duel.replay())
        with Dataset.open(path) as dataset:
            assert dataset.game(game_id)["setup"]["config_json"]
            assert dataset.validate_replay(engine, game_id).compatible
            with dataset.restore(engine, game_id, 1) as restored:
                assert capture(restored) == capture(duel)


def test_version_two_records_remain_readable_and_replayable(engine, tmp_path):
    import duckdb

    from ygo_gym.dataset.schema.tables import create_sql
    from ygo_gym.dataset.storage.writing import insert

    source = tmp_path / "source.duckdb"
    with engine.create_duel(setup=DuelSetup((PlayerSetup(),) * 2)) as duel:
        game_id = DatasetWriter(source, engine).write(duel.replay())
    with Dataset.open(source) as dataset:
        game = dataset.game(game_id)
    game["schema_version"] = 2
    game["setup"].pop("config_json")

    def strip(value):
        if isinstance(value, dict):
            if "variant" in value:
                value.pop("code", None)
            for child in value.values():
                strip(child)
        elif isinstance(value, list):
            for child in value:
                strip(child)

    strip(game)
    path = tmp_path / "legacy.duckdb"
    with duckdb.connect(str(path)) as connection:
        for table in ("games", "steps", "snapshots"):
            sql = create_sql(table).replace(', "config_json" VARCHAR', "")
            sql = sql.replace('"stage" VARCHAR, "code" BIGINT,', '"stage" VARCHAR,')
            connection.execute(sql)
        connection.execute(
            'COMMENT ON TABLE games IS \'{"format":"ygo-gym.dataset","schema_version":2}\''
        )
        insert(connection, "games", [game])
    with Dataset.open(path) as dataset:
        assert dataset.game(game_id)["setup"]["config_json"] is None
        assert dataset.validate_replay(engine, game_id).compatible
