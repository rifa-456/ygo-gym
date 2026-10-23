import pytest

from ygo_gym.match import play

from .support import CollectingAgent, quiet_setup


@pytest.mark.parametrize(
    "action, error",
    [(True, TypeError), (1.5, TypeError), (-1, IndexError), (99999, IndexError)],
)
def test_invalid_agent_action_does_not_advance_duel(engine, action, error):
    from ygo_gym.dataset.codec import capture

    agents = CollectingAgent(lambda _: action), CollectingAgent()
    with engine.create_duel(setup=quiet_setup()) as duel:
        before = capture(duel)
        with pytest.raises(error, match="player 0"):
            play(duel, agents=agents)
        assert capture(duel) == before
        assert agents[0].final is agents[1].final is None


def test_separate_sessions_and_complete_lifecycle_are_required(engine):
    agent = CollectingAgent()
    with engine.create_duel(setup=quiet_setup()) as duel:
        with pytest.raises(ValueError, match="separate"):
            play(duel, agents=(agent, agent))
        with pytest.raises(TypeError, match="reset"):
            play(duel, agents=(object(), agent))
        for limit in (0, -1, True):
            with pytest.raises(ValueError, match="max_steps"):
                play(duel, agents=(agent, CollectingAgent()), max_steps=limit)
        assert not agent.resets


def test_second_agent_receives_terminal_delivery_if_first_end_callback_fails(engine):
    class BrokenEnd(CollectingAgent):
        def end(self, episode):
            raise RuntimeError("callback failed")

    other = CollectingAgent()
    with engine.create_duel(setup=quiet_setup()) as duel:
        with pytest.raises(ExceptionGroup, match="end callbacks") as errors:
            play(duel, agents=(BrokenEnd(), other), max_steps=1)
        assert str(errors.value.exceptions[0]) == "callback failed"
        assert other.final is not None
        assert not duel.closed


def test_already_terminal_position_delivers_initial_updates_without_actions(engine):
    from ygo_gym import ActionKind, Puzzle

    with Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua").start(
        engine, seed=42
    ) as episode:
        while not episode.ended:
            episode.step(
                next(
                    i
                    for kind in (ActionKind.END_PHASE, ActionKind.PASS)
                    for i, a in enumerate(episode.actions)
                    if a.kind == kind
                )
            )
        agents = CollectingAgent(), CollectingAgent()
        result = play(episode, agents=agents)
        assert result.step_count == 0 and result.terminated
        assert result.returns == (-1.0, 1.0)
        for agent in agents:
            assert not agent.decisions
            assert len(agent.final.updates) == 1


def test_closed_duel_is_rejected_before_reset(engine):
    duel = engine.create_duel(setup=quiet_setup())
    duel.close()
    agents = CollectingAgent(), CollectingAgent()
    with pytest.raises(RuntimeError, match="closed"):
        play(duel, agents=agents)
    assert all(not a.resets for a in agents)
