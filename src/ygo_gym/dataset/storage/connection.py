import json
from pathlib import Path

from ..schema.tables import FORMAT, SCHEMA_VERSION, TABLES, create_sql


class DatasetFormatError(ValueError):
    """The file is not a supported YGO Gym semantic dataset."""


def connect(path: Path, *, read_only: bool):
    try:
        import duckdb
    except ImportError as error:
        raise ImportError("dataset storage requires the 'dataset' extra: uv sync --extra dataset") from error
    return duckdb.connect(str(path), read_only=read_only)


def initialize(connection) -> None:
    for name in TABLES:
        connection.execute(create_sql(name))
    marker = json.dumps({"format": FORMAT, "schema_version": SCHEMA_VERSION})
    connection.execute("COMMENT ON TABLE games IS '" + marker + "'")


def validate(connection) -> None:
    row = connection.execute(
        "SELECT comment FROM duckdb_tables() WHERE table_name = 'games' "
        "AND schema_name = 'main' AND NOT internal"
    ).fetchone()
    try:
        marker = json.loads(row[0]) if row else {}
        supported = marker["format"] == FORMAT and marker["schema_version"] == SCHEMA_VERSION
    except (KeyError, TypeError, ValueError):
        supported = False
    if not supported:
        raise DatasetFormatError("unsupported dataset schema; no migration is available for this file")
    for name, fields in TABLES.items():
        actual = connection.execute(f'DESCRIBE "{name}"').fetchall()
        if [r[0] for r in actual] != list(fields):
            raise DatasetFormatError(f"unexpected columns in {name}")
