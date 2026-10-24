from __future__ import annotations

import base64
import binascii
import struct
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

_MAX_CARD_CODE = 0xFFFFFFFF
_YDKE_PREFIX = "ydke://"
_YDK_SECTIONS = {"#main": "main", "#extra": "extra", "!side": "side"}


def _normalize_cards(cards: Iterable[int], zone: str) -> tuple[int, ...]:
    normalized = tuple(cards)
    for code in normalized:
        if type(code) is not int:
            raise TypeError(f"{zone} card codes must be integers")
        if code <= 0 or code > _MAX_CARD_CODE:
            raise ValueError(f"{zone} card code {code} does not fit in uint32")
    return normalized


def _encode_ydke_zone(cards: tuple[int, ...]) -> str:
    return base64.b64encode(struct.pack(f"<{len(cards)}I", *cards)).decode("ascii")


def _decode_ydke_zone(value: str, zone: str) -> tuple[int, ...]:
    try:
        data = base64.b64decode(value, validate=True)
    except binascii.Error as error:
        raise ValueError(f"ydke {zone} section is not valid base64") from error
    if len(data) % 4:
        raise ValueError(f"ydke {zone} section is not a sequence of uint32 codes")
    return struct.unpack(f"<{len(data) // 4}I", data)


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

    @classmethod
    def from_ydk(cls, path: str | Path) -> Deck:
        return cls.parse_ydk(Path(path).read_text(encoding="utf-8-sig"))

    @classmethod
    def parse_ydk(cls, text: str) -> Deck:
        """Parse YGOPro .ydk text; other #/! lines, such as #created by, are ignored."""
        zones: dict[str, list[int]] = {"main": [], "extra": [], "side": []}
        zone = "main"
        for number, line in enumerate(text.removeprefix("﻿").splitlines(), 1):
            line = line.strip()
            if line in _YDK_SECTIONS:
                zone = _YDK_SECTIONS[line]
            elif line and not line.startswith(("#", "!")):
                if not line.isdecimal():
                    raise ValueError(f"ydk line {number} is not a card code: {line!r}")
                zones[zone].append(int(line))
        return cls(**zones)

    @classmethod
    def from_ydke(cls, uri: str) -> Deck:
        if not uri.startswith(_YDKE_PREFIX):
            raise ValueError("ydke URI must start with ydke://")
        sections = uri.removeprefix(_YDKE_PREFIX).split("!")
        if len(sections) != 4 or sections[3]:
            raise ValueError("ydke URI must contain main, extra, and side sections")
        main, extra, side = (
            _decode_ydke_zone(value, zone)
            for value, zone in zip(sections, ("main", "extra", "side"))
        )
        return cls(main, extra, side)

    def to_ydke(self) -> str:
        sections = (self.main, self.extra, self.side)
        return _YDKE_PREFIX + "!".join(map(_encode_ydke_zone, sections)) + "!"
