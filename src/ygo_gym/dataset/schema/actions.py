from .types import ZONE, integers, struct

ACTION_FIELDS = {
    "variant": "VARCHAR",
    "kind": "VARCHAR",
    **integers(
        "card", "client_mode", "value", "position", "index", "available", "count", "attribute", "code"
    ),
    "description": "UBIGINT",
    "number": "UBIGINT",
    "race": "UBIGINT",
    "direct": "BOOLEAN",
    "zone": ZONE,
    "choice": "VARCHAR",
}
ACTION = struct(ACTION_FIELDS)
ACTION_VARIANTS = {
    "SimpleAction": (),
    "CardAction": ("card",),
    "EffectAction": ("card", "description", "client_mode"),
    "AttackAction": ("card", "direct"),
    "TributeAction": ("card", "value"),
    "SumAction": ("card", "value"),
    "ZoneAction": ("zone",),
    "PositionAction": ("position",),
    "OptionAction": ("index", "description"),
    "CounterAction": ("card", "available", "count"),
    "RaceAction": ("race",),
    "AttributeAction": ("attribute",),
    "CardCodeAction": ("code",),
    "NumberAction": ("index", "number"),
    "RpsAction": ("choice",),
}
