from ._native import (
    ActionKind,
    AttackAction,
    AttributeAction,
    CardAction,
    CardCodeAction,
    CounterAction,
    EffectAction,
    NumberAction,
    OptionAction,
    PositionAction,
    RaceAction,
    RpsAction,
    SimpleAction,
    SumAction,
    TributeAction,
    ZoneAction,
)

type Action = (
    SimpleAction
    | CardAction
    | EffectAction
    | AttackAction
    | TributeAction
    | SumAction
    | ZoneAction
    | PositionAction
    | OptionAction
    | CounterAction
    | RaceAction
    | AttributeAction
    | CardCodeAction
    | NumberAction
    | RpsAction
)

__all__ = [
    "Action",
    "ActionKind",
    "AttackAction",
    "AttributeAction",
    "CardAction",
    "CardCodeAction",
    "CounterAction",
    "EffectAction",
    "NumberAction",
    "OptionAction",
    "PositionAction",
    "RaceAction",
    "RpsAction",
    "SimpleAction",
    "SumAction",
    "TributeAction",
    "ZoneAction",
]
