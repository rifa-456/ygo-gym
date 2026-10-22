import os
from pathlib import Path
from uuid import uuid4

from .connection import connect, initialize, validate


def insert(connection, table: str, records) -> None:
    import pyarrow as pa

    schema = connection.execute(f'SELECT * FROM "{table}" LIMIT 0').to_arrow_table().schema
    batch = []

    def flush():
        values = pa.Table.from_pylist(batch, schema=schema)
        connection.register("_ygo_dataset_batch", values)
        try:
            connection.execute(f'INSERT INTO "{table}" SELECT * FROM _ygo_dataset_batch')
        finally:
            connection.unregister("_ygo_dataset_batch")
        batch.clear()

    for record in records:
        batch.append(record)
        if len(batch) == 32:
            flush()
    if batch:
        flush()


def save(path: str | Path, game: dict, steps, *, append: bool = True, snapshots=()) -> None:
    save_many(path, [(game, steps, snapshots)], append=append)


def save_many(path: str | Path, episodes, *, append: bool = True) -> None:
    target = Path(path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    exists = target.exists()
    if exists and not append:
        raise FileExistsError(target)
    temporary = target.with_name(target.name + "." + uuid4().hex + ".tmp")
    working = target if exists else temporary
    connection = None
    try:
        connection = connect(working, read_only=False)
        if exists:
            validate(connection)
        else:
            initialize(connection)
        connection.execute("BEGIN TRANSACTION")
        try:
            for episode in episodes:
                game, steps = episode[:2]
                snapshots = episode[2] if len(episode) == 3 else ()
                insert(connection, "games", [game])
                insert(connection, "steps", steps)
                insert(connection, "snapshots", snapshots)
            connection.execute("COMMIT")
        except BaseException:
            connection.execute("ROLLBACK")
            raise
        connection.execute("CHECKPOINT")
        connection.close()
        connection = None
        if not exists:
            if target.exists():
                raise FileExistsError(target)
            os.replace(temporary, target)
    finally:
        if connection is not None:
            connection.close()
        if not exists:
            temporary.unlink(missing_ok=True)
            Path(str(temporary) + ".wal").unlink(missing_ok=True)
