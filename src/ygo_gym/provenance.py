import hashlib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import _native
from .engine import Engine


def package_version() -> str:
    try:
        return version("ygo-gym")
    except PackageNotFoundError:
        return "0.1.0+source"


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
    """Content fingerprints of the package, core, card databases, and scripts that produced a run."""

    package_version: str
    core_major: int
    core_minor: int
    native_sha256: str
    database_sha256: str
    scripts_sha256: tuple[str, ...]

    @classmethod
    def capture(cls, engine: Engine):
        core = engine.core_version
        return cls(
            package_version(),
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
