#pragma once
#include "action/expansion.h"
#include "client/capture.h"

namespace ygo_gym::client {
[[nodiscard]] std::vector<std::uint32_t> expand_response(const state::Observation& observation, const Packet& response);
}
