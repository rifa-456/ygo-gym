#pragma once

#include <optional>
#include <vector>

#include "protocol/decisions/decision.h"

namespace ygo_gym::protocol {

[[nodiscard]] std::optional<Decision> decode_decision(const std::vector<std::uint8_t>& messages);
[[nodiscard]] bool contains_retry(const std::vector<std::uint8_t>& messages);

}
