#include "binding.h"

#include <cstddef>
#include <type_traits>

#include <pybind11/stl.h>

#include "event.h"
#include "../state/types.h"

namespace py = pybind11;

namespace ygo_gym::event {
namespace {

template<typename T>
void public_type(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.event";
}

std::size_t normalize_index(py::ssize_t index, std::size_t size) {
    if(index < 0)
        index += static_cast<py::ssize_t>(size);
    if(index < 0 || static_cast<std::size_t>(index) >= size)
        throw py::index_error("index out of range");
    return static_cast<std::size_t>(index);
}

py::object event_object(const Event& event) {
    return std::visit([](const auto& value) { return py::cast(value); }, event);
}

py::object optional_player(const std::optional<std::uint8_t>& player) {
    if(!player)
        return py::none();
    return py::cast(static_cast<state::Player>(*player));
}

}

void bind_events(py::module_& module) {
    py::enum_<SummonKind>(module, "SummonKind")
        .value("NORMAL", SummonKind::normal)
        .value("SPECIAL", SummonKind::special)
        .value("FLIP", SummonKind::flip);
    py::enum_<SummonStage>(module, "SummonStage")
        .value("ATTEMPT", SummonStage::attempt)
        .value("COMPLETE", SummonStage::complete);
    py::enum_<ChainStage>(module, "ChainStage")
        .value("ACTIVATING", ChainStage::activating)
        .value("ADDED", ChainStage::added)
        .value("RESOLVING", ChainStage::resolving)
        .value("RESOLVED", ChainStage::resolved)
        .value("NEGATED", ChainStage::negated)
        .value("DISABLED", ChainStage::disabled)
        .value("ENDED", ChainStage::ended);
    py::enum_<LifePointKind>(module, "LifePointKind")
        .value("DAMAGE", LifePointKind::damage)
        .value("RECOVER", LifePointKind::recover)
        .value("PAY", LifePointKind::pay)
        .value("SET", LifePointKind::set);
    py::enum_<RelationEventKind>(module, "RelationEventKind")
        .value("EQUIP", RelationEventKind::equip)
        .value("UNEQUIP", RelationEventKind::unequip)
        .value("TARGET", RelationEventKind::target)
        .value("CANCEL_TARGET", RelationEventKind::cancel_target);
    py::enum_<RandomKind>(module, "RandomKind")
        .value("COIN", RandomKind::coin)
        .value("DICE", RandomKind::dice);
    py::enum_<DamageStepStage>(module, "DamageStepStage")
        .value("START", DamageStepStage::start)
        .value("END", DamageStepStage::end);

    auto location = py::class_<Locator>(module, "EventLocation");
    location
        .def_property_readonly("controller", [](const Locator& value) { return static_cast<state::Player>(value.controller); })
        .def_property_readonly("location", [](const Locator& value) { return static_cast<state::Location>(value.location); })
        .def_readonly("sequence", &Locator::sequence)
        .def_property_readonly("position", [](const Locator& value) { return static_cast<state::Position>(value.position); });
    public_type(location);

    auto event_card = py::class_<EventCardView>(module, "EventCard");
    event_card
        .def_property_readonly("id", &EventCardView::id)
        .def_property_readonly("code", &EventCardView::code)
        .def_property_readonly("current_card", [](const EventCardView& value) -> py::object {
            if(!value.current_card())
                return py::none();
            return py::int_(*value.current_card());
        });
    public_type(event_card);

    auto event_cards = py::class_<EventCardCollection>(module, "EventCardCollection");
    event_cards
        .def("__len__", &EventCardCollection::size)
        .def("__getitem__", [](const EventCardCollection& values, py::ssize_t index) {
            return values.at(normalize_index(index, values.size()));
        });
    public_type(event_cards);

#define SIMPLE_TYPE(TYPE, NAME) auto NAME = py::class_<TYPE>(module, #TYPE); public_type(NAME)
    SIMPLE_TYPE(TurnEvent, turn);
    turn.def_property_readonly("player", [](const TurnEvent& value) { return static_cast<state::Player>(value.player); });

    SIMPLE_TYPE(PhaseEvent, phase);
    phase.def_property_readonly("phase", [](const PhaseEvent& value) { return static_cast<state::Phase>(value.phase); });

    SIMPLE_TYPE(ShuffleEvent, shuffle);
    shuffle
        .def_property_readonly("player", [](const ShuffleEvent& value) { return static_cast<state::Player>(value.player); })
        .def_property_readonly("location", [](const ShuffleEvent& value) { return static_cast<state::Location>(value.location); });

    SIMPLE_TYPE(RevealEvent, reveal);
    reveal.def_readonly("card", &RevealEvent::card);

    SIMPLE_TYPE(DrawEvent, draw);
    draw
        .def_property_readonly("player", [](const DrawEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("card", &DrawEvent::card);

    SIMPLE_TYPE(MoveEvent, move);
    move
        .def_readonly("card", &MoveEvent::card)
        .def_readonly("previous", &MoveEvent::previous)
        .def_readonly("current", &MoveEvent::current)
        .def_readonly("reason", &MoveEvent::reason);

    SIMPLE_TYPE(PositionEvent, position);
    position
        .def_readonly("card", &PositionEvent::card)
        .def_property_readonly("controller", [](const PositionEvent& value) { return static_cast<state::Player>(value.controller); })
        .def_property_readonly("location", [](const PositionEvent& value) { return static_cast<state::Location>(value.location); })
        .def_readonly("sequence", &PositionEvent::sequence)
        .def_property_readonly("previous_position", [](const PositionEvent& value) { return static_cast<state::Position>(value.previous_position); })
        .def_property_readonly("position", [](const PositionEvent& value) { return static_cast<state::Position>(value.position); });

    SIMPLE_TYPE(SetEvent, set);
    set.def_readonly("card", &SetEvent::card);

    SIMPLE_TYPE(SummonEvent, summon);
    summon
        .def_readonly("card", &SummonEvent::card)
        .def_property_readonly("player", [](const SummonEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("kind", &SummonEvent::kind)
        .def_readonly("stage", &SummonEvent::stage);

    SIMPLE_TYPE(ChainEvent, chain);
    chain
        .def_readonly("stage", &ChainEvent::stage)
        .def_readonly("card", &ChainEvent::card)
        .def_property_readonly("player", [](const ChainEvent& value) { return optional_player(value.player); })
        .def_readonly("description", &ChainEvent::description)
        .def_readonly("chain_index", &ChainEvent::chain_index);

    SIMPLE_TYPE(LifePointEvent, lp);
    lp
        .def_property_readonly("player", [](const LifePointEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("amount", &LifePointEvent::amount)
        .def_readonly("kind", &LifePointEvent::kind);

    SIMPLE_TYPE(CounterEvent, counter);
    counter
        .def_readonly("card", &CounterEvent::card)
        .def_readonly("type", &CounterEvent::type)
        .def_readonly("change", &CounterEvent::change);

    SIMPLE_TYPE(RelationEvent, relation);
    relation
        .def_readonly("kind", &RelationEvent::kind)
        .def_readonly("source", &RelationEvent::source)
        .def_readonly("target", &RelationEvent::target);

    SIMPLE_TYPE(AttackEvent, attack);
    attack
        .def_readonly("attacker", &AttackEvent::attacker)
        .def_readonly("target", &AttackEvent::target);

    SIMPLE_TYPE(BattleEvent, battle);
    battle
        .def_readonly("attacker", &BattleEvent::attacker)
        .def_readonly("attacker_attack", &BattleEvent::attacker_attack)
        .def_readonly("attacker_defense", &BattleEvent::attacker_defense)
        .def_readonly("attacker_destroyed", &BattleEvent::attacker_destroyed)
        .def_readonly("target", &BattleEvent::target)
        .def_readonly("target_attack", &BattleEvent::target_attack)
        .def_readonly("target_defense", &BattleEvent::target_defense)
        .def_readonly("target_destroyed", &BattleEvent::target_destroyed);

    SIMPLE_TYPE(RandomEvent, random);
    random
        .def_property_readonly("player", [](const RandomEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("kind", &RandomEvent::kind)
        .def_readonly("results", &RandomEvent::results);

    SIMPLE_TYPE(DamageStepEvent, damage_step);
    damage_step.def_readonly("stage", &DamageStepEvent::stage);

    SIMPLE_TYPE(GraveDeckSwapEvent, grave_deck);
    grave_deck.def_property_readonly("player", [](const GraveDeckSwapEvent& value) { return static_cast<state::Player>(value.player); });

    SIMPLE_TYPE(DeckReverseEvent, deck_reverse);

    SIMPLE_TYPE(WinEvent, win);
    win
        .def_property_readonly("winner", [](const WinEvent& value) { return optional_player(value.winner); })
        .def_readonly("reason", &WinEvent::reason);
#undef SIMPLE_TYPE

    auto batch = py::class_<Batch>(module, "EventBatch");
    batch
        .def("__len__", &Batch::size)
        .def_property_readonly("cards", &Batch::cards)
        .def("__getitem__", [](const Batch& value, py::ssize_t index) {
            const auto events = value.events();
            return event_object(events.at(normalize_index(index, events.size())));
        });
    public_type(batch);
}

}
