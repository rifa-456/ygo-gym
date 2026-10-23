#pragma once

#include <array>
#include <cstdint>
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym {

struct DuelOptions {
    std::uint64_t flags{DUEL_MODE_MR5};
    std::array<std::uint32_t, 2> life_points{8000, 8000};
    std::array<std::uint32_t, 2> opening_hand{5, 5};
    std::array<std::uint32_t, 2> draw_count{1, 1};
    bool shuffle{true};
};

}
