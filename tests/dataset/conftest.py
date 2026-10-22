import pytest
from ygo_gym.dataset import Provenance, Recorder
from ygo_gym.task import Task


@pytest.fixture(scope="session")
def provenance(engine):
    return Provenance.capture(engine)


@pytest.fixture
def recorder(engine, deck, provenance):
    with Recorder.create(
        engine, deck, deck, seed=123, task=Task(max_steps=4), provenance=provenance
    ) as value:
        yield value


@pytest.fixture(autouse=True)
def dataset_dependencies():
    pytest.importorskip("duckdb")
