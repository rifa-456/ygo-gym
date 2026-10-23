import json

import pytest

pytest.importorskip("duckdb")

from ygo_gym.dataset.schema.tables import FORMAT, SCHEMA_VERSION, TABLES, create_sql
from ygo_gym.dataset.storage.connection import DatasetFormatError, connect, validate


def test_older_nested_fields_cannot_be_silently_dropped_on_append(tmp_path):
    connection = connect(tmp_path / "older.duckdb", read_only=False)
    try:
        for name in TABLES:
            sql = create_sql(name).replace(
                ', "effects_disabled" BOOLEAN, "summon_completed" BOOLEAN', ""
            )
            connection.execute(sql)
        marker = json.dumps({"format": FORMAT, "schema_version": SCHEMA_VERSION})
        connection.execute("COMMENT ON TABLE games IS '" + marker + "'")
        validate(connection)
        with pytest.raises(DatasetFormatError, match="older semantic fields"):
            validate(connection, writing=True)
    finally:
        connection.close()
