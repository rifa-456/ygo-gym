from dataclasses import dataclass, replace
from enum import IntFlag

from .. import _native

DuelRule = IntFlag("DuelRule", dict(_native.duel_flags), module=__name__)


@dataclass(frozen=True, slots=True)
class DuelConfig:
    """Core rules and initial values, indexed by the duel's engine seats.

    Main Deck tuples run from top to bottom when shuffle=False. Engine seat 0
    takes the first turn. Match remaps player-specific settings with its seats.
    """

    flags: int = DuelRule.MODE_MR5
    life_points: tuple[int, int] = (8000, 8000)
    opening_hand: tuple[int, int] = (5, 5)
    draw_count: tuple[int, int] = (1, 1)
    shuffle: bool = True

    def __post_init__(self):
        if isinstance(self.flags, bool) or not isinstance(self.flags, int):
            raise TypeError("flags must be an integer or DuelRule bitmask")
        if not 0 <= self.flags <= 0xFFFFFFFFFFFFFFFF:
            raise ValueError("flags must fit uint64")
        if self.flags & DuelRule.RELAY:
            raise ValueError("relay duels require more than two player sessions")
        for name in ("life_points", "opening_hand", "draw_count"):
            values = tuple(getattr(self, name))
            if len(values) != 2 or any(
                type(v) is not int or not 0 <= v <= 0x7FFFFFFF for v in values
            ):
                raise ValueError(f"{name} must contain two nonnegative int32 values")
            object.__setattr__(self, name, values)
        if type(self.shuffle) is not bool:
            raise TypeError("shuffle must be bool")

    def for_seats(self, players):
        return replace(
            self,
            **{
                name: tuple(getattr(self, name)[p] for p in players)
                for name in ("life_points", "opening_hand", "draw_count")
            },
        )

    def native(self):
        value = _native.DuelOptions()
        value.flags = int(self.flags)
        value.life_points = self.life_points
        value.opening_hand = self.opening_hand
        value.draw_count = self.draw_count
        value.shuffle = self.shuffle
        return value
