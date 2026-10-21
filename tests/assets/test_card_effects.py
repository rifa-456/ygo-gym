import pytest

from ygo_gym import Deck, Engine
from ygo_gym.action import ActionKind
from ygo_gym.protocol import IdleDecision
from ygo_gym.state import Location


@pytest.mark.parametrize(
    "code, hand_delta, deck_delta, grave_delta, opponent_lp_delta",
    [(55144522, 1, -2, 1, 0), (70368879, 0, -1, 1, 1000), (79571449, 0, -3, 3, 0)],
    ids=["pot-of-greed", "upstart-goblin", "graceful-charity"],
)
def test_real_card_effect(pytestconfig, code, hand_delta, deck_delta, grave_delta, opponent_lp_delta):
    root = pytestconfig.rootpath / "third_party"
    scripts = root / "CardScripts"
    engine = Engine(root / "BabelCDB/cards.cdb", (scripts, scripts / "official"))
    with engine.create_duel(Deck(main=(code,) * 40), Deck(main=(69247929,) * 40), seed=123) as duel:
        player = int(duel.current_player)
        before = duel.state()
        counts = {location: len(before.zone(player, location))
                  for location in (Location.HAND, Location.DECK, Location.GRAVEYARD)}
        opponent_lp = before.global_state.life_points[1 - player]
        activation = next(i for i, action in enumerate(duel.actions) if action.kind == ActionKind.ACTIVATE)
        duel.step(activation)
        for _ in range(32):
            if isinstance(duel.decision, IdleDecision):
                break
            for kind in (ActionKind.CONFIRM, ActionKind.SELECT_ZONE, ActionKind.SELECT_CARD,
                         ActionKind.PASS, ActionKind.NO):
                index = next((i for i, action in enumerate(duel.actions) if action.kind == kind), None)
                if index is not None:
                    duel.step(index)
                    break
            else:
                pytest.fail("Unexpected prompt while resolving the card effect")
        else:
            pytest.fail("Card effect did not finish")
        after = duel.state()
        for location, delta in ((Location.HAND, hand_delta), (Location.DECK, deck_delta),
                                (Location.GRAVEYARD, grave_delta)):
            assert len(after.zone(player, location)) == counts[location] + delta
        assert after.global_state.life_points[1 - player] == opponent_lp + opponent_lp_delta
