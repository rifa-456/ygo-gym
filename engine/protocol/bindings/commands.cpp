#include "protocol/bindings/types.h"

namespace ygo_gym::protocol {

void bind_commands(py::module_& module) {
    auto battle = py::class_<BattleDecision>(module, "BattleDecision");
    battle
        .def_property_readonly("kind", [](const BattleDecision&) { return DecisionKind::battle_command; })
        .def_readonly("player", &BattleDecision::player)
        .def_readonly("activatable", &BattleDecision::activatable)
        .def_readonly("attackable", &BattleDecision::attackable)
        .def_readonly("can_main_phase_2", &BattleDecision::can_main_phase_2)
        .def_readonly("can_end_phase", &BattleDecision::can_end_phase)
        .def("response", &BattleDecision::response, py::arg("command"), py::arg("index") = 0);
    set_public_module(battle);

    auto idle = py::class_<IdleDecision>(module, "IdleDecision");
    idle
        .def_property_readonly("kind", [](const IdleDecision&) { return DecisionKind::idle_command; })
        .def_readonly("player", &IdleDecision::player)
        .def_readonly("summonable", &IdleDecision::summonable)
        .def_readonly("special_summonable", &IdleDecision::special_summonable)
        .def_readonly("repositionable", &IdleDecision::repositionable)
        .def_readonly("monster_settable", &IdleDecision::monster_settable)
        .def_readonly("spell_trap_settable", &IdleDecision::spell_trap_settable)
        .def_readonly("activatable", &IdleDecision::activatable)
        .def_readonly("can_battle_phase", &IdleDecision::can_battle_phase)
        .def_readonly("can_end_phase", &IdleDecision::can_end_phase)
        .def_readonly("can_shuffle_hand", &IdleDecision::can_shuffle_hand)
        .def("response", &IdleDecision::response, py::arg("command"), py::arg("index") = 0);
    set_public_module(idle);

    auto effect_yes_no = py::class_<EffectYesNoDecision>(module, "EffectYesNoDecision");
    effect_yes_no
        .def_property_readonly("kind", [](const EffectYesNoDecision&) { return DecisionKind::effect_yes_no; })
        .def_readonly("player", &EffectYesNoDecision::player)
        .def_readonly("card", &EffectYesNoDecision::card)
        .def_readonly("description", &EffectYesNoDecision::description)
        .def("response", &EffectYesNoDecision::response, py::arg("yes"));
    set_public_module(effect_yes_no);

    auto yes_no = py::class_<YesNoDecision>(module, "YesNoDecision");
    yes_no
        .def_property_readonly("kind", [](const YesNoDecision&) { return DecisionKind::yes_no; })
        .def_readonly("player", &YesNoDecision::player)
        .def_readonly("description", &YesNoDecision::description)
        .def("response", &YesNoDecision::response, py::arg("yes"));
    set_public_module(yes_no);

    auto option = py::class_<OptionDecision>(module, "OptionDecision");
    option
        .def_property_readonly("kind", [](const OptionDecision&) { return DecisionKind::option; })
        .def_readonly("player", &OptionDecision::player)
        .def_readonly("options", &OptionDecision::options)
        .def("response", &OptionDecision::response, py::arg("index"));
    set_public_module(option);

    auto chain = py::class_<ChainDecision>(module, "ChainDecision");
    chain
        .def_property_readonly("kind", [](const ChainDecision&) { return DecisionKind::chain; })
        .def_readonly("player", &ChainDecision::player)
        .def_readonly("special_count", &ChainDecision::special_count)
        .def_readonly("forced", &ChainDecision::forced)
        .def_readonly("hint_timing", &ChainDecision::hint_timing)
        .def_readonly("opponent_hint_timing", &ChainDecision::opponent_hint_timing)
        .def_readonly("options", &ChainDecision::options)
        .def("response", &ChainDecision::response, py::arg("index"))
        .def("pass_response", &ChainDecision::pass_response);
    set_public_module(chain);
}

}
