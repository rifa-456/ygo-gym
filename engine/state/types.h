#pragma once

#include <cstdint>
#include <optional>

namespace ygo_gym::state {

constexpr std::uint32_t unknown_card = 0;
constexpr std::uint32_t invalid_index = 0xffffffffu;

enum class Player : std::uint8_t {
    player0 = 0,
    player1 = 1,
};

enum class Location : std::uint32_t {
    deck = 0x01,
    hand = 0x02,
    monster_zone = 0x04,
    spell_trap_zone = 0x08,
    graveyard = 0x10,
    banished = 0x20,
    extra_deck = 0x40,
    overlay = 0x80,
};

enum class Position : std::uint32_t {
    faceup_attack = 0x01,
    facedown_attack = 0x02,
    faceup_defense = 0x04,
    facedown_defense = 0x08,
};

enum class Phase : std::uint16_t {
    draw = 0x001,
    standby = 0x002,
    main1 = 0x004,
    battle_start = 0x008,
    battle_step = 0x010,
    damage = 0x020,
    damage_calculation = 0x040,
    battle = 0x080,
    main2 = 0x100,
    end = 0x200,
};

enum class RelationKind : std::uint8_t {
    equip,
    target,
    material,
    reason,
};

struct CardRecord {
    std::uint32_t code{};
    std::uint8_t owner{};
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    std::uint32_t position{};
    std::uint32_t properties_index{invalid_index};
    std::uint32_t monster_index{invalid_index};
    std::uint32_t pendulum_index{invalid_index};
    std::uint32_t link_index{invalid_index};
};

struct CardProperties {
    std::uint32_t alias{};
    std::uint32_t type{};
    std::uint32_t attribute{};
    std::uint64_t race{};
};

struct MonsterState {
    std::uint32_t level{};
    std::uint32_t rank{};
    std::int32_t attack{};
    std::int32_t defense{};
    std::int32_t base_attack{};
    std::int32_t base_defense{};
};

struct PendulumState {
    std::uint32_t left_scale{};
    std::uint32_t right_scale{};
};

struct LinkState {
    std::uint32_t rating{};
    std::uint32_t markers{};
};

struct ZoneCount {
    std::uint8_t player{};
    std::uint32_t location{};
    std::uint32_t count{};
};

struct CounterState {
    std::uint32_t card{};
    std::uint16_t type{};
    std::uint16_t count{};
};

struct RelationState {
    RelationKind kind{};
    std::uint32_t source{};
    std::uint32_t target{};
    std::uint32_t sequence{};
};

struct ChainState {
    std::uint32_t index{};
    std::uint32_t card{};
    std::uint8_t triggering_player{};
    std::uint8_t triggering_controller{};
    std::uint32_t triggering_location{};
    std::uint32_t triggering_sequence{};
    std::uint64_t description{};
    std::uint32_t target_begin{};
    std::uint32_t target_count{};
};

struct GlobalState {
    std::uint8_t turn_player{};
    std::optional<std::uint8_t> decision_player;
    std::int32_t turn_count{};
    std::uint16_t phase{};
    std::int32_t life_points[2]{};
};

}
