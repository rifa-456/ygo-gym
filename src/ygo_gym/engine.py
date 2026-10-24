from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from types import TracebackType

from . import _native
from .action import Action
from .database import CardText, load_card_definitions, load_card_texts
from .deck import Deck
from .protocol import CoreResponse, Decision
from .replay import DeckStart, Replay, ReplayUnavailableError, ScriptStart, Start
from .state import Observation, Player, State


@dataclass(frozen=True, slots=True)
class CoreVersion:
    major: int
    minor: int


class DuelStatus(IntEnum):
    END = 0
    AWAITING = 1
    CONTINUE = 2


@dataclass(frozen=True, slots=True)
class Outcome:
    winner: Player | None
    reason: int
    rewards: tuple[float, float]


@dataclass(frozen=True, slots=True)
class Checkpoint:
    native: _native.Checkpoint
    actions: tuple[int, ...]
    lost: str | None


class Duel:
    __slots__ = ("_native_duel", "_engine", "_start", "_seed", "_actions", "_lost")

    def __init__(
        self, native_duel: _native.Duel, engine: Engine | None = None,
        start: Start | None = None, seed: int = 0,
    ) -> None:
        self._native_duel = native_duel
        self._engine = engine
        self._start = start
        self._seed = seed
        self._actions: list[int] = []
        self._lost: str | None = None if start is not None else "duel was not created from a known start"

    def replay(self) -> Replay:
        """Reproduce this duel from its start; reseeded branches and snapshots raise."""
        if self._lost is not None:
            raise ReplayUnavailableError(self._lost)
        return Replay(self._start, self._seed, tuple(self._actions))

    def _branch(self, native_duel: _native.Duel, preserve_rng: bool) -> Duel:
        branch = Duel(native_duel, self._engine, self._start, self._seed)
        branch._actions = list(self._actions)
        branch._lost = self._lost if preserve_rng else self._lost or "branch was reseeded"
        return branch

    def serialize(self, *, provenance=None) -> bytes:
        """Save an awaiting duel, including current core and Lua RNG states."""
        from .persistence.compatibility import fingerprint
        from .persistence.format import pack

        if self._engine is None:
            raise RuntimeError("serialization requires the originating Engine")
        return pack(self._native_duel.serialize(), fingerprint(self._engine, provenance))

    def clone(self, *, preserve_rng: bool = False, seed: int | None = None) -> Duel:
        """Clone an awaiting duel, independently seeding future randomness by default.

        Existing cards, zone order, and already sampled values are preserved.
        A seed reproduces future core and Lua random streams within the same
        compatible backend. preserve_rng=True copies their exact current state.
        """
        if not isinstance(preserve_rng, bool):
            raise TypeError("preserve_rng must be bool")
        if seed is not None:
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise TypeError("seed must be an integer")
            if seed < 0 or seed > 0xFFFFFFFFFFFFFFFF:
                raise ValueError("seed must fit in uint64")
            if preserve_rng:
                raise ValueError("seed and preserve_rng=True cannot be combined")
        return self._branch(self._native_duel.clone(preserve_rng=preserve_rng, seed=seed), preserve_rng)

    def checkpoint(self) -> Checkpoint:
        """Capture this awaiting duel, including any partial compound selection."""
        return Checkpoint(self._native_duel.checkpoint(), tuple(self._actions), self._lost)

    def restore(self, checkpoint: Checkpoint, *, preserve_rng: bool = False, seed: int | None = None) -> None:
        """Restore a checkpoint into its original duel and reseed future randomness.

        preserve_rng=True restores the captured random streams exactly. Restoring
        after termination is supported; a closed duel cannot be restored.
        """
        if not isinstance(checkpoint, Checkpoint):
            raise TypeError("checkpoint must be a Checkpoint")
        if not isinstance(preserve_rng, bool):
            raise TypeError("preserve_rng must be bool")
        if seed is not None:
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise TypeError("seed must be an integer")
            if seed < 0 or seed > 0xFFFFFFFFFFFFFFFF:
                raise ValueError("seed must fit in uint64")
            if preserve_rng:
                raise ValueError("seed and preserve_rng=True cannot be combined")
        self._native_duel.restore(checkpoint.native, preserve_rng=preserve_rng, seed=seed)
        self._actions = list(checkpoint.actions)
        self._lost = checkpoint.lost if preserve_rng else checkpoint.lost or "duel was restored with new randomness"

    @property
    def closed(self) -> bool:
        return self._native_duel.closed

    @property
    def status(self) -> DuelStatus:
        return DuelStatus(self._native_duel.status)

    @property
    def terminated(self) -> bool:
        return self._native_duel.terminated

    @property
    def current_player(self) -> Player | None:
        return self._native_duel.current_player

    @property
    def outcome(self) -> Outcome | None:
        native = self._native_duel.outcome
        if native is None:
            return None
        return Outcome(winner=native.winner, reason=native.reason, rewards=tuple(native.rewards))

    @property
    def rewards(self) -> tuple[float, float]:
        return tuple(self._native_duel.rewards)

    @property
    def decision(self) -> Decision | None:
        return self._native_duel.decision

    @property
    def actions(self) -> tuple[Action, ...]:
        return tuple(self._native_duel.actions)

    @property
    def pending_actions(self) -> tuple[Action, ...]:
        return tuple(self._native_duel.pending_actions)

    @property
    def observation(self) -> Observation:
        return self._native_duel.observation

    def observe(self, player: int) -> Observation:
        if player not in (0, 1):
            raise ValueError("player must be 0 or 1")
        return self._native_duel.observe(player)

    def state(self) -> State:
        return self._native_duel.state()

    @property
    def message_buffer(self) -> bytes:
        return self._native_duel.message_buffer

    def step(self, action_index: int) -> None:
        if not isinstance(action_index, int):
            raise TypeError("action index must be an integer")
        if action_index < 0 or action_index >= len(self._native_duel.actions):
            raise IndexError("action index is out of range")
        self._native_duel.step(action_index)
        self._actions.append(action_index)

    def respond(self, response: CoreResponse) -> None:
        indices = None
        if self._engine is not None and self._lost is None:
            try:
                indices = self._engine._native_engine._plan_client_response(self.observation, response.bytes)
            except (ValueError, RuntimeError):
                pass
        self._native_duel.respond(response)
        if indices is None:
            self._lost = self._lost or "a raw response could not be expressed as actions"
        else:
            self._actions.extend(indices)

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


