from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from types import TracebackType

from . import _native
from ._database import load_card_rows
from .deck import Deck


@dataclass(frozen=True, slots=True)
class CoreVersion:
    major: int
    minor: int


class DuelStatus(IntEnum):
    END = 0
    AWAITING = 1
    CONTINUE = 2


class Duel:
    __slots__ = ("_native_duel",)

    def __init__(self, native_duel: _native.Duel) -> None:
        self._native_duel = native_duel

    @property
    def closed(self) -> bool:
        return self._native_duel.closed

    @property
    def status(self) -> DuelStatus:
        return DuelStatus(self._native_duel.status)

    @property
    def message_buffer(self) -> bytes:
        return self._native_duel.message_buffer

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
        if not database.is_file():
            raise FileNotFoundError(f"card database does not exist: {database}")
        if not roots:
            raise ValueError("at least one script root is required")
        for root in roots:
            if not root.is_dir():
                raise FileNotFoundError(f"script root does not exist: {root}")
        card_rows = load_card_rows(database)
        self._native_backend = _native.Backend(
            str(database),
            [str(root) for root in roots],
            card_rows,
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

    def create_duel(self, player1: Deck, player2: Deck, seed: int) -> Duel:
        if seed < 0 or seed > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("seed must fit in uint64")
        return Duel(
            self._native_backend.create_duel(
                seed,
                player1.main,
                player1.extra,
                player2.main,
                player2.extra,
            )
        )
