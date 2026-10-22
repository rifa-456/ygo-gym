from collections.abc import Iterator

import pytest
from ygo_gym import Deck, Duel, Engine


@pytest.fixture
def duel(engine: Engine, deck: Deck) -> Iterator[Duel]:
    with engine.create_duel(deck, deck, seed=123) as value:
        yield value
