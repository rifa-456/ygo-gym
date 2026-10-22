import hashlib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .. import _native
from ..deck import Deck
from ..engine import Engine


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def database_digest(engine: Engine) -> str:
    values = [digest(path) for path in engine.card_databases]
    if len(values) == 1:
        return values[0]
    return hashlib.sha256(b"".join(bytes.fromhex(value) for value in values)).hexdigest()


def script_digest(root: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(root.rglob("*.lua")):
        name = path.relative_to(root).as_posix().encode()
        result.update(len(name).to_bytes(8, "little"))
        result.update(name)
        result.update(bytes.fromhex(digest(path)))
    return result.hexdigest()


@dataclass(frozen=True, slots=True)
class Provenance:
    """Content fingerprints captured explicitly for a recording batch."""

    package_version: str
    core_major: int
    core_minor: int
    native_sha256: str
    database_sha256: str
    scripts_sha256: tuple[str, ...]

    @classmethod
    def capture(cls, engine: Engine):
        try:
            package = version("ygo-gym")
        except PackageNotFoundError:
            package = "0.1.0+source"
        core = engine.core_version
        return cls(
            package,
            core.major,
            core.minor,
            digest(Path(_native.__file__)),
            database_digest(engine),
            tuple(script_digest(p) for p in engine.script_roots),
        )

    def as_record(self) -> dict:
        return {
            "package_version": self.package_version,
            "core_major": self.core_major,
            "core_minor": self.core_minor,
            "native_sha256": self.native_sha256,
            "database_sha256": self.database_sha256,
            "scripts_sha256": list(self.scripts_sha256),
        }


def setup(player1: Deck | None, player2: Deck | None, seed: int, duel_options: int,
          *, source: str | None = None, source_name: str | None = None) -> dict:
    return {
        "seed": seed,
        "players": [
            {"main": list(p.main), "extra": list(p.extra), "side": list(p.side)} for p in (player1, player2) if p is not None
        ],
        "duel_options": duel_options,
        "source": source,
        "source_name": source_name,
    }


def create_duel(engine: Engine, value: dict):
    if value.get("source") is not None:
        return engine._create_scripted(value["source"], value["source_name"], value["seed"])
    players = [Deck(p["main"], p["extra"], p["side"]) for p in value["players"]]
    return engine.create_duel(*players, seed=value["seed"])
