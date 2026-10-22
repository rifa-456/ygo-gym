import gc

import pytest
from ygo_gym import Checkpoint, Deck, Duel, Engine
from ygo_gym.action import ActionKind as Kind

from .comparison import choose, duel as snapshot, observation
from .test_clone_rng import suspend_random_effect, resume_random_effect


def test_repeated_restore_and_clone(duel: Duel) -> None:
    checkpoint = duel.checkpoint()
    assert isinstance(checkpoint, Checkpoint)
    root = snapshot(duel)
    saved = duel.observation
    saved_values = observation(saved)
    for _ in range(20):
        with duel.clone(preserve_rng=True) as reference:
            for _ in range(8):
                if duel.terminated:
                    break
                action = choose(duel, Kind.SUMMON, Kind.SELECT_ZONE, Kind.PASS, Kind.END_PHASE)
                duel.step(action)
                reference.step(action)
                assert snapshot(duel) == snapshot(reference)
        duel.restore(checkpoint, preserve_rng=True)
        assert snapshot(duel) == root
        assert observation(saved) == saved_values
        with duel.clone(preserve_rng=True) as branch:
            assert snapshot(branch) == root


def test_multiple_checkpoints_and_owner_validation(duel: Duel) -> None:
    a = duel.checkpoint()
    initial = snapshot(duel)
    duel.step(choose(duel, Kind.SUMMON))
    b = duel.checkpoint()
    later = snapshot(duel)
    duel.restore(a, preserve_rng=True)
    assert snapshot(duel) == initial
    duel.restore(b, preserve_rng=True)
    assert snapshot(duel) == later
    with duel.clone(preserve_rng=True) as other:
        before = snapshot(other)
        with pytest.raises(ValueError, match="different"):
            other.restore(a)
        assert snapshot(other) == before


def test_partial_selection_and_checkpoint_after_restore(engine: Engine, deck: Deck) -> None:
    with engine.create_duel(Deck(main=(100000001,) * 40), deck, seed=123) as source:
        source.step(choose(source, Kind.ACTIVATE))
        for _ in range(16):
            if any(a.kind == Kind.SELECT_CARD for a in source.actions):
                break
            source.step(choose(source, Kind.PASS, Kind.NO, Kind.SELECT_ZONE))
        else:
            pytest.fail("effect did not reach card selection")
        source.step(choose(source, Kind.SELECT_CARD))
        assert len(source.pending_actions) == 1
        a = source.checkpoint()
        expected = snapshot(source)
        source.step(choose(source, Kind.SELECT_CARD))
        b = source.checkpoint()
        later = snapshot(source)
        for _ in range(8):
            source.restore(a, preserve_rng=True)
            assert snapshot(source) == expected
            c = source.checkpoint()
            source.restore(b, preserve_rng=True)
            assert snapshot(source) == later
            source.restore(c, preserve_rng=True)
            assert snapshot(source) == expected


def test_restore_after_termination(duel: Duel) -> None:
    a = duel.checkpoint()
    before = snapshot(duel)
    for _ in range(1000):
        if duel.terminated:
            break
        duel.step(choose(duel, Kind.END_PHASE, Kind.PASS, Kind.NO, Kind.SELECT_ZONE, Kind.CONFIRM, Kind.SELECT_CARD))
    assert duel.terminated
    assert duel.outcome is not None
    with pytest.raises(RuntimeError, match="terminated"):
        duel.checkpoint()
    duel.restore(a, preserve_rng=True)
    assert snapshot(duel) == before
    assert duel.outcome is None
    assert duel.rewards == (0.0, 0.0)


def test_restore_rng_modes(engine: Engine, deck: Deck) -> None:
    with suspend_random_effect(engine, deck) as source:
        checkpoint = source.checkpoint()
        with source.clone(preserve_rng=True) as reference:
            exact = resume_random_effect(reference)
        source.restore(checkpoint, preserve_rng=True)
        assert resume_random_effect(source) == exact
        results = []
        for seed in range(4):
            source.restore(checkpoint, seed=seed)
            expected = resume_random_effect(source)
            source.restore(checkpoint, seed=seed)
            assert resume_random_effect(source) == expected
            results.append(expected)
        assert len({r[0] for r in results}) > 1
        assert len({r[1] for r in results}) > 1
        assert len({r[2] for r in results}) == 1
        source.restore(checkpoint)
        resume_random_effect(source)


def test_checkpoint_survives_owner_close(engine: Engine, deck: Deck, duel: Duel) -> None:
    source = engine.create_duel(deck, deck, seed=123)
    checkpoint = source.checkpoint()
    source.close()
    with pytest.raises(RuntimeError, match="closed"):
        source.restore(checkpoint)
    with pytest.raises(RuntimeError, match="closed"):
        source.checkpoint()
    del source
    gc.collect()
    with pytest.raises(ValueError, match="different"):
        duel.restore(checkpoint)
    del checkpoint
    gc.collect()
    assert not duel.closed


@pytest.mark.parametrize("options,error", [
    ({"seed": -1}, ValueError),
    ({"seed": 2**64}, ValueError),
    ({"seed": True}, TypeError),
    ({"seed": 0.5}, TypeError),
    ({"preserve_rng": 1}, TypeError),
    ({"preserve_rng": True, "seed": 1}, ValueError),
])
def test_invalid_restore_options_do_not_mutate(duel: Duel, options, error) -> None:
    checkpoint = duel.checkpoint()
    before = snapshot(duel)
    with pytest.raises(error):
        duel.restore(checkpoint, **options)
    assert snapshot(duel) == before
