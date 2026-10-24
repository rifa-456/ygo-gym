import pytest
from hypothesis import given, settings, strategies as st
from ygo_gym import (
    ActionKind, CardSetup, Deck, DeckRules, DuelConfig, DuelRule, DuelSetup, Location, Match, MatchRules, PlayerSetup,
    Puzzle, Replay, ReplayUnavailableError, play_match,
)
from ygo_gym.agents import RandomAgent
from ygo_gym.dataset.codec import capture
from ygo_gym.protocol import IdleCommand

MIXED = Deck(main=(69247929, 89631139, 46986414, 55144522, 100000001) * 8)


@given(seed=st.integers(0, 2**64 - 1), choices=st.lists(st.integers(0, 65535), max_size=60))
@settings(max_examples=20, deadline=None)
def test_replays_reproduce_random_games(engine, seed, choices):
    with engine.create_duel(MIXED, MIXED, seed) as duel:
        for choice in choices:
            if duel.terminated:
                break
            duel.step(choice % len(duel.actions))
        replay = duel.replay()
        assert Replay.from_record(replay.record()) == replay
        with replay.play(engine) as again:
            assert capture(again) == capture(duel)
            assert again.replay() == replay


def test_configured_scripted_and_puzzle_starts_replay(engine):
    config = DuelConfig(flags=DuelRule.MODE_MR3, life_points=(1234, 5678), shuffle=False)
    deck = Deck((69247929, 89631139, 46986414) * 3)
    setup = DuelSetup((PlayerSetup(), PlayerSetup()), cards=(CardSetup(69247929, 0, 0, Location.HAND, 0),))
    puzzle = Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua")
    games = (
        engine.create_duel(deck, deck, seed=5, config=config),
        engine.create_duel(setup=setup, seed=5),
        puzzle.start(engine, seed=5).duel,
    )
    for duel in games:
        with duel:
            duel.step(0)
            replay = duel.replay()
            assert Replay.from_record(replay.record()) == replay
            with replay.play(engine) as again:
                assert capture(again) == capture(duel)


def test_preserved_branches_inherit_history_and_reseeded_branches_raise(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel:
        duel.step(0)
        with duel.clone(preserve_rng=True) as branch:
            branch.step(0)
            assert branch.replay().actions == duel.replay().actions + (0,)
        with duel.clone() as branch, pytest.raises(ReplayUnavailableError, match="reseeded"):
            branch.replay()
        with duel.clone(seed=3) as branch, pytest.raises(ReplayUnavailableError):
            branch.replay()


def test_restores_follow_their_checkpoint(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel:
        duel.step(0)
        checkpoint = duel.checkpoint()
        expected = duel.replay()
        duel.step(0)
        duel.restore(checkpoint, preserve_rng=True)
        assert duel.replay() == expected
        duel.restore(checkpoint)
        with pytest.raises(ReplayUnavailableError, match="new randomness"):
            duel.replay()
        duel.restore(checkpoint, preserve_rng=True)
        assert duel.replay() == expected


def test_deserialized_duels_have_no_start(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel, engine.deserialize(duel.serialize()) as restored:
        with pytest.raises(ReplayUnavailableError, match="known start"):
            restored.replay()


def test_raw_responses_are_recorded_as_actions(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel, engine.create_duel(deck, deck, seed=1) as reference:
        end = next(i for i, action in enumerate(duel.actions) if action.kind == ActionKind.END_PHASE)
        duel.respond(duel.decision.response(IdleCommand.END_PHASE))
        reference.step(end)
        assert duel.replay().actions == reference.replay().actions == (end,)
        with duel.replay().play(engine) as again:
            assert capture(again) == capture(reference)


def test_match_duels_carry_replays(engine, deck):
    with Match(engine, (deck, deck), rules=MatchRules(best_of=1, side_decking=False, max_steps_per_duel=40, decks=DeckRules.unrestricted()), seed=2) as match:
        result = play_match(match, agents=(_MatchRandom(), _MatchRandom()), seed=2)
    for duel in result.duels:
        assert duel.replay is not None and duel.replay.seed == duel.seed
        with duel.replay.play(engine) as again:
            assert again.terminated == (duel.reason != "step_limit")


class _MatchRandom(RandomAgent):
    def match_reset(self, match):
        pass

    def choose_first(self, decision):
        return 0

    def match_end(self, result):
        pass
