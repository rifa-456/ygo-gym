#include "event/bindings/types.h"

namespace ygo_gym::event {

void bind_battle(py::module_& module) {
    auto lp = py::class_<LifePointEvent>(module, "LifePointEvent");
    public_type(lp);
    lp
        .def_property_readonly("player", [](const LifePointEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("amount", &LifePointEvent::amount)
        .def_readonly("kind", &LifePointEvent::kind);

    auto counter = py::class_<CounterEvent>(module, "CounterEvent");
    public_type(counter);
    counter
        .def_readonly("card", &CounterEvent::card)
        .def_readonly("type", &CounterEvent::type)
        .def_readonly("change", &CounterEvent::change);

    auto relation = py::class_<RelationEvent>(module, "RelationEvent");
    public_type(relation);
    relation
        .def_readonly("kind", &RelationEvent::kind)
        .def_readonly("source", &RelationEvent::source)
        .def_readonly("target", &RelationEvent::target);

    auto attack = py::class_<AttackEvent>(module, "AttackEvent");
    public_type(attack);
    attack
        .def_readonly("attacker", &AttackEvent::attacker)
        .def_readonly("target", &AttackEvent::target);

    auto battle = py::class_<BattleEvent>(module, "BattleEvent");
    public_type(battle);
    battle
        .def_readonly("attacker", &BattleEvent::attacker)
        .def_readonly("attacker_attack", &BattleEvent::attacker_attack)
        .def_readonly("attacker_defense", &BattleEvent::attacker_defense)
        .def_readonly("attacker_destroyed", &BattleEvent::attacker_destroyed)
        .def_readonly("target", &BattleEvent::target)
        .def_readonly("target_attack", &BattleEvent::target_attack)
        .def_readonly("target_defense", &BattleEvent::target_defense)
        .def_readonly("target_destroyed", &BattleEvent::target_destroyed);

    auto random = py::class_<RandomEvent>(module, "RandomEvent");
    public_type(random);
    random
        .def_property_readonly("player", [](const RandomEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("kind", &RandomEvent::kind)
        .def_readonly("results", &RandomEvent::results);

    auto damage_step = py::class_<DamageStepEvent>(module, "DamageStepEvent");
    public_type(damage_step);
    damage_step.def_readonly("stage", &DamageStepEvent::stage);

    auto grave_deck = py::class_<GraveDeckSwapEvent>(module, "GraveDeckSwapEvent");
    public_type(grave_deck);
    grave_deck.def_property_readonly("player", [](const GraveDeckSwapEvent& value) { return static_cast<state::Player>(value.player); });

    auto deck_reverse = py::class_<DeckReverseEvent>(module, "DeckReverseEvent");
    public_type(deck_reverse);

    auto win = py::class_<WinEvent>(module, "WinEvent");
    public_type(win);
    win
        .def_property_readonly("winner", [](const WinEvent& value) { return optional_player(value.winner); })
        .def_readonly("reason", &WinEvent::reason);
}

}
