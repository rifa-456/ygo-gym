from ._native import (
    AnnounceAttributeDecision,
    AnnounceCardDecision,
    AnnounceNumberDecision,
    AnnounceRaceDecision,
    AttackRef,
    BattleCommand,
    BattleDecision,
    CardDecision,
    CardRef,
    ChainDecision,
    CoreResponse,
    CounterDecision,
    CounterRef,
    DecisionKind,
    EffectRef,
    EffectYesNoDecision,
    IdleCommand,
    IdleDecision,
    OptionDecision,
    PlaceDecision,
    PositionDecision,
    RockPaperScissorsDecision,
    RpsChoice,
    SortDecision,
    SumDecision,
    SumRef,
    TributeDecision,
    TributeRef,
    UnselectCardDecision,
    YesNoDecision,
    ZoneRef,
)

type Decision = (
    BattleDecision
    | IdleDecision
    | EffectYesNoDecision
    | YesNoDecision
    | OptionDecision
    | CardDecision
    | ChainDecision
    | PlaceDecision
    | PositionDecision
    | TributeDecision
    | CounterDecision
    | SumDecision
    | SortDecision
    | UnselectCardDecision
    | AnnounceRaceDecision
    | AnnounceAttributeDecision
    | AnnounceCardDecision
    | AnnounceNumberDecision
    | RockPaperScissorsDecision
)

__all__ = [
    "AnnounceAttributeDecision",
    "AnnounceCardDecision",
    "AnnounceNumberDecision",
    "AnnounceRaceDecision",
    "AttackRef",
    "BattleCommand",
    "BattleDecision",
    "CardDecision",
    "CardRef",
    "ChainDecision",
    "CoreResponse",
    "CounterDecision",
    "CounterRef",
    "Decision",
    "DecisionKind",
    "EffectRef",
    "EffectYesNoDecision",
    "IdleCommand",
    "IdleDecision",
    "OptionDecision",
    "PlaceDecision",
    "PositionDecision",
    "RockPaperScissorsDecision",
    "RpsChoice",
    "SortDecision",
    "SumDecision",
    "SumRef",
    "TributeDecision",
    "TributeRef",
    "UnselectCardDecision",
    "YesNoDecision",
    "ZoneRef",
]
