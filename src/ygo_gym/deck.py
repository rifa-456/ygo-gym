from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

_MAX_CARD_CODE = 0xFFFFFFFF


def _normalize_cards(cards: Iterable[int], zone: str) -> tuple[int, ...]:
    normalized = tuple(cards)
    for code in normalized:
        if type(code) is not int:
            raise TypeError(f"{zone} card codes must be integers")
        if code <= 0 or code > _MAX_CARD_CODE:
            raise ValueError(f"{zone} card code {code} does not fit in uint32")
    return normalized


@dataclass(frozen=True, slots=True, init=False)
class Deck:
    main: tuple[int, ...]
    extra: tuple[int, ...]
    side: tuple[int, ...]

    def __init__(
        self,
        main: Iterable[int],
        extra: Iterable[int] = (),
        side: Iterable[int] = (),
    ) -> None:
        object.__setattr__(self, "main", _normalize_cards(main, "main deck"))
        object.__setattr__(self, "extra", _normalize_cards(extra, "extra deck"))
        object.__setattr__(self, "side", _normalize_cards(side, "side deck"))
