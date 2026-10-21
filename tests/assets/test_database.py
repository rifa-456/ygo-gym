import sqlite3


def test_database_integrity_and_schema(pytestconfig):
    path = pytestconfig.rootpath / "third_party/BabelCDB/cards.cdb"
    assert path.is_file(), "Initialize the BabelCDB submodule"
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as database:
        assert database.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
        required = {
            "datas": {"id", "ot", "alias", "setcode", "type", "atk", "def",
                      "level", "race", "attribute", "category"},
            "texts": {"id", "name", "desc", *(f"str{i}" for i in range(1, 17))},
        }
        for table, columns in required.items():
            available = {row[1] for row in database.execute(f"PRAGMA table_info({table})")}
            assert columns <= available, f"Missing {table} columns: {columns - available}"
        assert database.execute("SELECT count(*) FROM datas").fetchone()[0] > 0
        assert database.execute(
            "SELECT count(*) FROM datas d LEFT JOIN texts t ON t.id=d.id WHERE t.id IS NULL"
        ).fetchone()[0] == 0
        assert database.execute(
            "SELECT count(*) FROM datas WHERE id IS NULL OR id <= 0 OR id > 4294967295"
        ).fetchone()[0] == 0
