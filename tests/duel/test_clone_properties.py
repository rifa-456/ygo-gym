from hypothesis import example, given, settings, strategies as st
from ygo_gym import Deck, Engine

from .comparison import duel as snapshot


@given(
    seed=st.integers(min_value=0, max_value=2**64 - 1),
    choices=st.lists(st.integers(min_value=0, max_value=65535), min_size=1, max_size=12),
)
@example(seed=0, choices=[0] * 12)
@example(seed=2**64 - 1, choices=[65535] * 12)
@settings(max_examples=25, deadline=None)
def test_clone_matches_generated_legal_paths(engine: Engine, seed: int, choices: list[int]) -> None:
    deck = Deck(main=(69247929, 89631139, 46986414, 55144522) * 10)
    with engine.create_duel(deck, deck, seed) as source, source.clone(preserve_rng=True) as branch:
        assert snapshot(source) == snapshot(branch)
        for choice in choices:
            if source.terminated:
                break
            assert source.actions, "nonterminal duel has no legal actions"
            index = choice % len(source.actions)
            source.step(index)
            branch.step(index)
            assert snapshot(source) == snapshot(branch)
