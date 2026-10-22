from importlib import import_module
from pathlib import Path

from ..task import Task
from .schema.tables import TABLES
from .storage.connection import connect, validate


class Dataset:
    """Read-only access to complete semantic records; no simulator replay is needed."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise FileNotFoundError(self.path)
        self._connection = connect(self.path, read_only=True)
        try:
            validate(self._connection)
        except BaseException:
            self._connection.close()
            self._connection = None
            raise

    @classmethod
    def open(cls, path: str | Path):
        return cls(path)

    def _query(self, table: str, game_id: str | None):
        if self._connection is None:
            raise RuntimeError("dataset is closed")
        if table not in TABLES:
            raise ValueError("table must be games, steps, or snapshots")
        order = {"games": "game_id", "steps": "game_id, step_index", "snapshots": "game_id, boundary"}[table]
        sql = f'SELECT * FROM "{table}"'
        params = []
        if game_id is not None:
            sql += " WHERE game_id = ?"
            params.append(game_id)
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql + " ORDER BY " + order, params)
        except BaseException:
            cursor.close()
            raise
        return cursor

    def _rows(self, table: str, game_id: str | None = None):
        cursor = self._query(table, game_id)
        names = [column[0] for column in cursor.description]
        try:
            while batch := cursor.fetchmany(64):
                for values in batch:
                    yield dict(zip(names, values, strict=True))
        finally:
            cursor.close()

    def games(self):
        return self._rows("games")

    def game(self, game_id: str) -> dict:
        rows = self._rows("games", game_id)
        try:
            result = next(rows, None)
        finally:
            rows.close()
        if result is None:
            raise KeyError(game_id)
        return result

    def steps(self, game_id: str | None = None):
        return self._rows("steps", game_id)

    def snapshots(self, game_id: str | None = None):
        return self._rows("snapshots", game_id)

    def arrow_batches(self, table: str, *, game_id: str | None = None, batch_size: int = 1024):
        if type(batch_size) is not int or batch_size < 1:
            raise ValueError("batch_size must be positive")
        try:
            import_module("pyarrow")
        except ImportError as error:
            raise ImportError("Arrow batches require the 'dataset' extra") from error
        cursor = self._query(table, game_id)
        try:
            reader = cursor.to_arrow_reader(batch_size)
            try:
                yield from reader
            finally:
                reader.close()
        finally:
            cursor.close()

    def evaluate(self, task: Task):
        from .evaluation import Evaluation

        return Evaluation(self, task)

    def restore(self, engine, game_id: str, boundary: int, *, task=None, provenance=None):
        from .snapshots import restore

        return restore(self, engine, game_id, boundary, task=task, provenance=provenance)

    def validate_replay(self, engine, game_id: str, *, provenance=None):
        from .replay import validate_replay

        return validate_replay(self, engine, game_id, provenance=provenance)

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
