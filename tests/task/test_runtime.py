import pytest
from ygo_gym.task import Task, TaskDuel


def count_reward(transition, context):
    context.memory["n"] = context.memory.get("n", 0) + 1
    return context.memory["n"], -context.memory["n"]


def test_custom_task_runs_without_recording_and_clones_memory(engine, deck):
    with TaskDuel(engine.create_duel(deck, deck, seed=123), Task(reward=count_reward, max_steps=3)) as game:
        game.step(0)
        checkpoint = game.checkpoint()
        assert game.rewards == (1.0, -1.0)
        with game.clone(preserve_rng=True) as branch:
            branch.step(0)
            assert branch.rewards == (2.0, -2.0)
            assert game.rewards == (1.0, -1.0)
            game.step(0)
            assert game.rewards == branch.rewards
        game.step(0)
        assert game.truncated and not game.terminated
        assert not game.duel.terminated
        game.restore(checkpoint, preserve_rng=True)
        assert game.rewards == (1.0, -1.0)
        assert not game.ended
        assert game.step_count == 1
        game.step(0)
        assert game.rewards == (2.0, -2.0)


def test_task_checkpoint_rejects_wrong_owner(engine, deck):
    with TaskDuel(engine.create_duel(deck, deck, seed=123)) as first:
        checkpoint = first.checkpoint()
        with first.clone() as second:
            with pytest.raises(ValueError, match="different"):
                second.restore(checkpoint)
