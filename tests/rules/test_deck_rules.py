import pytest

from ygo_gym import Deck, DeckRules, Match, MatchRules
from ygo_gym.database import load_card_definitions


def definitions(engine):
    return {c.code: c for c in load_card_definitions(engine.card_database)}


def test_validation_checks_aliases_placements_pool_and_limits(engine):
    cards = definitions(engine)
    rules = DeckRules(main_size=(1, 60), limits={69247929: 1})
    rules.validate(Deck((69247929,)), cards)
    with pytest.raises(ValueError, match="copy limit"):
        rules.validate(Deck((69247929,) * 2), cards)
    with pytest.raises(ValueError, match="cannot be placed"):
        rules.validate(Deck((69247929,), extra=(69247929,)), cards)
    with pytest.raises(ValueError, match="pool"):
        DeckRules(main_size=(1, 60), allowed_cards=frozenset({89631139})).validate(
            Deck((69247929,)), cards
        )
    alias = next(
        c
        for c in cards.values()
        if c.alias in cards
        and c.type == cards[c.alias].type
        and not c.type & (0x40 | 0x2000 | 0x800000 | 0x4000000 | 0x4000 | 0x8000000)
    )
    with pytest.raises(ValueError, match="copy limit"):
        DeckRules(main_size=(1, 60), copy_limit=1).validate(
            Deck((alias.code, alias.alias)), cards
        )


def test_registered_inventory_and_zone_sizes_are_enforced(engine):
    cards = definitions(engine)
    rules = DeckRules(main_size=(1, 60))
    original = Deck((69247929,), side=(89631139,))
    rules.validate_side(original, Deck((89631139,), side=(69247929,)), cards)
    with pytest.raises(ValueError, match="size"):
        rules.validate_side(original, Deck((69247929, 89631139)), cards)
    with pytest.raises(ValueError, match="inventory"):
        rules.validate_side(original, Deck((69247929,), side=(69247929,)), cards)


def test_edopro_banlist_sections_and_whitelists(tmp_path, engine):
    file = tmp_path / "lflist.conf"
    file.write_text("!Limited\n69247929 1\n!Only these\n$whitelist\n89631139 3\n")
    rules = DeckRules.from_banlist(file, "Only these", main_size=(1, 60))
    rules.validate(Deck((89631139,)), definitions(engine))
    with pytest.raises(ValueError, match="pool"):
        rules.validate(Deck((69247929,)), definitions(engine))
    with pytest.raises(ValueError, match="select"):
        DeckRules.from_banlist(file)


def test_default_match_rules_reject_the_unrestricted_fixture_deck(engine, deck):
    with pytest.raises(ValueError, match="copy limit"):
        Match(engine, (deck, deck), rules=MatchRules())
