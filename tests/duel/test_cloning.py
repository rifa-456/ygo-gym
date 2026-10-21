import gc

import pytest
from ygo_gym import Deck, Duel, Engine
from ygo_gym.action import ActionKind as Kind
from ygo_gym.event import RandomEvent
from ygo_gym.state import Location, UNKNOWN_CARD

from .comparison import choose, duel as snapshot, observation


@pytest.mark.parametrize("seed", [0, 123, 2**64 - 1])
def test_same_actions_and_source_destruction(engine: Engine, deck: Deck, seed: int) -> None:
    with engine.create_duel(deck, deck, seed) as source, source.clone(preserve_rng=True) as branch:
        saved = source.observation
        saved_values = observation(saved)
        assert snapshot(source) == snapshot(branch)
        for _ in range(16):
            if source.terminated:
                break
            index = choose(source, Kind.SUMMON, Kind.SELECT_ZONE, Kind.PASS, Kind.END_PHASE)
            source.step(index)
            branch.step(index)
            assert snapshot(source) == snapshot(branch)
        with branch.clone(preserve_rng=True) as descendant:
            expected = snapshot(branch)
            source.close()
            branch.close()
            gc.collect()
            assert observation(saved) == saved_values
            assert snapshot(descendant) == expected
            descendant.step(choose(descendant, Kind.PASS, Kind.END_PHASE, Kind.SELECT_ZONE, Kind.SUMMON))
            assert not descendant.closed


def test_different_actions_do_not_mutate_source(duel: Duel) -> None:
    before = snapshot(duel)
    with duel.clone(preserve_rng=True) as branch:
        assert snapshot(branch) == before
        branch.step(choose(branch, Kind.SET_MONSTER))
        branch.step(choose(branch, Kind.SELECT_ZONE))
        assert snapshot(duel) == before
        own, other = branch.observe(0), branch.observe(1)
        assert any(c.location == Location.MONSTER_ZONE and c.code for c in own.cards)
        assert all(c.code == UNKNOWN_CARD for c in other.cards if c.location == Location.MONSTER_ZONE)
    duel.step(choose(duel, Kind.END_PHASE))
    assert not duel.closed


def test_partial_selection_and_suspended_random_effect(engine: Engine, deck: Deck) -> None:
    scripted_deck = Deck(main=(100000001,) * 40)
    with engine.create_duel(scripted_deck, deck, seed=123) as source:
        source.step(choose(source, Kind.ACTIVATE))
        for _ in range(12):
            if any(a.kind == Kind.SELECT_CARD for a in source.actions):
                break
            source.step(choose(source, Kind.PASS, Kind.NO, Kind.SELECT_ZONE))
        else:
            pytest.fail("scripted effect did not reach card selection")
        source.step(choose(source, Kind.SELECT_CARD))
        assert len(source.pending_actions) == 1
        assert len(source.observation.events) == 0
        with source.clone(preserve_rng=True) as branch:
            assert snapshot(source) == snapshot(branch)
            source.step(choose(source, Kind.SELECT_CARD))
            branch.step(choose(branch, Kind.SELECT_CARD))
            assert snapshot(source) == snapshot(branch)
            with branch.clone(preserve_rng=True) as descendant:
                before = snapshot(source)
                branch.close()
                gc.collect()
                assert snapshot(descendant) == before
                for _ in range(12):
                    index = choose(source, Kind.CONFIRM, Kind.YES, Kind.PASS, Kind.SELECT_ZONE, Kind.END_PHASE)
                    source.step(index)
                    descendant.step(index)
                    assert snapshot(source) == snapshot(descendant)
                    if any(isinstance(e, RandomEvent) for e in source.observation.events):
                        break
                else:
                    pytest.fail("suspended effect never emitted its dice result")


def test_branch_keeps_assets_after_source_and_engine_are_deleted(engine: Engine, deck: Deck) -> None:
    separate_engine = Engine(engine.card_database, engine.script_roots)
    source = separate_engine.create_duel(deck, deck, seed=321)
    try:
        branch = source.clone(preserve_rng=True)
    finally:
        source.close()
    del source, separate_engine
    gc.collect()
    with branch:
        for _ in range(8):
            branch.step(choose(branch, Kind.SUMMON, Kind.SELECT_ZONE, Kind.PASS, Kind.END_PHASE))
            assert len(branch.state().cards) == 80


def test_closed_duel_rejects_clone(duel: Duel) -> None:
    duel.close()
    with pytest.raises(RuntimeError, match="closed"):
        duel.clone(preserve_rng=True)


def test_terminal_duel_rejects_clone(engine: Engine, deck: Deck) -> None:
    with engine.create_duel(Deck(main=(69247929,)), deck, seed=123) as terminal:
        assert terminal.terminated
        with pytest.raises(RuntimeError, match="terminated"):
            terminal.clone(preserve_rng=True)
