import pytest
from ygo_gym import Provenance
from ygo_gym.dataset import Dataset, DatasetWriter


@pytest.fixture(scope="session")
def provenance(engine):
    return Provenance.capture(engine)


@pytest.fixture
def replay(engine, deck):
    """A four-step game between vanilla decks."""
    with engine.create_duel(deck, deck, seed=123) as duel:
        for _ in range(4):
            duel.step(0)
        return duel.replay()


def recorded(engine, path, replay, provenance, **options):
    """Write one replay and return its game row and steps as read back from the file."""
    game_id = DatasetWriter(path, engine, provenance=provenance, **options).write(replay)
    with Dataset.open(path) as dataset:
        return dataset.game(game_id), list(dataset.steps(game_id))
