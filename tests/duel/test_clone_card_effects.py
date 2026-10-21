import pytest
from ygo_gym import Deck, Engine
from ygo_gym.action import ActionKind as Kind
from ygo_gym.protocol import IdleDecision

from .comparison import choose, duel as snapshot


@pytest.mark.parametrize("code", [55144522, 79571449, 22589918, 74519184],
                         ids=["pot-of-greed", "graceful-charity", "reload", "hand-destruction"])
def test_real_effect_matches_at_every_awaiting_boundary(engine: Engine, deck: Deck, code: int) -> None:
    with engine.create_duel(Deck(main=(code,) * 40), deck, seed=321) as source:
        source.step(choose(source, Kind.ACTIVATE))
        boundaries = 0
        for _ in range(48):
            if source.terminated or isinstance(source.decision, IdleDecision):
                break
            with source.clone(preserve_rng=True) as branch:
                assert snapshot(source) == snapshot(branch)
                index = choose(source, Kind.CONFIRM, Kind.SELECT_ZONE, Kind.SELECT_CARD,
                               Kind.PASS, Kind.NO, Kind.YES)
                source.step(index)
                branch.step(index)
                assert snapshot(source) == snapshot(branch)
                boundaries += 1
        else:
            pytest.fail("real card effect did not finish")
        assert boundaries > 0
        assert not source.terminated
        assert isinstance(source.decision, IdleDecision)


def test_nested_chain_survives_independent_continuation(engine: Engine) -> None:
    cards = Deck(main=(22589918,) * 40)
    with engine.create_duel(cards, cards, seed=321) as source:
        source.step(choose(source, Kind.ACTIVATE))
        for _ in range(16):
            if any(a.kind == Kind.ACTIVATE for a in source.actions):
                source.step(choose(source, Kind.ACTIVATE))
                break
            source.step(choose(source, Kind.SELECT_ZONE, Kind.PASS, Kind.NO))
        else:
            pytest.fail("Reload did not provide a chain response")
        max_links = 0
        for _ in range(48):
            max_links = max(max_links, len(source.state().chain))
            if isinstance(source.decision, IdleDecision):
                break
            with source.clone(preserve_rng=True) as branch:
                assert snapshot(source) == snapshot(branch)
                index = choose(source, Kind.SELECT_ZONE, Kind.PASS, Kind.NO, Kind.CONFIRM,
                               Kind.SELECT_CARD, Kind.YES)
                source.step(index)
                branch.step(index)
                assert snapshot(source) == snapshot(branch)
        else:
            pytest.fail("nested Reload chain did not finish")
        assert max_links >= 2
