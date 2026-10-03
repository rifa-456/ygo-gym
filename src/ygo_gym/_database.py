from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypeAlias

_TYPE_LINK = 0x04000000
_UINT32_MASK = 0xFFFFFFFF
_UINT64_MASK = 0xFFFFFFFFFFFFFFFF

CardRow: TypeAlias = tuple[
    int,
    int,
    tuple[int, ...],
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    int,
]


def load_card_rows(path: Path) -> list[CardRow]:
    with sqlite3.connect(path) as database:
        rows = database.execute(
            "SELECT id, alias, setcode, type, atk, def, level, race, attribute FROM datas"
        )
        return [_decode_row(row) for row in rows]


def _decode_row(row: tuple[int, ...]) -> CardRow:
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

    return (
        code & _UINT32_MASK,
        alias & _UINT32_MASK,
        setcodes,
        card_type & _UINT32_MASK,
        level,
        attribute & _UINT32_MASK,
        race & _UINT64_MASK,
        attack,
        defense,
        (packed_level_bits >> 24) & 0xFF,
        (packed_level_bits >> 16) & 0xFF,
        link_marker,
    )
