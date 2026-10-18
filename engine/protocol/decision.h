#pragma once

#include "commands.h"
#include "selection.h"
#include "announcement.h"

namespace ygo_gym::protocol {

using Decision = std::variant<
    BattleDecision,
    IdleDecision,
    EffectYesNoDecision,
    YesNoDecision,
    OptionDecision,
    CardDecision,
    ChainDecision,
    PlaceDecision,
    PositionDecision,
    TributeDecision,
    CounterDecision,
    SumDecision,
    SortDecision,
    UnselectCardDecision,
    AnnounceRaceDecision,
    AnnounceAttributeDecision,
    AnnounceCardDecision,
    AnnounceNumberDecision,
    RockPaperScissorsDecision
>;

[[nodiscard]] DecisionKind kind(const Decision& decision) noexcept;
[[nodiscard]] std::uint8_t player(const Decision& decision) noexcept;

}
