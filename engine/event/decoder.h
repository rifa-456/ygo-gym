#pragma once

#include <cstdint>
#include <vector>

#include "event.h"

namespace ygo_gym::event {
[[nodiscard]] Transition decode(const std::vector<std::uint8_t>& messages);
}
