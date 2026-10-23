from ygo_gym import ActionKind, CardSetup, DuelSetup, Location, PlayerSetup
from ygo_gym.dataset.codec.actions import action as encode_action


class CollectingAgent:
    def __init__(self, choose=None):
        self.choose = choose
        self.resets = []
        self.decisions = []
        self.action_values = []
        self.final = None

    def reset(self, *, player, seed):
        self.resets.append((player, seed))
        self.decisions = []
        self.action_values = []
        self.final = None

    def act(self, decision):
        self.decisions.append(decision)
        self.action_values.append(
            [encode_action(action) for action in decision.actions]
        )
        if self.choose is not None:
            return self.choose(decision)
        priorities = (
            ActionKind.SET_MONSTER,
            ActionKind.SELECT_ZONE,
            ActionKind.END_PHASE,
            ActionKind.PASS,
        )
        return next(
            (
                i
                for kind in priorities
                for i, a in enumerate(decision.actions)
                if a.kind == kind
            ),
            0,
        )

    def end(self, episode):
        self.final = episode

    def updates(self):
        return [
            update for decision in self.decisions for update in decision.updates
        ] + list(self.final.updates)


def quiet_setup():
    return DuelSetup(
        players=(PlayerSetup(draw_count=0), PlayerSetup(draw_count=0)),
        cards=tuple(
            CardSetup(69247929, player, player, Location.HAND, 0) for player in (0, 1)
        ),
    )
