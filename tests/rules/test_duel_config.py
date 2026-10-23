import pytest

from ygo_gym import Deck, DuelConfig, DuelRule
from ygo_gym.state import Location


@pytest.mark.parametrize(
    "flags",
    [DuelRule.MODE_MR1, DuelRule.MODE_MR3, DuelRule.MODE_MR5, DuelRule.MODE_SPEED],
)
def test_rules_and_initial_values_reach_the_core(engine, flags):
    config = DuelConfig(
        flags=flags, life_points=(4567, 6789), opening_hand=(2, 3), draw_count=(0, 0)
    )
    with engine.create_duel(
        Deck((69247929,) * 10), Deck((69247929,) * 10), config=config
    ) as duel:
        state = duel.state()
        assert state.duel_options == int(flags)
        assert state.player(0).life_points == 4567
        assert state.player(1).starting_hand_size == 3
        assert state.player(0).draw_count == 0
        assert (
            sum(
                c.location == Location.HAND and int(c.controller) == 0
                for c in state.cards
            )
            == 2
        )


def test_unshuffled_order_is_top_to_bottom(engine):
    cards = (69247929, 89631139, 46986414, 53129443, 12580477, 44095762)
    config = DuelConfig(shuffle=False, opening_hand=(2, 0), draw_count=(0, 0))
    with engine.create_duel(Deck(cards), Deck(cards), config=config) as duel:
        hand = [
            c.code
            for c in duel.state().cards
            if c.location == Location.HAND and int(c.controller) == 0
        ]
        assert hand == list(cards[:2])


@pytest.mark.parametrize(
    "options",
    [
        {"flags": True},
        {"opening_hand": (-1, 0)},
        {"life_points": (True, 8000)},
        {"draw_count": (1,)},
        {"shuffle": 1},
        {"flags": DuelRule.RELAY},
    ],
)
def test_invalid_config(options):
    with pytest.raises((ValueError, TypeError)):
        DuelConfig(**options)
