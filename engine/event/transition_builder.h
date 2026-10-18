#pragma once

#include <unordered_map>
#include "reader.h"

namespace ygo_gym::event {

struct LocatorKey {
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    bool operator==(const LocatorKey& other) const noexcept {
        return controller == other.controller && location == other.location && sequence == other.sequence;
    }
};

struct LocatorHash {
    std::size_t operator()(const LocatorKey& value) const noexcept {
        std::size_t hash = value.controller;
        hash = hash * 1315423911u + value.location;
        hash = hash * 1315423911u + value.sequence;
        return hash;
    }
};

inline LocatorKey key(const Locator& value) {
    return LocatorKey{value.controller, value.location, value.sequence};
}

class TransitionBuilder {
public:
    void message(const std::uint8_t* data, std::size_t size);
    Transition finish() { return std::move(transition_); }

private:
    std::uint32_t card(std::uint32_t code, std::uint8_t visible_to, std::optional<Locator> current);
    std::uint32_t moved_card(std::uint32_t code, std::uint8_t visible_to, const Locator& previous, const Locator& current);
    void clear_zone(std::uint8_t player, std::uint32_t location);
    void win(Reader& reader);
    void confirm(Reader& reader, std::uint8_t type);
    void shuffle_simple(Reader& reader, std::uint32_t location);
    void shuffle_cards(Reader& reader, std::uint32_t location);
    void deck_top(Reader& reader);
    void move(Reader& reader);
    void position(Reader& reader);
    void set(Reader& reader);
    void summon(Reader& reader, SummonKind kind, SummonStage stage, bool public_code);
    void complete_summon(SummonKind kind);
    void chaining(Reader& reader);
    void chain_stage(Reader& reader, ChainStage stage);
    void draw(Reader& reader);
    void life(Reader& reader, LifePointKind kind);
    void life_set(Reader& reader);
    void counter(Reader& reader, int sign);
    void relation(Reader& reader, RelationEventKind kind_value);
    void attack(Reader& reader);
    void battle(Reader& reader);
    void random(Reader& reader, RandomKind kind_value);

    struct ChainMeta { std::uint32_t card{}; std::uint8_t player{}; std::uint64_t description{}; };
    Transition transition_;
    std::unordered_map<LocatorKey, std::uint32_t, LocatorHash> located_;
    std::unordered_map<std::uint32_t, ChainMeta> chain_;
    std::optional<std::pair<std::uint32_t, std::uint8_t>> latest_summon_[3];
};

}
