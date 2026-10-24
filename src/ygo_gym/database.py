from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

_TYPE_LINK = 0x04000000
_UINT32_MASK = 0xFFFFFFFF
_UINT64_MASK = 0xFFFFFFFFFFFFFFFF


@dataclass(frozen=True, slots=True)
class CardDefinition:
    code: int
    alias: int
    setcodes: tuple[int, ...]
    type: int
    level: int
    attribute: int
    race: int
    attack: int
    defense: int
    left_scale: int
    right_scale: int
    link_marker: int


@dataclass(frozen=True, slots=True)
class CardText:
    code: int
    name: str
    description: str
    strings: tuple[str, ...]


def read_card_rows(paths: Iterable[Path], query: str) -> dict[int, tuple]:
    """Key rows by their first column; later databases replace earlier ones, as in the engine."""
    rows = {}
    for path in paths:
        with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as database:
            for row in database.execute(query):
                rows[row[0] & _UINT32_MASK] = row
    return rows


def load_card_texts(paths: Iterable[Path]) -> dict[int, CardText]:
    strings = ", ".join(f"str{index}" for index in range(1, 17))
    rows = read_card_rows(paths, f"SELECT id, name, desc, {strings} FROM texts")
    return {
        code: CardText(code, name or "", description or "", tuple(value or "" for value in values))
        for code, (_, name, description, *values) in rows.items()
    }


def load_card_definitions(path: Path) -> list[CardDefinition]:
    with sqlite3.connect(path) as database:
        rows = database.execute(
            "SELECT id, alias, setcode, type, atk, def, level, race, attribute FROM datas"
        )
        return [decode_card_definition(row) for row in rows]


def decode_card_definition(row: tuple[int, ...]) -> CardDefinition:
    code, alias, packed_setcodes, card_type, attack, defense, packed_level, race, attribute = row

    packed_setcodes &= _UINT64_MASK
    setcodes = tuple(
        setcode
        for shift in range(0, 64, 16)
        if (setcode := (packed_setcodes >> shift) & 0xFFFF)
    )

    packed_level_bits = packed_level & _UINT32_MASK
    level = packed_level & 0xFF
    if packed_level < 0:
        level = (-level) & _UINT32_MASK

    link_marker = 0
    if card_type & _TYPE_LINK:
        link_marker = defense & _UINT32_MASK
        defense = 0

    return CardDefinition(
        code=code & _UINT32_MASK,
        alias=alias & _UINT32_MASK,
        setcodes=setcodes,
        type=card_type & _UINT32_MASK,
        level=level,
        attribute=attribute & _UINT32_MASK,
        race=race & _UINT64_MASK,
        attack=attack,
        defense=defense,
        left_scale=(packed_level_bits >> 24) & 0xFF,
        right_scale=(packed_level_bits >> 16) & 0xFF,
        link_marker=link_marker,
    )
