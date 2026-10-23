from dataclasses import replace

import pytest

from ygo_gym import Deck, DeckRules, DuelConfig, Match, MatchPhase, MatchRules

A, B = 69247929, 89631139


def rules(**changes):
    return MatchRules(first_player=0, decks=DeckRules.unrestricted(), **changes)


def decks():
    return (Deck((A,) * 10, side=(B,)), Deck((A,) * 10, side=(B,)))


def test_best_of_five_and_seats_are_stable_match_identities(engine):
    with Match(engine, decks(), rules=rules(best_of=5), seed=3) as match:
        match.surrender(1)
        assert match.scores == (1, 0)
        assert match.phase == MatchPhase.SIDE_DECKING
        match.submit_side(1, match.side_deck_input(1).deck)
        match.submit_side(0, match.side_deck_input(0).deck)
        assert match.decision.player == 1
        match.choose_first(1, 1)
        assert match.seat_players == (1, 0)
        assert match.current_player == 1
        match.surrender(1)
        assert match.scores == (2, 0)
        assert not match.ended
        match.submit_side(0, match.side_deck_input(0).deck)
        match.submit_side(1, match.side_deck_input(1).deck)
        match.choose_first(1, 0)
        match.surrender(1)
        assert match.result.winner == 0
        assert match.result.returns == (1.0, -1.0)
        assert match.result.scores == (3, 0)
        assert len(match.result.duels) == 3
    assert match.result.scores == (3, 0)


def test_side_submissions_are_private_and_transactional(engine):
    with Match(engine, decks(), rules=rules(), seed=1) as match:
        match.surrender(0)
        own = match.side_deck_input(0)
        changed = Deck((B,) + (A,) * 9, side=(A,))
        match.submit_side(0, changed)
        assert match.side_deck_input(1).deck == own.deck
        assert not hasattr(match.side_deck_input(1), "opponent_deck")
        assert match.side_deck_input(0).deck == own.deck
        with pytest.raises(RuntimeError, match="already submitted"):
            match.submit_side(0, own.deck)
        with pytest.raises(ValueError, match="inventory"):
            match.submit_side(1, Deck((A,) * 10, side=(A,)))
        assert match.phase == MatchPhase.SIDE_DECKING
        match.submit_side(1, own.deck)
        match.choose_first(0, 0)
        assert match.duel.observe(0).cards
        assert len(match.duels) == 1


def test_player_specific_initial_values_follow_seat_swaps(engine):
    config = DuelConfig(
        life_points=(1234, 5678), opening_hand=(2, 3), draw_count=(0, 0)
    )
    with Match(engine, decks(), rules=rules(duel=config), seed=0) as match:
        match.surrender(0)
        for player in (0, 1):
            match.submit_side(player, match.side_deck_input(player).deck)
        match.choose_first(0, 1)
        assert match.duel.state().player(0).life_points == 5678
        assert match.duel.state().player(1).life_points == 1234
        assert match.duel.state().player(0).starting_hand_size == 3


def test_initial_choice_permissions_and_disabled_siding(engine):
    config = replace(rules(side_decking=False), first_player=None, initial_chooser=1)
    with Match(engine, decks(), rules=config, seed=2) as match:
        assert match.duel is None
        assert match.current_player == 1
        with pytest.raises(RuntimeError):
            match.choose_first(0, 0)
        match.choose_first(1, 0)
        match.surrender(0)
        assert match.phase == MatchPhase.FIRST_PLAYER
        assert match.current_player == 0
        with pytest.raises(RuntimeError):
            match.submit_side(0, decks()[0])
        match.choose_first(0, 1)
        assert match.seat_players == (1, 0)


def test_close_is_not_a_match_outcome_and_surrender_is_explicit(engine):
    match = Match(engine, decks(), rules=rules())
    match.close()
    assert match.result is None and match.phase == MatchPhase.CLOSED
    with pytest.raises(RuntimeError):
        match.surrender(0)
    with Match(engine, decks(), rules=rules()) as match:
        match.surrender(1, entire_match=True)
        assert match.result.reason == "surrender"
        assert match.result.winner == 0
        assert not match.duels


@pytest.mark.parametrize(
    "changes",
    [
        {"best_of": 0},
        {"best_of": True},
        {"max_duels": 0},
        {"first_player": True},
        {"initial_chooser": 2},
        {"draw_policy": "unknown"},
    ],
)
def test_invalid_match_rules(changes):
    with pytest.raises((TypeError, ValueError)):
        MatchRules(**changes)
