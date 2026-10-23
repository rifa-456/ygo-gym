#pragma once
#include "action/state.h"
#include "client/capture.h"

namespace ygo_gym::client {
[[nodiscard]] std::vector<std::uint32_t> plan(
    const state::Observation& observation,
    std::shared_ptr<const EngineState> engine, const Packet& response);
}
