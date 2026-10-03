#include "binding.h"

#include <pybind11/stl.h>

#include "action.h"

namespace py = pybind11;

namespace ygo_gym::action {
namespace {

template<typename T>
void set_public_module(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.action";
}

}

void bind_actions(py::module_& module) {
    py::enum_<ActionKind>(module, "ActionKind")
        .value("SUMMON", ActionKind::summon)
        .value("SPECIAL_SUMMON", ActionKind::special_summon)
        .value("REPOSITION", ActionKind::reposition)
        .value("SET_MONSTER", ActionKind::set_monster)
        .value("SET_SPELL_TRAP", ActionKind::set_spell_trap)
        .value("ACTIVATE", ActionKind::activate)
        .value("ATTACK", ActionKind::attack)
        .value("BATTLE_PHASE", ActionKind::battle_phase)
        .value("MAIN_PHASE_2", ActionKind::main_phase_2)
        .value("END_PHASE", ActionKind::end_phase)
        .value("SHUFFLE_HAND", ActionKind::shuffle_hand)
        .value("PASS", ActionKind::pass)
        .value("YES", ActionKind::yes)
        .value("NO", ActionKind::no)
        .value("OPTION", ActionKind::option)
        .value("SELECT_CARD", ActionKind::select_card)
        .value("SELECT_TRIBUTE", ActionKind::select_tribute)
        .value("SELECT_SUM_CARD", ActionKind::select_sum_card)
        .value("UNSELECT_CARD", ActionKind::unselect_card)
        .value("ORDER_CARD", ActionKind::order_card)
        .value("SELECT_ZONE", ActionKind::select_zone)
        .value("SELECT_POSITION", ActionKind::select_position)
        .value("ALLOCATE_COUNTER", ActionKind::allocate_counter)
        .value("SELECT_RACE", ActionKind::select_race)
        .value("SELECT_ATTRIBUTE", ActionKind::select_attribute)
        .value("ANNOUNCE_CARD", ActionKind::announce_card)
        .value("ANNOUNCE_NUMBER", ActionKind::announce_number)
        .value("ROCK_PAPER_SCISSORS", ActionKind::rock_paper_scissors)
        .value("CONFIRM", ActionKind::confirm)
        .value("CANCEL", ActionKind::cancel);

    auto simple = py::class_<SimpleAction>(module, "SimpleAction");
    simple.def_readonly("kind", &SimpleAction::kind);
    set_public_module(simple);

    auto card = py::class_<CardAction>(module, "CardAction");
    card
        .def_readonly("kind", &CardAction::kind)
        .def_readonly("card", &CardAction::card);
    set_public_module(card);

    auto effect = py::class_<EffectAction>(module, "EffectAction");
    effect
        .def_readonly("kind", &EffectAction::kind)
        .def_readonly("effect", &EffectAction::effect);
    set_public_module(effect);

    auto attack = py::class_<AttackAction>(module, "AttackAction");
    attack
        .def_readonly("kind", &AttackAction::kind)
        .def_readonly("attack", &AttackAction::attack);
    set_public_module(attack);

    auto tribute = py::class_<TributeAction>(module, "TributeAction");
    tribute
        .def_readonly("kind", &TributeAction::kind)
        .def_readonly("tribute", &TributeAction::tribute);
    set_public_module(tribute);

    auto sum = py::class_<SumAction>(module, "SumAction");
    sum
        .def_readonly("kind", &SumAction::kind)
        .def_readonly("sum", &SumAction::sum);
    set_public_module(sum);

    auto zone = py::class_<ZoneAction>(module, "ZoneAction");
    zone
        .def_readonly("kind", &ZoneAction::kind)
        .def_readonly("zone", &ZoneAction::zone);
    set_public_module(zone);

    auto position = py::class_<PositionAction>(module, "PositionAction");
    position
        .def_readonly("kind", &PositionAction::kind)
        .def_readonly("position", &PositionAction::position);
    set_public_module(position);

    auto option = py::class_<OptionAction>(module, "OptionAction");
    option
        .def_readonly("kind", &OptionAction::kind)
        .def_readonly("index", &OptionAction::index)
        .def_readonly("description", &OptionAction::description);
    set_public_module(option);

    auto counter = py::class_<CounterAction>(module, "CounterAction");
    counter
        .def_readonly("kind", &CounterAction::kind)
        .def_readonly("counter", &CounterAction::counter)
        .def_readonly("count", &CounterAction::count);
    set_public_module(counter);

    auto race = py::class_<RaceAction>(module, "RaceAction");
    race
        .def_readonly("kind", &RaceAction::kind)
        .def_readonly("race", &RaceAction::race);
    set_public_module(race);

    auto attribute = py::class_<AttributeAction>(module, "AttributeAction");
    attribute
        .def_readonly("kind", &AttributeAction::kind)
        .def_readonly("attribute", &AttributeAction::attribute);
    set_public_module(attribute);

    auto card_code = py::class_<CardCodeAction>(module, "CardCodeAction");
    card_code
        .def_readonly("kind", &CardCodeAction::kind)
        .def_readonly("code", &CardCodeAction::code);
    set_public_module(card_code);

    auto number = py::class_<NumberAction>(module, "NumberAction");
    number
        .def_readonly("kind", &NumberAction::kind)
        .def_readonly("index", &NumberAction::index)
        .def_readonly("number", &NumberAction::number);
    set_public_module(number);

    auto rps = py::class_<RpsAction>(module, "RpsAction");
    rps
        .def_readonly("kind", &RpsAction::kind)
        .def_readonly("choice", &RpsAction::choice);
    set_public_module(rps);
}

}
