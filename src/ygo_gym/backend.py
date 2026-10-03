from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import TypeAlias

from . import _native

Seed: TypeAlias = tuple[int, int, int, int]


@dataclass(frozen=True, slots=True)
class CoreVersion:
    major: int
    minor: int


class Duel:
    __slots__ = ("_native_duel",)

    def __init__(self, native_duel: _native.Duel) -> None:
        self._native_duel = native_duel

    @property
    def closed(self) -> bool:
        return self._native_duel.closed

    def close(self) -> None:
        self._native_duel.close()

    def __enter__(self) -> Duel:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class Backend:
    __slots__ = ("_native_backend", "_card_database", "_script_roots")

    def __init__(self, card_database: str | Path, script_roots: tuple[str | Path, ...]) -> None:
        database = Path(card_database).resolve()
        roots = tuple(Path(root).resolve() for root in script_roots)
        self._native_backend = _native.Backend(
            str(database),
            [str(root) for root in roots],
        )
        self._card_database = database
        self._script_roots = roots

    @classmethod
    def from_checkout(cls, root: str | Path | None = None) -> Backend:
        project_root = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[2]
        scripts = project_root / "third_party" / "CardScripts"
        return cls(
            card_database=project_root / "third_party" / "BabelCDB" / "cards.cdb",
            script_roots=(scripts, scripts / "official"),
        )

    @property
    def card_database(self) -> Path:
        return self._card_database

    @property
    def script_roots(self) -> tuple[Path, ...]:
        return self._script_roots

    @property
    def core_version(self) -> CoreVersion:
        major, minor = self._native_backend.core_version
        return CoreVersion(major=major, minor=minor)

    def create_duel(self, seed: Seed) -> Duel:
        if len(seed) != 4:
            raise ValueError("seed must contain exactly four 64-bit words")
        if any(word < 0 or word > 0xFFFFFFFFFFFFFFFF for word in seed):
            raise ValueError("seed words must fit in uint64")
        if not any(seed):
            raise ValueError("seed cannot be all zeros")
        return Duel(self._native_backend.create_duel(seed))
