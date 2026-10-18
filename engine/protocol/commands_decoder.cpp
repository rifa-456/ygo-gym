#include "decode_fields.h"

namespace ygo_gym::protocol {

BattleDecision read_battle(Reader& reader) {
    BattleDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.activatable = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, false);
    });
    decision.attackable = read_items<AttackRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        auto card = read_card(input, false, false);
        return AttackRef{std::move(card), input.read<std::uint8_t>() != 0};
    });
    decision.can_main_phase_2 = reader.read<std::uint8_t>() != 0;
    decision.can_end_phase = reader.read<std::uint8_t>() != 0;
    return decision;
}

IdleDecision read_idle(Reader& reader) {
    IdleDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    const auto normal_card = [](Reader& input) { return read_card(input, false); };
    decision.summonable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.special_summonable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.repositionable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_card(input, false, false);
    });
    decision.monster_settable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.spell_trap_settable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.activatable = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, false);
    });
    decision.can_battle_phase = reader.read<std::uint8_t>() != 0;
    decision.can_end_phase = reader.read<std::uint8_t>() != 0;
    decision.can_shuffle_hand = reader.read<std::uint8_t>() != 0;
    return decision;
}

ChainDecision read_chain(Reader& reader) {
    ChainDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.special_count = reader.read<std::uint8_t>();
    decision.forced = reader.read<std::uint8_t>() != 0;
    decision.hint_timing = reader.read<std::uint32_t>();
    decision.opponent_hint_timing = reader.read<std::uint32_t>();
    decision.options = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, true);
    });
    return decision;
}

}
