import pytest

from ygo_gym import (
    ActionKind,
    CardSetup,
    DuelSetup,
    Location,
    PlayerSetup,
    Puzzle,
    PuzzleDuel,
    play,
)
from ygo_gym.agents import RandomAgent
from ygo_gym.task import Task, TaskDuel


class EndTurn(RandomAgent):
    def act(self, decision):
        assert int(decision.observation.viewer) == 0
        for kind in (ActionKind.END_PHASE, ActionKind.PASS):
            for index, action in enumerate(decision.actions):
                if action.kind == kind:
                    return index
        return 0

    def end(self, episode):
        self.final = episode


def position():
    return DuelSetup(
        (PlayerSetup(), PlayerSetup()),
        cards=(CardSetup(69247929, 0, 0, Location.HAND, 0),),
    )


def test_default_puzzle_objective_is_enforced_with_one_solver(engine):
    with Puzzle("deadline", setup=position()).start(engine, seed=0) as episode:
        assert isinstance(episode, PuzzleDuel)
        agent = EndTurn()
        result = play(episode, agent=agent)
        assert result.terminated and result.returns == (-1.0, 1.0)
        assert result.player_steps[1] == 0
        assert agent.final.result == result
        assert int(episode.duel.outcome.winner) == 1
        assert episode.solved is False


def test_puzzle_rejects_a_second_agent(engine):
    with Puzzle("one-solver", setup=position()).start(engine, seed=0) as episode:
        with pytest.raises(ValueError, match="one solver"):
            play(episode, agents=(RandomAgent(), RandomAgent()))


def test_clones_checkpoints_and_task_snapshots_keep_puzzle_semantics(engine):
    puzzle = Puzzle("branching", setup=position())
    task = Task(max_steps=30)
    with puzzle.start(engine, seed=1, task=task) as episode:
        checkpoint = episode.checkpoint()
        with episode.clone(preserve_rng=True) as branch:
            assert isinstance(branch, PuzzleDuel) and branch.solver == 0
            assert play(branch, agent=EndTurn()).returns[0] == -1
        data = episode.serialize()
        with TaskDuel.deserialize(engine, data, task) as restored:
            assert isinstance(restored, PuzzleDuel)
            assert play(restored, agent=EndTurn()).returns[0] == -1
        episode.step(
            next(
                i
                for i, a in enumerate(episode.actions)
                if a.kind == ActionKind.END_PHASE
            )
        )
        episode.restore(checkpoint, preserve_rng=True)
        assert not episode.ended


def test_recorded_puzzle_uses_the_same_single_solver_contract(engine, tmp_path):
    pytest.importorskip("duckdb")
    from ygo_gym.dataset import Dataset, Recorder

    with Recorder.create(
        engine, puzzle=Puzzle("recorded", setup=position())
    ) as recorder:
        result = play(recorder, agent=EndTurn())
        assert result.terminated
        path = tmp_path / "puzzle.duckdb"
        recorder.save(path, snapshot_every=1)
        with Dataset.open(path) as dataset:
            assert dataset.validate_replay(engine, recorder.game_id).compatible
            with dataset.restore(
                engine, recorder.game_id, 0, task=recorder.task
            ) as restored:
                assert isinstance(restored, PuzzleDuel)
                assert play(restored, agent=EndTurn()).terminated
