#pragma once

#include <cstdint>
#include <vector>

#include "engine.h"
#include "protocol/decisions/decision.h"

namespace ygo_gym::action {

[[nodiscard]] std::vector<protocol::ZoneRef> available_zones(
    const protocol::PlaceDecision& decision,
    const std::vector<protocol::ZoneRef>& selected
);

[[nodiscard]] bool tribute_complete(
    const protocol::TributeDecision& decision,
    const std::vector<std::uint32_t>& selected
);

[[nodiscard]] bool tribute_can_complete(
    const protocol::TributeDecision& decision,
    const std::vector<std::uint32_t>& selected
);

[[nodiscard]] bool sum_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
);

[[nodiscard]] bool sum_can_complete(
    const protocol::SumDecision& decision,
    const std::vector<std::uint32_t>& selected
);

[[nodiscard]] std::vector<std::uint32_t> declarable_cards(
    const EngineState& engine,
    const protocol::AnnounceCardDecision& decision
);

}
