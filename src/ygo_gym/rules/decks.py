from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..deck import Deck

EXTRA_TYPES = 0x40 | 0x2000 | 0x800000 | 0x4000000


@dataclass(frozen=True, slots=True)
class DeckRules:
    """Deck-size, card-pool and copy limits, independently configurable.

    Limits use canonical card IDs, counting aliases together across all zones.
    Pass limits from a chosen banlist explicitly; no current list is assumed.
    """

    main_size: tuple[int, int] = (40, 60)
    extra_size: tuple[int, int] = (0, 15)
    side_size: tuple[int, int] = (0, 15)
    copy_limit: int | None = 3
    limits: Mapping[int, int] = field(default_factory=dict)
    allowed_cards: frozenset[int] | None = None
    check_card_types: bool = True
    ritual_in_extra: bool = False

    def __post_init__(self):
        for name in ("main_size", "extra_size", "side_size"):
            size = tuple(getattr(self, name))
            if (
                len(size) != 2
                or any(type(v) is not int or v < 0 for v in size)
                or size[0] > size[1]
            ):
                raise ValueError(f"{name} must be a nonnegative (minimum, maximum)")
            object.__setattr__(self, name, size)
        if self.copy_limit is not None and (
            type(self.copy_limit) is not int or self.copy_limit < 0
        ):
            raise ValueError("copy_limit must be nonnegative or None")
        limits = dict(self.limits)
        if any(
            type(k) is not int or k <= 0 or type(v) is not int or v < 0
            for k, v in limits.items()
        ):
            raise ValueError("limits must map positive card IDs to nonnegative counts")
        object.__setattr__(self, "limits", MappingProxyType(limits))
        if self.allowed_cards is not None:
            cards = frozenset(self.allowed_cards)
            if any(type(v) is not int or v <= 0 for v in cards):
                raise ValueError("allowed_cards must contain positive card IDs")
            object.__setattr__(self, "allowed_cards", cards)
        if (
            type(self.check_card_types) is not bool
            or type(self.ritual_in_extra) is not bool
        ):
            raise TypeError("card-type options must be bool")

    @classmethod
    def unrestricted(cls):
        return cls((0, 65535), (0, 65535), (0, 65535), None, check_card_types=False)

    @classmethod
    def from_banlist(cls, path, name=None, **options):
        from .banlist import read_banlist

        limits, allowed = read_banlist(path, name)
        return cls(limits=limits, allowed_cards=allowed, **options)

    def validate(self, deck, cards):
        if not isinstance(deck, Deck):
            raise TypeError("submission must be a Deck")
        counts = Counter()
        for zone in ("main", "extra", "side"):
            values = getattr(deck, zone)
            low, high = getattr(self, zone + "_size")
            if not low <= len(values) <= high:
                raise ValueError(f"{zone} deck requires between {low} and {high} cards")
            for code in values:
                if code not in cards:
                    raise ValueError(f"unknown card: {code}")
                card = cards[code]
                canonical = card.alias or code
                if (
                    self.allowed_cards is not None
                    and code not in self.allowed_cards
                    and canonical not in self.allowed_cards
                ):
                    raise ValueError(f"card {code} is outside the allowed card pool")
                counts[canonical] += 1
                extra = bool(card.type & EXTRA_TYPES) or (
                    self.ritual_in_extra and bool(card.type & 0x80)
                )
                if self.check_card_types and (
                    card.type & (0x4000 | 0x8000000)
                    or (zone != "side" and extra != (zone == "extra"))
                ):
                    raise ValueError(f"card {code} cannot be placed in {zone}")
        for code, count in counts.items():
            limit = self.limits.get(code, self.copy_limit)
            if limit is not None and count > limit:
                raise ValueError(f"card {code} exceeds its copy limit of {limit}")

    def validate_side(self, original, submitted, cards):
        self.validate(submitted, cards)
        for zone in ("main", "extra", "side"):
            if len(getattr(original, zone)) != len(getattr(submitted, zone)):
                raise ValueError(f"side decking must preserve the {zone} deck size")

        def inventory(deck):
            return Counter(deck.main + deck.extra + deck.side)

        if inventory(original) != inventory(submitted):
            raise ValueError(
                "side decking must preserve the exact registered card inventory"
            )
