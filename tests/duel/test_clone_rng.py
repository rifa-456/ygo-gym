from contextlib import ExitStack

import pytest
from ygo_gym import Deck, Duel, Engine
from ygo_gym.action import ActionKind as Kind
from ygo_gym.protocol import YesNoDecision

from .comparison import choose, duel as snapshot


def suspend_random_effect(engine: Engine, opponent: Deck) -> Duel:
    source = engine.create_duel(Deck(main=(100000002,) * 40), opponent, seed=123)
    try:
        source.step(choose(source, Kind.ACTIVATE))
        for _ in range(16):
            if isinstance(source.decision, YesNoDecision):
                return source
            source.step(choose(source, Kind.SELECT_ZONE, Kind.PASS, Kind.NO))
        raise AssertionError("random effect did not suspend")
    except BaseException:
        source.close()
        raise


def resume_random_effect(duel: Duel) -> tuple[int, int, int]:
    duel.step(choose(duel, Kind.YES))
    assert isinstance(duel.decision, YesNoDecision)
    return (*duel.state().global_state.life_points, duel.decision.description)


@pytest.mark.parametrize("seed", [0, 42, 2**64 - 1])
def test_seeded_suspended_effect_is_reproducible(engine: Engine, deck: Deck, seed: int) -> None:
    with suspend_random_effect(engine, deck) as source:
        before = snapshot(source)
        with source.clone(seed=seed) as a, source.clone(seed=seed) as b:
            assert snapshot(a) == snapshot(b) == before
            assert resume_random_effect(a) == resume_random_effect(b)
            assert snapshot(a) == snapshot(b)
            assert snapshot(source) == before


def test_each_random_stream_is_reseeded_without_replacing_script_locals(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as source, ExitStack() as stack:
        branches = [stack.enter_context(source.clone(seed=seed)) for seed in range(4)]
        outputs = [resume_random_effect(branch) for branch in branches]
        assert len({value[0] for value in outputs}) > 1
        assert len({value[1] for value in outputs}) > 1
        assert len({value[2] for value in outputs}) == 1


def test_default_clone_preserves_position_and_source(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as source:
        before = snapshot(source)
        with source.clone() as branch:
            assert snapshot(branch) == before
            resume_random_effect(branch)
            assert snapshot(source) == before


def test_exact_clone_after_seeded_clone_and_parent_destruction(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as source:
        with source.clone(seed=99) as parent:
            a = parent.clone(preserve_rng=True)
            b = parent.clone(preserve_rng=True)
        source.close()
        with a, b:
            assert resume_random_effect(a) == resume_random_effect(b)
            assert snapshot(a) == snapshot(b)


@pytest.mark.parametrize("options, error", [
    ({"seed": -1}, ValueError),
    ({"seed": 2**64}, ValueError),
    ({"seed": True}, TypeError),
    ({"seed": 1.5}, TypeError),
    ({"preserve_rng": 1}, TypeError),
    ({"preserve_rng": True, "seed": 42}, ValueError),
])
def test_invalid_rng_options(duel: Duel, options, error) -> None:
    before = snapshot(duel)
    with pytest.raises(error):
        duel.clone(**options)
    assert snapshot(duel) == before


def test_cloning_does_not_consume_source_randomness(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as source:
        with source.clone(preserve_rng=True) as control:
            for options in ({}, {"seed": 0}, {"seed": 42}, {"preserve_rng": True}):
                with source.clone(**options) as temporary:
                    resume_random_effect(temporary)
            assert resume_random_effect(source) == resume_random_effect(control)
            assert snapshot(source) == snapshot(control)


def test_same_duel_seed_initializes_lua_and_core_random_streams(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as first, suspend_random_effect(engine, deck) as second:
        assert first.decision.description == second.decision.description
        assert resume_random_effect(first) == resume_random_effect(second)
