import gc

from ygo_gym import ActionKind, Deck
from ygo_gym.dataset.codec.actions import action as encode_action


def choose(duel, *kinds):
    return next(
        i
        for kind in kinds
        for i, action in enumerate(duel.actions)
        if action.kind == kind
    )


def test_saved_legal_actions_survive_steps_and_close(engine, deck):
    with engine.create_duel(deck, deck, seed=13) as duel:
        actions = duel.actions
        expected = [encode_action(action) for action in actions]
        for _ in range(20):
            duel.step(
                choose(
                    duel,
                    ActionKind.SET_MONSTER,
                    ActionKind.SELECT_ZONE,
                    ActionKind.END_PHASE,
                    ActionKind.PASS,
                )
            )
    gc.collect()
    assert [encode_action(action) for action in actions] == expected


def test_saved_pending_actions_survive_selection_changes_and_close(engine, deck):
    with engine.create_duel(Deck(main=(100000001,) * 40), deck, seed=123) as duel:
        duel.step(choose(duel, ActionKind.ACTIVATE))
        for _ in range(12):
            if any(action.kind == ActionKind.SELECT_CARD for action in duel.actions):
                break
            duel.step(
                choose(duel, ActionKind.SELECT_ZONE, ActionKind.PASS, ActionKind.NO)
            )
        duel.step(choose(duel, ActionKind.SELECT_CARD))
        actions = duel.pending_actions
        assert len(actions) == 1
        expected = [encode_action(action) for action in actions]
        duel.step(choose(duel, ActionKind.SELECT_CARD))
        duel.step(choose(duel, ActionKind.CONFIRM))
    gc.collect()
    assert [encode_action(action) for action in actions] == expected
