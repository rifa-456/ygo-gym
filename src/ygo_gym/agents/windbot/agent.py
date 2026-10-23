from __future__ import annotations

import base64
import hashlib
import math
import sqlite3
from collections import deque
from pathlib import Path

from ...deck import Deck
from .catalog import available_decks
from .runtime import WindBotError, Worker, build, checkout


def _card_rows(engine):
    cards = {}
    for path in engine.card_databases:
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
            for row in connection.execute(
                "SELECT d.id,d.ot,d.alias,d.setcode,d.type,d.level,d.race,d.attribute,d.atk,d.def,t.name,t.desc "
                "FROM datas d JOIN texts t ON d.id=t.id"
            ):
                cards[row[0]] = (*row[:10], row[10] or "", row[11] or "")
    return list(cards.values())


class WindBotAgent:
    """An upstream executor session driven by masked native client messages.

    Construct before creating duels on this Engine. Start play at the initial
    decision; existing WindBot memory cannot be reconstructed from a clone or
    engine snapshot. Each seat requires a separate instance.
    """

    available_decks = staticmethod(available_decks)
    build = staticmethod(build)

    def __init__(
        self,
        engine,
        *,
        deck: str,
        root: str | Path | None = None,
        dotnet: str = "dotnet",
        timeout: float = 30.0,
    ):
        if not isinstance(deck, str) or not deck:
            raise ValueError("deck must be a WindBot executor ID")
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("timeout must be positive")
        self.root = checkout(root)
        self.engine = engine
        choices = {
            entry.id: entry for entry in available_decks(self.root, dotnet=dotnet)
        }
        if deck not in choices:
            raise ValueError(
                f"Unknown WindBot executor {deck!r}; use available_decks()"
            )
        self.variant = choices[deck]
        self.deck = self.variant.load()
        self.worker = Worker(
            build(self.root, dotnet=dotnet), dotnet=dotnet, timeout=timeout
        )
        try:
            self.cards = _card_rows(engine)
        except BaseException:
            self.worker.close()
            raise
        self.closed = False
        self._player = None
        self._session = None
        self._last_batch = -1
        self._plan = deque()
        self._started = False
        engine._native_engine._enable_client_protocol()

    def reset(self, *, player, seed: int) -> None:
        if self.closed:
            raise WindBotError("WindBot agent is closed")
        if int(player) not in (0, 1):
            raise ValueError("player must be 0 or 1")
        if type(seed) is not int or not 0 <= seed <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("seed must fit in uint64")
        self._player = int(player)
        self._session = None
        self._last_batch = -1
        self._plan.clear()
        self._started = False
        encoded_seed = (
            int.from_bytes(
                hashlib.sha256(seed.to_bytes(8, "little")).digest()[:4], "little"
            )
            & 0x7FFFFFFF
        )
        encode_zone = lambda cards: base64.b64encode(
            b"".join(code.to_bytes(4, "little") for code in cards)
        ).decode()
        deck_uri = (
            "ydke://"
            + "!".join(
                encode_zone(cards)
                for cards in (self.deck.main, self.deck.extra, self.deck.side)
            )
            + "!"
        )
        self.worker.request(
            op="reset",
            deck=self.variant.id,
            assets=str(self.root / "third_party/WindBot"),
            deck_file=deck_uri,
            seed=encoded_seed,
            cards=self.cards,
        )
        self._started = True

    def _feed(self, updates):
        packets = []
        for observation in updates:
            if int(observation.viewer) != self._player:
                raise WindBotError("WindBot received another player's observation")
            batch = observation._client_batch
            if batch is None:
                raise WindBotError(
                    "Create WindBotAgent before creating the duel; cloned and restored duels do not carry WindBot memory"
                )
            session, index, initial, values = batch
            if self._session is None:
                if not initial:
                    raise WindBotError(
                        "WindBot must receive the duel's initial observation"
                    )
                self._session = session
            if session != self._session or index < self._last_batch:
                raise WindBotError(
                    "WindBot received a different or rewound duel without reset"
                )
            if index == self._last_batch:
                continue
            if index != self._last_batch + 1:
                raise WindBotError(
                    "WindBot missed client updates; deliver every observation through AgentInput.updates"
                )
            self._last_batch = index
            packets.extend(base64.b64encode(value).decode() for value in values)
        if not packets:
            return []
        result = self.worker.request(op="feed", packets=packets)
        if result["surrendered"]:
            raise WindBotError(
                "WindBot requested surrender; no legal action is substituted"
            )
        if result["closed"]:
            raise WindBotError("WindBot closed its client session")
        return [base64.b64decode(value) for value in result["responses"]]

    def act(self, decision) -> int:
        if not self._started or self.closed:
            raise WindBotError("WindBot must be reset before acting")
        responses = self._feed(decision.updates)
        if responses:
            if self._plan or len(responses) != 1:
                raise WindBotError("WindBot produced unexpected concurrent decisions")
            try:
                self._plan.extend(
                    self.engine._native_engine._plan_client_response(
                        decision.observation, responses[0]
                    )
                )
            except (ValueError, RuntimeError, IndexError) as error:
                raise WindBotError(
                    f"Executor {self.variant.id} returned an unsupported or illegal response: {error}"
                ) from error
        if not self._plan:
            raise WindBotError(
                "WindBot did not produce a response to the current decision"
            )
        index = self._plan.popleft()
        if not 0 <= index < len(decision.actions):
            raise WindBotError(
                "WindBot action plan no longer matches the current legal actions"
            )
        return index

    def end(self, episode) -> None:
        if self._started and not self.closed:
            responses = self._feed(episode.updates)
            if responses and not episode.result.truncated:
                raise WindBotError(
                    "WindBot received an unanswered decision at natural termination"
                )
        self._started = False
        self._plan.clear()

    def match_reset(self, match) -> None:
        if match.deck != self.deck:
            raise ValueError("Match deck does not match this WindBot agent's deck")
        self.reset(player=match.player, seed=match.seed)

    def side_deck(self, decision) -> Deck:
        return decision.deck

    def choose_first(self, decision) -> int:
        go_first = self.worker.request(op="first")
        return int(decision.player) if go_first else 1 - int(decision.player)

    def match_end(self, result) -> None:
        pass

    def close(self) -> None:
        if not self.closed:
            self.worker.close()
            self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
