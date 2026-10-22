import pytest

from ygo_gym import (
    ActionKind,
    CardSetup,
    DuelSetup,
    Location,
    Phase,
    PlayerSetup,
    Position,
)


def setup_cards(*cards):
    return DuelSetup(players=(PlayerSetup(), PlayerSetup()), cards=cards)


def codes(duel, player, location):
    state = duel.state()
    return [state.cards[index].code for index in state.zone(player, location)]


def test_ordered_zones_and_no_opening_draw(engine):
    cards = tuple(
        CardSetup(code=code, owner=0, controller=0, location=location, sequence=index)
        for location, values in (
            (Location.DECK, (46986414, 89631139)),
            (Location.GRAVEYARD, (69247929, 55144522)),
            (Location.HAND, (55144522,)),
            (Location.EXTRA_DECK, (23995346, 75286621)),
            (Location.BANISHED, (69247929, 89631139)),
        )
        for index, code in enumerate(values)
    )
    with engine.create_duel(setup=setup_cards(*cards), seed=42) as duel:
        assert codes(duel, 0, Location.DECK) == [46986414, 89631139]
        assert codes(duel, 0, Location.GRAVEYARD) == [69247929, 55144522]
        assert codes(duel, 0, Location.HAND) == [55144522]
        assert codes(duel, 0, Location.EXTRA_DECK) == [23995346, 75286621]
        assert codes(duel, 0, Location.BANISHED) == [69247929, 89631139]
        assert duel.observation.global_state.phase == Phase.MAIN1
        duel.step(
            next(i for i, a in enumerate(duel.actions) if a.kind == ActionKind.ACTIVATE)
        )
        for _ in range(20):
            if len(codes(duel, 0, Location.DECK)) == 0:
                break
            choices = [
                i
                for kind in (ActionKind.SELECT_ZONE, ActionKind.PASS, ActionKind.YES)
                for i, a in enumerate(duel.actions)
                if a.kind == kind
            ]
            assert choices
            duel.step(choices[0])
        assert codes(duel, 0, Location.HAND) == [89631139, 46986414]


def test_field_ownership_slots_and_visibility(engine):
    setup = setup_cards(
        CardSetup(
            code=69247929,
            owner=1,
            controller=0,
            location=Location.MONSTER_ZONE,
            sequence=3,
            position=Position.FACEDOWN_DEFENSE,
        )
    )
    with engine.create_duel(setup=setup) as duel:
        card = duel.state().cards[0]
        assert int(card.owner) == 1 and int(card.controller) == 0 and card.sequence == 3
        assert duel.observe(0).cards[0].code == 69247929
        assert duel.observe(1).cards[0].code == 0


def test_empty_decks_and_first_turn_only_phase_skips(engine):
    with engine.create_duel(setup=setup_cards()) as duel:
        assert duel.observation.global_state.phase == Phase.MAIN1
        for _ in range(12):
            if duel.terminated:
                break
            index = next(
                i
                for kind in (ActionKind.END_PHASE, ActionKind.PASS)
                for i, a in enumerate(duel.actions)
                if a.kind == kind
            )
            duel.step(index)
        assert duel.terminated and int(duel.outcome.winner) == 0


def test_setup_rejects_structural_errors():
    card = CardSetup(69247929, 0, 0, Location.DECK, 1)
    with pytest.raises(ValueError, match="contiguous"):
        setup_cards(card)
    with pytest.raises(ValueError, match="duplicate"):
        setup_cards(card, card)
    with pytest.raises(ValueError):
        PlayerSetup(draw_count=-1)
    with pytest.raises(ValueError, match="overlay"):
        CardSetup(69247929, 0, 0, Location.OVERLAY, 0)


def test_missing_card_and_mixed_initialization_rejected(engine, deck):
    with pytest.raises(RuntimeError, match="no entry"):
        engine.create_duel(
            setup=setup_cards(CardSetup(4294967295, 0, 0, Location.HAND, 0))
        )
    with pytest.raises(ValueError, match="combined"):
        engine.create_duel(deck, deck, setup=setup_cards())
