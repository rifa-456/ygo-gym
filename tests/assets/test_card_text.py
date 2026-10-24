import sqlite3

import pytest
from ygo_gym import CardText, Engine

BLUE_EYES = 89631139
NEW_CARD = 100000003


def test_card_text_reads_names_descriptions_and_strings(engine):
    text = engine.card_text(BLUE_EYES)
    assert isinstance(text, CardText)
    assert text.code == BLUE_EYES
    assert text.name == "Blue-Eyes White Dragon"
    assert text.description
    assert len(text.strings) == 16


def test_unknown_codes_raise_key_error(engine):
    with pytest.raises(KeyError):
        engine.card_text(1)


def test_additional_databases_take_precedence(engine, tmp_path):
    database = tmp_path / "extra.cdb"
    with sqlite3.connect(engine.card_database) as source, sqlite3.connect(database) as target:
        for (sql,) in source.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('datas','texts')"):
            target.execute(sql)
        strings = ", ".join(f"str{index}" for index in range(1, 17))
        target.executemany(
            "INSERT INTO datas (id, ot, alias, setcode, type, atk, def, level, race, attribute, category) "
            "VALUES (?, 0, 0, 0, 17, 0, 0, 1, 1, 1, 0)",
            [(BLUE_EYES,), (NEW_CARD,)],
        )
        target.executemany(
            f"INSERT INTO texts (id, name, desc, {strings}) VALUES (?, ?, ?, {', '.join('?' * 16)})",
            [(BLUE_EYES, "Override", "changed", *[""] * 16), (NEW_CARD, "New", None, "first", *[None] * 15)],
        )
    custom = Engine(engine.card_database, engine.script_roots, additional_card_databases=(database,))
    assert custom.card_text(BLUE_EYES).name == "Override"
    new = custom.card_text(NEW_CARD)
    assert new.description == ""
    assert new.strings[0] == "first" and new.strings[1:] == ("",) * 15
