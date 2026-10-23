from dataclasses import dataclass, field
from enum import StrEnum

from ..rules import DeckRules, DuelConfig, DuelRule


class DrawPolicy(StrEnum):
    COUNT = "count"
    REPLAY = "replay"


@dataclass(frozen=True, slots=True)
class MatchRules:
    """Two-player series rules, with EDOPro-style counting by default.

    COUNT ends after best_of duels even if draws prevent a majority. REPLAY
    counts decisive duels only. max_duels optionally bounds either policy.
    first_player=None asks an initial chooser selected from the match seed.
    Thereafter the previous loser chooses; a draw retains the previous chooser.
    DuelConfig player values refer to stable match players, not engine seats.
    """

    best_of: int = 3
    side_decking: bool = True
    draw_policy: DrawPolicy = DrawPolicy.COUNT
    first_player: int | None = None
    initial_chooser: int | None = None
    max_duels: int | None = None
    max_steps_per_duel: int | None = None
    match_kill: bool = True
    duel: DuelConfig = field(default_factory=DuelConfig)
    decks: DeckRules = field(default_factory=DeckRules)

    def __post_init__(self):
        if type(self.best_of) is not int or self.best_of < 1:
            raise ValueError("best_of must be a positive integer")
        for name in ("max_duels", "max_steps_per_duel"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 1):
                raise ValueError(f"{name} must be a positive integer or None")
        for name in ("first_player", "initial_chooser"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value not in (0, 1)):
                raise ValueError(f"{name} must be 0, 1, or None")
        for name in ("side_decking", "match_kill"):
            if type(getattr(self, name)) is not bool:
                raise TypeError(f"{name} must be bool")
        object.__setattr__(self, "draw_policy", DrawPolicy(self.draw_policy))
        if not isinstance(self.duel, DuelConfig) or not isinstance(
            self.decks, DeckRules
        ):
            raise TypeError("duel and decks must be DuelConfig and DeckRules")
        if self.duel.flags & DuelRule.SIMPLE_AI:
            raise ValueError("matches require two independently controlled players")
        if self.decks.ritual_in_extra != bool(
            self.duel.flags & DuelRule.EXTRA_DECK_RITUAL
        ):
            raise ValueError(
                "deck placement and duel rules must agree on Ritual placement"
            )
