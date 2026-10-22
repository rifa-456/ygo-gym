from typing import TypedDict


class ResultRecord(TypedDict):
    rewards: list[float]
    terminated: bool
    truncated: bool
    reason: str | None


class FrameRecord(TypedDict):
    observations: list[dict]
    state: dict
    actions: list[dict]
    current_player: int | None
    decision_kind: str | None
    engine_terminated: bool
    engine_rewards: list[float]
    outcome: dict | None


class StepRecord(TypedDict):
    game_id: str
    step_index: int
    acting_player: int
    before: FrameRecord
    action_index: int
    action: dict
    after: FrameRecord
    result: ResultRecord
    recorded_result: ResultRecord
