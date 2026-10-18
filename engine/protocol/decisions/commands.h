#pragma once

#include "protocol/decisions/references.h"

namespace ygo_gym::protocol {

struct BattleDecision {
    std::uint8_t player;
    std::vector<EffectRef> activatable;
    std::vector<AttackRef> attackable;
    bool can_main_phase_2;
    bool can_end_phase;

    [[nodiscard]] Response response(BattleCommand command, std::uint32_t index = 0) const;
};

struct IdleDecision {
    std::uint8_t player;
    std::vector<CardRef> summonable;
    std::vector<CardRef> special_summonable;
    std::vector<CardRef> repositionable;
    std::vector<CardRef> monster_settable;
    std::vector<CardRef> spell_trap_settable;
    std::vector<EffectRef> activatable;
    bool can_battle_phase;
    bool can_end_phase;
    bool can_shuffle_hand;

    [[nodiscard]] Response response(IdleCommand command, std::uint32_t index = 0) const;
};

struct EffectYesNoDecision {
    std::uint8_t player;
    CardRef card;
    std::uint64_t description;

    [[nodiscard]] Response response(bool yes) const;
};

struct YesNoDecision {
    std::uint8_t player;
    std::uint64_t description;

    [[nodiscard]] Response response(bool yes) const;
};

struct OptionDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
};

struct ChainDecision {
    std::uint8_t player;
    std::uint8_t special_count;
    bool forced;
    std::uint32_t hint_timing;
    std::uint32_t opponent_hint_timing;
    std::vector<EffectRef> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
    [[nodiscard]] Response pass_response() const;
};

}
