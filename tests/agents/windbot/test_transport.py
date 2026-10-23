import struct

import pytest
from ygo_gym import Deck, Engine
from ygo_gym.action import ActionKind as Kind


@pytest.fixture
def client_engine(pytestconfig):
    engine = Engine.from_checkout(pytestconfig.rootpath)
    engine._native_engine._enable_client_protocol()
    return engine


def packets(observation, message):
    return [
        packet[2:]
        for packet in observation._client_batch[3]
        if packet[:2] == bytes((1, message))
    ]


def test_initial_draws_are_private(client_engine):
    first, second = 89631139, 46986414
    with client_engine.create_duel(
        Deck((first,) * 40), Deck((second,) * 40), seed=1
    ) as duel:
        for player, own in ((0, first), (1, second)):
            observation = duel.observe(player)
            assert observation._client_batch[2]
            draws = packets(observation, 90)
            assert draws
            for draw in draws:
                count = struct.unpack_from("<I", draw, 1)[0]
                identities = [
                    struct.unpack_from("<I", draw, 5 + 8 * index)[0]
                    for index in range(count)
                ]
                assert identities == [own if draw[0] == player else 0] * count
        p0 = duel.observe(0)._client_batch
        p1 = duel.observe(1)._client_batch
        assert p0[:3] == p1[:3]
        assert p0[3] != p1[3]


def test_response_plan_uses_legal_steps(client_engine):
    deck = Deck((89631139,) * 40)
    with client_engine.create_duel(deck, deck, seed=1) as duel:
        prompt = duel.decision
        if not hasattr(prompt, "can_end_phase"):
            pytest.skip("initial prompt differs from idle selection")
        plan = client_engine._native_engine._plan_client_response(
            duel.observation, struct.pack("<i", 7)
        )
        assert len(plan) == 1
        assert duel.actions[plan[0]].kind == Kind.END_PHASE
        index = duel.observation._client_batch[1]
        duel.step(plan[0])
        assert duel.observe(0)._client_batch[1] == index + 1


def test_clone_does_not_reuse_external_agent_history(client_engine):
    deck = Deck((89631139,) * 40)
    with client_engine.create_duel(deck, deck, seed=1) as duel:
        with duel.clone(preserve_rng=True) as branch:
            assert branch.observation._client_batch is None
        checkpoint = duel.checkpoint()
        duel.restore(checkpoint, preserve_rng=True)
        assert duel.observation._client_batch is None


def test_normal_engine_does_not_collect_protocol(pytestconfig):
    engine = Engine.from_checkout(pytestconfig.rootpath)
    deck = Deck((89631139,) * 40)
    with engine.create_duel(deck, deck, seed=1) as duel:
        assert duel.observation._client_batch is None


def test_opponent_identity_is_absent_from_query_updates(client_engine):
    with client_engine.create_duel(
        Deck((89631139,) * 40), Deck((46986414,) * 40), seed=1
    ) as duel:
        updates = packets(duel.observe(0), 6)
        assert updates
        for update in updates:
            if update[0] == 1:
                assert struct.pack("<I", 46986414) not in update


def test_partial_selection_plan_keeps_atomic_steps(engine, deck):
    engine = Engine(engine.card_database, engine.script_roots)
    engine._native_engine._enable_client_protocol()
    scripted = Deck((100000001,) * 40)
    with engine.create_duel(scripted, deck, seed=123) as duel:
        for _ in range(20):
            if any(action.kind == Kind.SELECT_CARD for action in duel.actions):
                break
            choices = (Kind.ACTIVATE, Kind.PASS, Kind.NO, Kind.SELECT_ZONE)
            selected = next(
                index
                for kind in choices
                for index, action in enumerate(duel.actions)
                if action.kind == kind
            )
            duel.step(selected)
        else:
            pytest.fail("script did not reach card selection")
        response = struct.pack("<iiii", 0, 2, 0, 1)
        with pytest.raises(ValueError, match="legal semantic action"):
            engine._native_engine._plan_client_response(
                duel.observation, struct.pack("<iii", 0, 1, 0)
            )
        assert not duel.pending_actions
        plan = engine._native_engine._plan_client_response(duel.observation, response)
        assert len(plan) == 3
        for index in plan:
            duel.step(index)
        assert not duel.pending_actions


def test_semantic_status_is_masked_with_the_card(client_engine):
    deck = Deck((89631139,) * 40)
    with client_engine.create_duel(deck, deck, seed=1) as duel:
        own = [
            card
            for card in duel.observe(0).cards
            if int(card.controller) == 0 and int(card.location) == 2
        ]
        hidden = [
            card
            for card in duel.observe(1).cards
            if int(card.controller) == 0 and int(card.location) == 2
        ]
        assert own and hidden
        assert all(isinstance(card.properties.effects_disabled, bool) for card in own)
        assert all(isinstance(card.properties.summon_completed, bool) for card in own)
        assert all(card.properties is None for card in hidden)
