import pytest
from ygo_gym.agents.windbot.catalog import WindBotDeck
from ygo_gym.agents.windbot.runtime import WindBotError, build


def test_load_deck(tmp_path):
    path = tmp_path / "deck.ydk"
    path.write_text(
        "#created by test\n#main\n89631139\n#extra\n23995346\n!side\n53129443\n"
    )
    variant = WindBotDeck("test", "Test", path, "Normal", None, ())
    assert variant.available
    deck = variant.load()
    assert deck.main == (89631139,)
    assert deck.extra == (23995346,)
    assert deck.side == (53129443,)


def test_build_reports_missing_sdk(pytestconfig):
    with pytest.raises(WindBotError, match=".NET 8 SDK"):
        build(pytestconfig.rootpath, dotnet="ygo-gym-nonexistent-dotnet")
