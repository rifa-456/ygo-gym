#include "commands.h"
#include "response_encoding.h"

namespace ygo_gym::protocol {

Response BattleDecision::response(BattleCommand command, std::uint32_t index) const {
    switch(command) {
    case BattleCommand::activate:
        check_index(index, activatable.size(), "activation");
        break;
    case BattleCommand::attack:
        check_index(index, attackable.size(), "attack");
        break;
    case BattleCommand::main_phase_2:
        if(!can_main_phase_2)
            throw std::invalid_argument("main phase 2 is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case BattleCommand::end_phase:
        if(!can_end_phase)
            throw std::invalid_argument("end phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    }
    const auto value = command_response_value(static_cast<std::uint16_t>(command), index);
    return scalar_response<std::int32_t>(DecisionKind::battle_command, static_cast<std::int32_t>(value));
}

Response IdleDecision::response(IdleCommand command, std::uint32_t index) const {
    switch(command) {
    case IdleCommand::summon:
        check_index(index, summonable.size(), "summon");
        break;
    case IdleCommand::special_summon:
        check_index(index, special_summonable.size(), "special summon");
        break;
    case IdleCommand::reposition:
        check_index(index, repositionable.size(), "reposition");
        break;
    case IdleCommand::set_monster:
        check_index(index, monster_settable.size(), "monster set");
        break;
    case IdleCommand::set_spell_trap:
        check_index(index, spell_trap_settable.size(), "spell/trap set");
        break;
    case IdleCommand::activate:
        check_index(index, activatable.size(), "activation");
        break;
    case IdleCommand::battle_phase:
        if(!can_battle_phase)
            throw std::invalid_argument("battle phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case IdleCommand::end_phase:
        if(!can_end_phase)
            throw std::invalid_argument("end phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case IdleCommand::shuffle_hand:
        if(!can_shuffle_hand)
            throw std::invalid_argument("hand shuffle is not available");
        if(index != 0)
            throw std::invalid_argument("shuffle hand does not take an index");
        break;
    }
    const auto value = command_response_value(static_cast<std::uint16_t>(command), index);
    return scalar_response<std::int32_t>(DecisionKind::idle_command, static_cast<std::int32_t>(value));
}

Response EffectYesNoDecision::response(bool yes) const {
    return scalar_response<std::int32_t>(DecisionKind::effect_yes_no, yes ? 1 : 0);
}

Response YesNoDecision::response(bool yes) const {
    return scalar_response<std::int32_t>(DecisionKind::yes_no, yes ? 1 : 0);
}

Response OptionDecision::response(std::uint32_t index) const {
    check_index(index, options.size(), "option");
    return scalar_response<std::int32_t>(DecisionKind::option, static_cast<std::int32_t>(index));
}

Response ChainDecision::response(std::uint32_t index) const {
    check_index(index, options.size(), "chain");
    return scalar_response<std::int32_t>(DecisionKind::chain, static_cast<std::int32_t>(index));
}

Response ChainDecision::pass_response() const {
    if(forced)
        throw std::invalid_argument("chain selection is forced");
    return cancel_response(DecisionKind::chain);
}

}
