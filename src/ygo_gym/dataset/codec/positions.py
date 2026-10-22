from ...state import Location
from ..schema import positions as schema
from .actions import action
from .events import batch
from .values import fields

LOCATIONS = (
    Location.DECK,
    Location.HAND,
    Location.MONSTER_ZONE,
    Location.SPELL_TRAP_ZONE,
    Location.GRAVEYARD,
    Location.BANISHED,
    Location.EXTRA_DECK,
)


def card(value) -> dict:
    result = fields(value, {k: v for k, v in schema.CARD_FIELDS.items() if not v.startswith("STRUCT")})
    for name, spec in (
        ("properties", schema.PROPERTY_FIELDS),
        ("monster", schema.MONSTER_FIELDS),
        ("pendulum", schema.PENDULUM_FIELDS),
        ("link", schema.LINK_FIELDS),
    ):
        result[name] = fields(getattr(value, name), spec)
    return result


def position(value) -> dict:
    chain = []
    for index, link in enumerate(value.chain):
        row = fields(link, {k: v for k, v in schema.CHAIN_FIELDS.items() if k != "targets"})
        row["targets"] = list(value.chain_targets(index))
        chain.append(row)
    return {
        "global_state": fields(value.global_state, schema.GLOBAL_FIELDS),
        "cards": [card(c) for c in value.cards],
        "counters": [fields(c, schema.COUNTER_FIELDS) for c in value.counters],
        "relations": [fields(r, schema.RELATION_FIELDS) for r in value.relations],
        "chain": chain,
        "pending_actions": [action(a) for a in value.pending_actions],
        "events": batch(value.events),
    }


def observation(value) -> dict:
    return {
        **position(value),
        "viewer": int(value.viewer),
        "zone_counts": [fields(z, schema.ZONE_COUNT_FIELDS) for z in value.zone_counts],
    }


def state(value) -> dict:
    return {
        **position(value),
        "duel_options": value.duel_options,
        "players": [fields(value.player(p), schema.PLAYER_FIELDS) for p in (0, 1)],
        "zones": [
            {"player": p, "location": int(loc), "cards": list(value.zone(p, loc))}
            for p in (0, 1)
            for loc in LOCATIONS
        ],
    }
