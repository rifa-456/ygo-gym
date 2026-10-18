#pragma once

#include "protocol/decisions/references.h"

namespace ygo_gym::protocol {

struct CardDecision {
    std::uint8_t player;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<CardRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
    [[nodiscard]] Response cancel_response() const;
};

struct PlaceDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint32_t unavailable;
    bool disable_field;

    [[nodiscard]] Response response(const std::vector<ZoneRef>& zones) const;
};

struct PositionDecision {
    std::uint8_t player;
    std::uint32_t card_code;
    std::uint8_t positions;

    [[nodiscard]] Response response(std::uint8_t position) const;
};

struct TributeDecision {
    std::uint8_t player;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<TributeRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
    [[nodiscard]] Response cancel_response() const;
};

struct CounterDecision {
    std::uint8_t player;
    std::uint16_t counter_type;
    std::uint16_t count;
    std::vector<CounterRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint16_t>& counts) const;
};

struct SumDecision {
    std::uint8_t player;
    std::uint8_t mode;
    std::uint32_t target;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<SumRef> required;
    std::vector<SumRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
};

struct SortDecision {
    std::uint8_t player;
    bool chain;
    std::vector<CardRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint8_t>& order) const;
    [[nodiscard]] Response cancel_response() const;
};

struct UnselectCardDecision {
    std::uint8_t player;
    bool finishable;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<CardRef> selectable;
    std::vector<CardRef> unselectable;

    [[nodiscard]] Response response(std::uint32_t index) const;
    [[nodiscard]] Response finish_response() const;
};

}
