from .actions import ACTION
from .events import BATCH
from .types import OUTCOME, integers, struct

GLOBAL_FIELDS = {
    **integers("turn_player", "decision_player", "turn_count", "phase"),
    "life_points": "BIGINT[]",
}
GLOBAL = struct(GLOBAL_FIELDS)
PROPERTY_FIELDS = {
    **integers("alias", "attribute"),
    "type": "UBIGINT",
    "race": "UBIGINT",
    "effects_disabled": "BOOLEAN",
    "summon_completed": "BOOLEAN",
}
MONSTER_FIELDS = integers(
    "level", "rank", "attack", "defense", "base_attack", "base_defense"
)
PENDULUM_FIELDS = integers("left_scale", "right_scale")
LINK_FIELDS = integers("rating", "markers")
CARD_FIELDS = {
    **integers("id", "code", "owner", "controller", "location", "sequence", "position"),
    "properties": struct(PROPERTY_FIELDS),
    "monster": struct(MONSTER_FIELDS),
    "pendulum": struct(PENDULUM_FIELDS),
    "link": struct(LINK_FIELDS),
}
CARD = struct(CARD_FIELDS)
COUNTER_FIELDS = integers("card", "type", "count")
RELATION_FIELDS = {"kind": "VARCHAR", **integers("source", "target", "sequence")}
CHAIN_FIELDS = {
    **integers(
        "index",
        "card",
        "triggering_player",
        "triggering_controller",
        "triggering_location",
        "triggering_sequence",
    ),
    "description": "UBIGINT",
    "targets": "BIGINT[]",
}
POSITION_FIELDS = {
    "global_state": GLOBAL,
    "cards": CARD + "[]",
    "counters": struct(COUNTER_FIELDS) + "[]",
    "relations": struct(RELATION_FIELDS) + "[]",
    "chain": struct(CHAIN_FIELDS) + "[]",
    "pending_actions": ACTION + "[]",
    "events": BATCH,
}
ZONE_COUNT_FIELDS = integers("player", "location", "count")
OBSERVATION = struct(
    {
        **POSITION_FIELDS,
        "viewer": "BIGINT",
        "zone_counts": struct(ZONE_COUNT_FIELDS) + "[]",
    }
)
PLAYER_FIELDS = integers(
    "life_points",
    "starting_life_points",
    "starting_hand_size",
    "draw_count",
    "used_locations",
    "disabled_locations",
    "faceup_extra_count",
)
ZONE_FIELDS = {**integers("player", "location"), "cards": "BIGINT[]"}
STATE = struct(
    {
        **POSITION_FIELDS,
        "duel_options": "UBIGINT",
        "players": struct(PLAYER_FIELDS) + "[]",
        "zones": struct(ZONE_FIELDS) + "[]",
    }
)
FRAME = struct(
    {
        "observations": OBSERVATION + "[]",
        "state": STATE,
        "actions": ACTION + "[]",
        "current_player": "BIGINT",
        "decision_kind": "VARCHAR",
        "engine_terminated": "BOOLEAN",
        "engine_rewards": "DOUBLE[]",
        "outcome": OUTCOME,
    }
)
