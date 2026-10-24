import pytest
from hypothesis import given, strategies as st
from ygo_gym import Deck

codes = st.lists(st.integers(1, 0xFFFFFFFF), max_size=60)


def test_ydk_sections_comments_and_bom():
    text = "﻿#created by someone\n#main\n89631139\n 46986414 \n\n#extra\n44508094\n!side\n55144522\n"
    assert Deck.parse_ydk(text) == Deck((89631139, 46986414), (44508094,), (55144522,))


def test_ydk_without_sections_is_main_deck():
    assert Deck.parse_ydk("89631139\n89631139\n") == Deck((89631139, 89631139))


def test_ydk_rejects_non_code_lines():
    with pytest.raises(ValueError, match="line 2"):
        Deck.parse_ydk("#main\nBlue-Eyes\n")


def test_ydk_file(tmp_path):
    path = tmp_path / "deck.ydk"
    path.write_text("#main\n89631139\n#extra\n!side\n", encoding="utf-8-sig")
    assert Deck.from_ydk(path) == Deck((89631139,))


@given(main=codes, extra=codes, side=codes)
def test_ydke_round_trip(main, extra, side):
    deck = Deck(main, extra, side)
    assert Deck.from_ydke(deck.to_ydke()) == deck


def test_ydke_known_encoding():
    assert Deck((1, 2), (), (3,)).to_ydke() == "ydke://AQAAAAIAAAA=!!AwAAAA==!"


@pytest.mark.parametrize("uri", ["ydk://!!!", "ydke://AQAAAA==!!", "ydke://AQAAAA==!!!x", "ydke://AQAA!!!", "ydke://@@@@!!!"])
def test_ydke_rejects_malformed_uris(uri):
    with pytest.raises(ValueError):
        Deck.from_ydke(uri)


def test_windbot_decks_load_through_ydk(pytestconfig):
    paths = sorted((pytestconfig.rootpath / "third_party/WindBot/Decks").glob("*.ydk"))
    assert paths
    for path in paths:
        deck = Deck.from_ydk(path)
        assert len(deck.main) >= 40
        assert Deck.from_ydke(deck.to_ydke()) == deck
