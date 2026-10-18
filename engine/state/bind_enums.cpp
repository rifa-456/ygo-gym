#include "binding_types.h"

namespace ygo_gym::state {

void bind_enums(py::module_& module) {
    py::enum_<Player>(module, "Player")
        .value("PLAYER_0", Player::player0)
        .value("PLAYER_1", Player::player1);
    py::enum_<Location>(module, "Location", py::arithmetic())
        .value("DECK", Location::deck)
        .value("HAND", Location::hand)
        .value("MONSTER_ZONE", Location::monster_zone)
        .value("SPELL_TRAP_ZONE", Location::spell_trap_zone)
        .value("GRAVEYARD", Location::graveyard)
        .value("BANISHED", Location::banished)
        .value("EXTRA_DECK", Location::extra_deck)
        .value("OVERLAY", Location::overlay);
    py::enum_<Position>(module, "Position", py::arithmetic())
        .value("FACEUP_ATTACK", Position::faceup_attack)
        .value("FACEDOWN_ATTACK", Position::facedown_attack)
        .value("FACEUP_DEFENSE", Position::faceup_defense)
        .value("FACEDOWN_DEFENSE", Position::facedown_defense);
    py::enum_<Phase>(module, "Phase")
        .value("DRAW", Phase::draw)
        .value("STANDBY", Phase::standby)
        .value("MAIN1", Phase::main1)
        .value("BATTLE_START", Phase::battle_start)
        .value("BATTLE_STEP", Phase::battle_step)
        .value("DAMAGE", Phase::damage)
        .value("DAMAGE_CALCULATION", Phase::damage_calculation)
        .value("BATTLE", Phase::battle)
        .value("MAIN2", Phase::main2)
        .value("END", Phase::end);
    py::enum_<RelationKind>(module, "RelationKind")
        .value("EQUIP", RelationKind::equip)
        .value("TARGET", RelationKind::target)
        .value("MATERIAL", RelationKind::material)
        .value("REASON", RelationKind::reason);
}

}
