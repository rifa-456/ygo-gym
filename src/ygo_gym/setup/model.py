from dataclasses import dataclass

from ..state import Location, Player, Position


def integer(value, name, maximum, minimum=0):
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        raise ValueError(f"{name} must be an integer between {minimum} and {maximum}")


@dataclass(frozen=True, slots=True)
class PlayerSetup:
    life_points: int = 8000
    draw_count: int = 1

    def __post_init__(self):
        integer(self.life_points, "life_points", 0xFFFFFFFF)
        integer(self.draw_count, "draw_count", 0xFFFFFFFF)


@dataclass(frozen=True, slots=True)
class CardSetup:
    code: int
    owner: int
    controller: int
    location: Location
    sequence: int
    position: Position | None = None
    summon_complete: bool = False

    def __post_init__(self):
        integer(self.code, "code", 0xFFFFFFFF, 1)
        for name in ("owner", "controller"):
            value = getattr(self, name)
            if isinstance(value, Player):
                object.__setattr__(self, name, int(value))
        integer(self.owner, "owner", 1)
        integer(self.controller, "controller", 1)
        integer(self.sequence, "sequence", 0xFFFF)
        if not isinstance(self.location, Location) or self.location == Location.OVERLAY:
            raise ValueError(
                "location must be a supported zone; direct overlay placement is not supported"
            )
        if self.position is None:
            default = (
                Position.FACEUP_ATTACK
                if self.location in (Location.GRAVEYARD, Location.BANISHED)
                else Position.FACEDOWN_DEFENSE
            )
            object.__setattr__(self, "position", default)
        if not isinstance(self.position, Position):
            raise TypeError("position must be a Position")
        if type(self.summon_complete) is not bool:
            raise TypeError("summon_complete must be bool")
        limit = {Location.MONSTER_ZONE: 6, Location.SPELL_TRAP_ZONE: 7}.get(
            self.location
        )
        if limit is not None and self.sequence > limit:
            raise ValueError("sequence exceeds the zone slot range")


@dataclass(frozen=True, slots=True)
class DuelSetup:
    """A history-free MR5 position starting with player 0's first Main Phase.

    Ordered zones use contiguous sequences from zero, with the Main Deck top
    at the highest sequence. No opening hand is dealt and no deck is shuffled.
    The first Draw and Standby phases are skipped; later turns run normally.
    """

    players: tuple[PlayerSetup, PlayerSetup]
    cards: tuple[CardSetup, ...] = ()
    allow_first_turn_attack: bool = True

    def __post_init__(self):
        object.__setattr__(self, "players", tuple(self.players))
        object.__setattr__(self, "cards", tuple(self.cards))
        if len(self.players) != 2 or not all(
            isinstance(p, PlayerSetup) for p in self.players
        ):
            raise ValueError("players must contain two PlayerSetup values")
        if not all(isinstance(c, CardSetup) for c in self.cards):
            raise TypeError("cards must contain CardSetup values")
        if type(self.allow_first_turn_attack) is not bool:
            raise TypeError("allow_first_turn_attack must be bool")
        groups = {}
        for card in self.cards:
            key = card.controller, card.location
            sequences = groups.setdefault(key, set())
            if card.sequence in sequences:
                raise ValueError(f"duplicate slot or sequence: {key}, {card.sequence}")
            sequences.add(card.sequence)
        fixed = {Location.MONSTER_ZONE, Location.SPELL_TRAP_ZONE}
        for (_, location), sequences in groups.items():
            if location not in fixed and sequences != set(range(len(sequences))):
                raise ValueError("ordered zone sequences must be contiguous from zero")
        for left, right in ((5, 6), (6, 5)):
            if left in groups.get(
                (0, Location.MONSTER_ZONE), ()
            ) and right in groups.get((1, Location.MONSTER_ZONE), ()):
                raise ValueError(
                    "both players occupy the same shared Extra Monster Zone"
                )

    def to_lua(self) -> str:
        from .render import render

        return render(self)
