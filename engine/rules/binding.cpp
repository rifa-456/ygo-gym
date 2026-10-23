#include "rules/binding.h"
#include "duel/options.h"
#include <pybind11/stl.h>
namespace py = pybind11;
namespace ygo_gym::rules {
void bind(py::module_& module) {
    py::dict flags;
    flags["TEST_MODE"] = py::int_(static_cast<std::uint64_t>(DUEL_TEST_MODE));
    flags["ATTACK_FIRST_TURN"] = py::int_(static_cast<std::uint64_t>(DUEL_ATTACK_FIRST_TURN));
    flags["USE_TRAPS_IN_NEW_CHAIN"] = py::int_(static_cast<std::uint64_t>(DUEL_USE_TRAPS_IN_NEW_CHAIN));
    flags["6_STEP_BATLLE_STEP"] = py::int_(static_cast<std::uint64_t>(DUEL_6_STEP_BATLLE_STEP));
    flags["PSEUDO_SHUFFLE"] = py::int_(static_cast<std::uint64_t>(DUEL_PSEUDO_SHUFFLE));
    flags["TRIGGER_WHEN_PRIVATE_KNOWLEDGE"] = py::int_(static_cast<std::uint64_t>(DUEL_TRIGGER_WHEN_PRIVATE_KNOWLEDGE));
    flags["SIMPLE_AI"] = py::int_(static_cast<std::uint64_t>(DUEL_SIMPLE_AI));
    flags["RELAY"] = py::int_(static_cast<std::uint64_t>(DUEL_RELAY));
    flags["OCG_OBSOLETE_IGNITION"] = py::int_(static_cast<std::uint64_t>(DUEL_OCG_OBSOLETE_IGNITION));
    flags["1ST_TURN_DRAW"] = py::int_(static_cast<std::uint64_t>(DUEL_1ST_TURN_DRAW));
    flags["1_FACEUP_FIELD"] = py::int_(static_cast<std::uint64_t>(DUEL_1_FACEUP_FIELD));
    flags["PZONE"] = py::int_(static_cast<std::uint64_t>(DUEL_PZONE));
    flags["SEPARATE_PZONE"] = py::int_(static_cast<std::uint64_t>(DUEL_SEPARATE_PZONE));
    flags["EMZONE"] = py::int_(static_cast<std::uint64_t>(DUEL_EMZONE));
    flags["FSX_MMZONE"] = py::int_(static_cast<std::uint64_t>(DUEL_FSX_MMZONE));
    flags["TRAP_MONSTERS_NOT_USE_ZONE"] = py::int_(static_cast<std::uint64_t>(DUEL_TRAP_MONSTERS_NOT_USE_ZONE));
    flags["RETURN_TO_DECK_TRIGGERS"] = py::int_(static_cast<std::uint64_t>(DUEL_RETURN_TO_DECK_TRIGGERS));
    flags["TRIGGER_ONLY_IN_LOCATION"] = py::int_(static_cast<std::uint64_t>(DUEL_TRIGGER_ONLY_IN_LOCATION));
    flags["SPSUMMON_ONCE_OLD_NEGATE"] = py::int_(static_cast<std::uint64_t>(DUEL_SPSUMMON_ONCE_OLD_NEGATE));
    flags["CANNOT_SUMMON_OATH_OLD"] = py::int_(static_cast<std::uint64_t>(DUEL_CANNOT_SUMMON_OATH_OLD));
    flags["NO_STANDBY_PHASE"] = py::int_(static_cast<std::uint64_t>(DUEL_NO_STANDBY_PHASE));
    flags["NO_MAIN_PHASE_2"] = py::int_(static_cast<std::uint64_t>(DUEL_NO_MAIN_PHASE_2));
    flags["3_COLUMNS_FIELD"] = py::int_(static_cast<std::uint64_t>(DUEL_3_COLUMNS_FIELD));
    flags["DRAW_UNTIL_5"] = py::int_(static_cast<std::uint64_t>(DUEL_DRAW_UNTIL_5));
    flags["NO_HAND_LIMIT"] = py::int_(static_cast<std::uint64_t>(DUEL_NO_HAND_LIMIT));
    flags["UNLIMITED_SUMMONS"] = py::int_(static_cast<std::uint64_t>(DUEL_UNLIMITED_SUMMONS));
    flags["INVERTED_QUICK_PRIORITY"] = py::int_(static_cast<std::uint64_t>(DUEL_INVERTED_QUICK_PRIORITY));
    flags["EQUIP_NOT_SENT_IF_MISSING_TARGET"] = py::int_(static_cast<std::uint64_t>(DUEL_EQUIP_NOT_SENT_IF_MISSING_TARGET));
    flags["0_ATK_DESTROYED"] = py::int_(static_cast<std::uint64_t>(DUEL_0_ATK_DESTROYED));
    flags["STORE_ATTACK_REPLAYS"] = py::int_(static_cast<std::uint64_t>(DUEL_STORE_ATTACK_REPLAYS));
    flags["SINGLE_CHAIN_IN_DAMAGE_SUBSTEP"] = py::int_(static_cast<std::uint64_t>(DUEL_SINGLE_CHAIN_IN_DAMAGE_SUBSTEP));
    flags["CAN_REPOS_IF_NON_SUMPLAYER"] = py::int_(static_cast<std::uint64_t>(DUEL_CAN_REPOS_IF_NON_SUMPLAYER));
    flags["TCG_SEGOC_NONPUBLIC"] = py::int_(static_cast<std::uint64_t>(DUEL_TCG_SEGOC_NONPUBLIC));
    flags["TCG_SEGOC_FIRSTTRIGGER"] = py::int_(static_cast<std::uint64_t>(DUEL_TCG_SEGOC_FIRSTTRIGGER));
    flags["TCG_FAST_EFFECT_IGNITION"] = py::int_(static_cast<std::uint64_t>(DUEL_TCG_FAST_EFFECT_IGNITION));
    flags["EXTRA_DECK_RITUAL"] = py::int_(static_cast<std::uint64_t>(DUEL_EXTRA_DECK_RITUAL));
    flags["NORMAL_SUMMON_FACEUP_DEF"] = py::int_(static_cast<std::uint64_t>(DUEL_NORMAL_SUMMON_FACEUP_DEF));
    flags["MODE_SPEED"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_SPEED));
    flags["MODE_RUSH"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_RUSH));
    flags["MODE_MR1"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_MR1));
    flags["MODE_GOAT"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_GOAT));
    flags["MODE_MR2"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_MR2));
    flags["MODE_MR3"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_MR3));
    flags["MODE_MR4"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_MR4));
    flags["MODE_MR5"] = py::int_(static_cast<std::uint64_t>(DUEL_MODE_MR5));
    module.attr("duel_flags") = flags;
    py::class_<DuelOptions>(module, "DuelOptions")
        .def(py::init<>())
        .def_readwrite("flags", &DuelOptions::flags)
        .def_readwrite("life_points", &DuelOptions::life_points)
        .def_readwrite("opening_hand", &DuelOptions::opening_hand)
        .def_readwrite("draw_count", &DuelOptions::draw_count)
        .def_readwrite("shuffle", &DuelOptions::shuffle);
}
}
