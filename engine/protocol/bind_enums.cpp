#include "binding_types.h"

namespace ygo_gym::protocol {

void bind_enums(py::module_& module) {
    py::enum_<DecisionKind>(module, "DecisionKind")
        .value("BATTLE_COMMAND", DecisionKind::battle_command)
        .value("IDLE_COMMAND", DecisionKind::idle_command)
        .value("EFFECT_YES_NO", DecisionKind::effect_yes_no)
        .value("YES_NO", DecisionKind::yes_no)
        .value("OPTION", DecisionKind::option)
        .value("CARD", DecisionKind::card)
        .value("CHAIN", DecisionKind::chain)
        .value("PLACE", DecisionKind::place)
        .value("POSITION", DecisionKind::position)
        .value("TRIBUTE", DecisionKind::tribute)
        .value("SORT_CHAIN", DecisionKind::sort_chain)
        .value("COUNTER", DecisionKind::counter)
        .value("SUM", DecisionKind::sum)
        .value("DISABLE_FIELD", DecisionKind::disable_field)
        .value("SORT_CARD", DecisionKind::sort_card)
        .value("UNSELECT_CARD", DecisionKind::unselect_card)
        .value("ROCK_PAPER_SCISSORS", DecisionKind::rock_paper_scissors)
        .value("ANNOUNCE_RACE", DecisionKind::announce_race)
        .value("ANNOUNCE_ATTRIBUTE", DecisionKind::announce_attribute)
        .value("ANNOUNCE_CARD", DecisionKind::announce_card)
        .value("ANNOUNCE_NUMBER", DecisionKind::announce_number);

    py::enum_<IdleCommand>(module, "IdleCommand")
        .value("SUMMON", IdleCommand::summon)
        .value("SPECIAL_SUMMON", IdleCommand::special_summon)
        .value("REPOSITION", IdleCommand::reposition)
        .value("SET_MONSTER", IdleCommand::set_monster)
        .value("SET_SPELL_TRAP", IdleCommand::set_spell_trap)
        .value("ACTIVATE", IdleCommand::activate)
        .value("BATTLE_PHASE", IdleCommand::battle_phase)
        .value("END_PHASE", IdleCommand::end_phase)
        .value("SHUFFLE_HAND", IdleCommand::shuffle_hand);

    py::enum_<BattleCommand>(module, "BattleCommand")
        .value("ACTIVATE", BattleCommand::activate)
        .value("ATTACK", BattleCommand::attack)
        .value("MAIN_PHASE_2", BattleCommand::main_phase_2)
        .value("END_PHASE", BattleCommand::end_phase);

    py::enum_<RpsChoice>(module, "RpsChoice")
        .value("ROCK", RpsChoice::rock)
        .value("PAPER", RpsChoice::paper)
        .value("SCISSORS", RpsChoice::scissors);
}

}
