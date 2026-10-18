#pragma once

#include "references.h"

namespace ygo_gym::protocol {

struct AnnounceRaceDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint64_t available;

    [[nodiscard]] Response response(std::uint64_t races) const;
};

struct AnnounceAttributeDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint32_t available;

    [[nodiscard]] Response response(std::uint32_t attributes) const;
};

struct AnnounceCardDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> opcodes;

    [[nodiscard]] Response response(std::uint32_t code) const;
};

struct AnnounceNumberDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
};

struct RockPaperScissorsDecision {
    std::uint8_t player;

    [[nodiscard]] Response response(RpsChoice choice) const;
};

}
