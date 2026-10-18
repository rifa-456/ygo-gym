from ._native import (
    AttackEvent,
    BattleEvent,
    ChainEvent,
    ChainStage,
    CounterEvent,
    DamageStepEvent,
    DamageStepStage,
    DeckReverseEvent,
    DrawEvent,
    EventBatch,
    EventCard,
    EventCardCollection,
    EventLocation,
    GraveDeckSwapEvent,
    LifePointEvent,
    LifePointKind,
    MoveEvent,
    PhaseEvent,
    PositionEvent,
    RandomEvent,
    RandomKind,
    RelationEvent,
    RelationEventKind,
    RevealEvent,
    SetEvent,
    ShuffleEvent,
    SummonEvent,
    SummonKind,
    SummonStage,
    TurnEvent,
    WinEvent,
)

type Event = (
    TurnEvent
    | PhaseEvent
    | ShuffleEvent
    | RevealEvent
    | DrawEvent
    | MoveEvent
    | PositionEvent
    | SetEvent
    | SummonEvent
    | ChainEvent
    | LifePointEvent
    | CounterEvent
    | RelationEvent
    | AttackEvent
    | BattleEvent
    | RandomEvent
    | DamageStepEvent
    | GraveDeckSwapEvent
    | DeckReverseEvent
    | WinEvent
)

__all__ = [
    "AttackEvent",
    "BattleEvent",
    "ChainEvent",
    "ChainStage",
    "CounterEvent",
    "DamageStepEvent",
    "DamageStepStage",
    "DeckReverseEvent",
    "DrawEvent",
    "Event",
    "EventBatch",
    "EventCard",
    "EventCardCollection",
    "EventLocation",
    "GraveDeckSwapEvent",
    "LifePointEvent",
    "LifePointKind",
    "MoveEvent",
    "PhaseEvent",
    "PositionEvent",
    "RandomEvent",
    "RandomKind",
    "RelationEvent",
    "RelationEventKind",
    "RevealEvent",
    "SetEvent",
    "ShuffleEvent",
    "SummonEvent",
    "SummonKind",
    "SummonStage",
    "TurnEvent",
    "WinEvent",
]
