import pytest

from ygo_gym.match import play
from ygo_gym.task import Task, TaskDuel

from .support import CollectingAgent, quiet_setup


def shaping(transition, context):
    return 1.0, -0.5


def test_task_rewards_are_accumulated_and_delivered_once(engine):
    with (
        engine.create_duel(setup=quiet_setup()) as duel,
        TaskDuel(duel, Task(reward=shaping, max_steps=7)) as episode,
    ):
        agents = CollectingAgent(), CollectingAgent()
        result = play(episode, agents=agents)
        assert result.truncated and episode.truncated
        assert result.step_count == 7
        assert result.returns == (7.0, -3.5)
        for seat, agent in enumerate(agents):
            delivered = (
                sum(decision.reward for decision in agent.decisions)
                + agent.final.reward
            )
            assert delivered == result.returns[seat]


def test_recorded_task_limit_survives_save_replay_and_restore(engine, tmp_path):
    pytest.importorskip("duckdb")
    from ygo_gym.dataset import Dataset, Provenance, Recorder

    provenance = Provenance.capture(engine)
    agents = CollectingAgent(), CollectingAgent()
    path = tmp_path / "match.duckdb"
    with Recorder.create(
        engine,
        setup=quiet_setup(),
        task=Task(reward=shaping, max_steps=4),
        provenance=provenance,
    ) as recorder:
        result = play(recorder, agents=agents)
        assert result.truncated and recorder.truncated
        assert recorder.game()["recording_status"] == "complete"
        recorder.save(path, snapshot_every=2)
        with Dataset.open(path) as dataset:
            assert dataset.validate_replay(
                engine, recorder.game_id, provenance=provenance
            ).compatible
            assert list(dataset.steps(recorder.game_id))[-1]["result"]["truncated"]
            with dataset.restore(
                engine, recorder.game_id, 2, provenance=provenance
            ) as restored:
                assert restored.actions


def test_external_match_budget_keeps_recording_partial(engine):
    from ygo_gym.dataset import Recorder

    with Recorder.create(engine, setup=quiet_setup()) as recorder:
        result = play(
            recorder, agents=(CollectingAgent(), CollectingAgent()), max_steps=2
        )
        assert result.truncated and result.reason == "step_limit"
        assert not recorder.ended
        assert recorder.game()["recording_status"] == "partial"
        assert not list(recorder.steps())[-1]["result"]["truncated"]
