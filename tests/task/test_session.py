import pytest
from ygo_gym.task import Task, TaskSession, Transition


def transition(index=0, ended=False):
    return Transition(
        "game",
        index,
        0,
        {},
        0,
        {},
        {"engine_rewards": [1.0, -1.0] if ended else [0.0, 0.0], "engine_terminated": ended},
    )


def count_reward(value, context):
    context.memory["n"] = context.memory.get("n", 0) + 1
    return context.memory["n"], 0


def test_recurrent_session_state_can_be_saved_and_rebound():
    task = Task(reward=count_reward)
    a = TaskSession(task, "game")
    assert a.evaluate(transition()).rewards == (1.0, 0.0)
    b = TaskSession(task, "game")
    state = a.state_dict()
    b.load_state_dict(state)
    state["memory"]["n"] = 100
    assert a.evaluate(transition(1)) == b.evaluate(transition(1))
    assert b.context.memory["n"] == 2


def test_duel_end_takes_precedence_over_external_limits():
    session = TaskSession(Task(max_steps=1, truncation=lambda t, c: True), "game")
    result = session.evaluate(transition(ended=True))
    assert result.terminated and not result.truncated
    assert result.rewards == (1.0, -1.0) and result.reason == "duel_end"
    with pytest.raises(RuntimeError, match="ended"):
        session.evaluate(transition(1))


@pytest.mark.parametrize("value", [(1,), (float("nan"), 0), (0, float("inf")), (True, 0)])
def test_invalid_rewards_leave_evaluator_state_unchanged(value):
    def invalid(t, c):
        c.memory["changed"] = True
        return value

    session = TaskSession(Task(reward=invalid), "game")
    before = session.state_dict()
    with pytest.raises(ValueError):
        session.evaluate(transition())
    assert session.state_dict() == before


def test_function_contract_and_ordering():
    session = TaskSession(Task(termination=lambda t, c: 1), "game")
    with pytest.raises(TypeError, match="bool"):
        session.evaluate(transition())
    assert session.step_count == 0
    with pytest.raises(ValueError, match="order"):
        session.evaluate(transition(1))


@pytest.mark.parametrize("max_steps", [0, -1, True, 1.2])
def test_invalid_limits(max_steps):
    with pytest.raises(ValueError):
        Task(max_steps=max_steps)
