#pragma once

#include <cstdint>
#include <variant>

#include "protocol/decision.h"

namespace ygo_gym::action {

enum class ActionKind : std::uint8_t {
    summon,
    special_summon,
    reposition,
    set_monster,
    set_spell_trap,
    activate,
    attack,
    battle_phase,
    main_phase_2,
    end_phase,
    shuffle_hand,
    pass,
    yes,
    no,
    option,
    select_card,
    select_tribute,
    select_sum_card,
    unselect_card,
    order_card,
    select_zone,
    select_position,
    allocate_counter,
    select_race,
    select_attribute,
    announce_card,
    announce_number,
    rock_paper_scissors,
    confirm,
    cancel,
};

struct SimpleAction {
    ActionKind kind;
};

struct CardAction {
    ActionKind kind;
    protocol::CardRef card;
    std::uint32_t source_index;
};

struct EffectAction {
    ActionKind kind;
    protocol::EffectRef effect;
    std::uint32_t source_index;
};

struct AttackAction {
    ActionKind kind;
    protocol::AttackRef attack;
    std::uint32_t source_index;
};

struct TributeAction {
    ActionKind kind;
    protocol::TributeRef tribute;
    std::uint32_t source_index;
};

struct SumAction {
    ActionKind kind;
    protocol::SumRef sum;
    std::uint32_t source_index;
};

struct ZoneAction {
    ActionKind kind;
    protocol::ZoneRef zone;
};

struct PositionAction {
    ActionKind kind;
    std::uint8_t position;
};

struct OptionAction {
    ActionKind kind;
    std::uint32_t index;
    std::uint64_t description;
};

struct CounterAction {
    ActionKind kind;
    protocol::CounterRef counter;
    std::uint16_t count;
    std::uint32_t source_index;
};

struct RaceAction {
    ActionKind kind;
    std::uint64_t race;
};

struct AttributeAction {
    ActionKind kind;
    std::uint32_t attribute;
};

struct CardCodeAction {
    ActionKind kind;
    std::uint32_t code;
};

struct NumberAction {
    ActionKind kind;
    std::uint32_t index;
    std::uint64_t number;
};

struct RpsAction {
    ActionKind kind;
    protocol::RpsChoice choice;
};

using Action = std::variant<
    SimpleAction,
    CardAction,
    EffectAction,
    AttackAction,
    TributeAction,
    SumAction,
    ZoneAction,
    PositionAction,
    OptionAction,
    CounterAction,
    RaceAction,
    AttributeAction,
    CardCodeAction,
    NumberAction,
    RpsAction
>;

[[nodiscard]] ActionKind kind(const Action& action) noexcept;

}