class Engine:
    __slots__ = ("_native_engine", "_card_database", "_script_roots", "_card_databases", "_card_texts")

    def __init__(
        self, card_database: str | Path | None = None,
        script_roots: tuple[str | Path, ...] | None = None,
        *, additional_card_databases: tuple[str | Path, ...] = (),
    ) -> None:
        if card_database is None and script_roots is None:
            from .assets.location import engine_defaults

            card_database, script_roots = engine_defaults()
        elif card_database is None or script_roots is None:
            raise ValueError("provide both card_database and script_roots, or neither")
        database = Path(card_database).resolve()
        roots = tuple(Path(root).resolve() for root in script_roots)
        if not database.is_file():
            raise FileNotFoundError(f"card database does not exist: {database}")
        databases = (database, *(Path(path).resolve() for path in additional_card_databases))
        for path in databases:
            if not path.is_file():
                raise FileNotFoundError(f"card database does not exist: {path}")
        if not roots:
            raise ValueError("at least one script root is required")
        for root in roots:
            if not root.is_dir():
                raise FileNotFoundError(f"script root does not exist: {root}")

        self._native_engine = _native.Engine(
            str(database),
            [str(root) for root in roots],
            [card for path in databases for card in load_card_definitions(path)],
        )
        self._card_database = database
        self._card_databases = databases
        self._script_roots = roots
        self._card_texts: dict[int, CardText] | None = None

    def deserialize(self, snapshot: bytes, *, provenance=None) -> Duel:
        """Restore a trusted snapshot produced by a matching engine build and assets."""
        from .persistence import SnapshotCompatibilityError, check_snapshot
        from .persistence.format import unpack

        report = check_snapshot(self, snapshot, provenance=provenance)
        if not report.compatible:
            raise SnapshotCompatibilityError(report)
        _, payload = unpack(snapshot)
        return Duel(self._native_engine.deserialize(payload), self)

    @classmethod
    def from_checkout(cls, root: str | Path | None = None) -> Engine:
        from .assets.location import checkout_root

        project_root = checkout_root(root)
        scripts = project_root / "third_party" / "CardScripts"
        return cls(
            card_database=project_root / "third_party" / "BabelCDB" / "cards.cdb",
            script_roots=(scripts, scripts / "official"),
        )

    @property
    def card_database(self) -> Path:
        return self._card_database

    @property
    def card_databases(self) -> tuple[Path, ...]:
        return self._card_databases

    def card_text(self, code: int) -> CardText:
        """Look up text with the engine's database precedence; unknown codes raise KeyError."""
        if self._card_texts is None:
            self._card_texts = load_card_texts(self._card_databases)
        return self._card_texts[code]

    @property
    def script_roots(self) -> tuple[Path, ...]:
        return self._script_roots

    @property
    def core_version(self) -> CoreVersion:
        major, minor = self._native_engine.core_version
        return CoreVersion(major=major, minor=minor)

    def _create_scripted(self, source: str, name: str, seed: int, start: Start | None = None) -> Duel:
        from .setup.model import integer

        integer(seed, "seed", 0xFFFFFFFFFFFFFFFF)
        return Duel(self._native_engine.create_setup(seed, source, name), self, start or ScriptStart(source, name), seed)

    def create_duel(
        self, player1: Deck | None = None, player2: Deck | None = None,
        seed: int = 0, *, setup=None, config=None,
    ) -> Duel:
        from .setup import DuelSetup
        from .rules import DuelConfig

        if config is not None and not isinstance(config, DuelConfig):
            raise TypeError("config must be a DuelConfig")
        if setup is not None:
            if config is not None:
                raise ValueError("synthetic setups define their own initialization rules")
            if player1 is not None or player2 is not None:
                raise ValueError("setup and deck arguments cannot be combined")
            if not isinstance(setup, DuelSetup):
                raise TypeError("setup must be a DuelSetup")
            return self._create_scripted(setup.to_lua(), "ygo-gym.setup", seed)
        if not isinstance(player1, Deck) or not isinstance(player2, Deck):
            raise TypeError("provide two Deck values or a DuelSetup")
        if type(seed) is not int or seed < 0 or seed > 0xFFFFFFFFFFFFFFFF:
            raise ValueError("seed must fit in uint64")
        return Duel(
            self._native_engine.create_duel(
                seed,
                player1.main,
                player1.extra,
                player2.main,
                player2.extra,
                (config or DuelConfig()).native(),
            ),
            self,
            DeckStart((player1, player2), config),
            seed,
        )
