import pytest
from hypothesis import given, reject, settings, strategies as st
from ygo_gym import Deck, Engine
from ygo_gym.action import ActionKind as Kind
from ygo_gym.agents import AgentInput, InvalidChoiceError

WINDBOT_DECKS = ("AI_Salamangreat.ydk", "AI_Swordsoul.ydk", "AI_Zoodiac.ydk", "AI_BlueEyes.ydk")
MIXED = Deck(main=(69247929, 89631139, 46986414, 55144522, 100000001) * 8)
DECISIONS = 40
WALK_LIMIT = 64


def decision(duel) -> AgentInput:
    return AgentInput(duel.observation, tuple(duel.actions), ())


def walk(duel, draw):
    """Take random atomic steps on a branch until its current decision completes."""
    chosen, indices = [], []
    with duel.clone(preserve_rng=True) as branch:
        while len(indices) < WALK_LIMIT:
            index = draw(st.integers(0, len(branch.actions) - 1))
            chosen.append(branch.actions[index])
            indices.append(index)
            branch.step(index)
            if branch.terminated or not branch.pending_actions:
                return chosen, tuple(indices)
    reject()


def check_walks(duel, data):
    for _ in range(DECISIONS):
        if duel.terminated:
            return
        start = decision(duel)
        chosen, indices = walk(duel, data.draw)
        assert start.expand(chosen) == indices
        for index in indices:
            duel.step(index)


def selection(engine, deck):
    duel = engine.create_duel(Deck((100000001,) * 40), deck, seed=123)
    choices = (Kind.ACTIVATE, Kind.PASS, Kind.NO, Kind.SELECT_ZONE)
    for _ in range(20):
        if any(action.kind == Kind.SELECT_CARD for action in duel.actions):
            return duel
        duel.step(next(
            index
            for kind in choices
            for index, action in enumerate(duel.actions)
            if action.kind == kind
        ))
    duel.close()
    pytest.fail("script did not reach card selection")


@given(seed=st.integers(0, 2**64 - 1), data=st.data())
@settings(max_examples=20, deadline=None)
def test_expansion_reproduces_random_walks_with_scripted_cards(engine: Engine, seed, data):
    with engine.create_duel(MIXED, MIXED, seed) as duel:
        check_walks(duel, data)


@pytest.mark.parametrize("name", WINDBOT_DECKS)
@given(seed=st.integers(0, 2**64 - 1), data=st.data())
@settings(max_examples=5, deadline=None)
def test_expansion_reproduces_random_walks_with_real_decks(engine: Engine, pytestconfig, name, seed, data):
    deck = Deck.from_ydk(pytestconfig.rootpath / "third_party/WindBot/Decks" / name)
    with engine.create_duel(deck, deck, seed) as duel:
        check_walks(duel, data)


def test_selection_implies_a_legal_confirm(engine, deck):
    with selection(engine, deck) as duel:
        start = decision(duel)
        cards = [action for action in start.actions if action.kind == Kind.SELECT_CARD]
        two, three = start.expand(cards[:2]), start.expand(cards[:3])
        assert len(two) == 3 and len(three) == 4
        for index in two[:2]:
            duel.step(index)
        assert duel.actions[two[2]].kind == Kind.CONFIRM
        duel.step(two[2])
        assert not duel.pending_actions


def test_expansion_continues_a_partial_selection(engine, deck):
    with selection(engine, deck) as duel:
        first = next(index for index, action in enumerate(duel.actions) if action.kind == Kind.SELECT_CARD)
        duel.step(first)
        partial = decision(duel)
        second = next(action for action in partial.actions if action.kind == Kind.SELECT_CARD)
        for index in partial.expand([second]):
            duel.step(index)
        assert not duel.pending_actions


def test_invalid_choices_name_the_failing_action(engine, deck):
    with selection(engine, deck) as duel:
        start = decision(duel)
        card = next(action for action in start.actions if action.kind == Kind.SELECT_CARD)
        with pytest.raises(InvalidChoiceError, match="not complete") as incomplete:
            start.expand([card])
        assert incomplete.value.step == 1
        with pytest.raises(InvalidChoiceError, match="not legal") as repeated:
            start.expand([card, card, card])
        assert repeated.value.step == 1
        assert not duel.pending_actions


def test_trailing_actions_after_completion_are_rejected(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel:
        start = decision(duel)
        last = start.actions[-1]
        assert start.expand([last]) == (len(start.actions) - 1,)
        with pytest.raises(InvalidChoiceError, match="already complete") as error:
            start.expand([last, last])
        assert error.value.step == 1
        assert isinstance(error.value, ValueError)


def test_observations_without_a_decision_cannot_expand(engine, deck):
    with engine.create_duel(deck, deck, seed=1) as duel:
        waiting = duel.observe(1 - int(duel.current_player))
        with pytest.raises(ValueError, match="no decision"):
            AgentInput(waiting, (), ()).expand([duel.actions[0]])
