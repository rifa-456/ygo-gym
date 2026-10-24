from ygo_gym.episode import play
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
    from ygo_gym import Provenance
    from ygo_gym.dataset import Dataset, DatasetWriter

    provenance = Provenance.capture(engine)
    task = Task(reward=shaping, max_steps=4)
    path = tmp_path / "match.duckdb"
    with engine.create_duel(setup=quiet_setup()) as duel, TaskDuel(duel, task) as episode:
        result = play(episode, agents=(CollectingAgent(), CollectingAgent()))
        assert result.truncated and episode.truncated
        replay = duel.replay()
    writer = DatasetWriter(path, engine, task=task, snapshot_every=2, provenance=provenance)
    game_id = writer.write(replay)
    with Dataset.open(path) as dataset:
        assert dataset.game(game_id)["recording_status"] == "complete"
        assert dataset.validate_replay(engine, game_id, provenance=provenance).compatible
        assert list(dataset.steps(game_id))[-1]["result"]["truncated"]
        with dataset.restore(engine, game_id, 2, provenance=provenance) as restored:
            assert restored.actions


def test_external_match_budget_keeps_recording_partial(engine, tmp_path):
    from ygo_gym.dataset import Dataset, DatasetWriter

    with engine.create_duel(setup=quiet_setup()) as duel:
        result = play(duel, agents=(CollectingAgent(), CollectingAgent()), max_steps=2)
        assert result.truncated and result.reason == "step_limit"
        replay = duel.replay()
    path = tmp_path / "partial.duckdb"
    game_id = DatasetWriter(path, engine).write(replay)
    with Dataset.open(path) as dataset:
        assert dataset.game(game_id)["recording_status"] == "partial"
        assert not list(dataset.steps(game_id))[-1]["result"]["truncated"]
