#include "binding_types.h"

namespace ygo_gym::event {

void bind_movement(py::module_& module) {
    auto turn = py::class_<TurnEvent>(module, "TurnEvent");
    public_type(turn);
    turn.def_property_readonly("player", [](const TurnEvent& value) { return static_cast<state::Player>(value.player); });

    auto phase = py::class_<PhaseEvent>(module, "PhaseEvent");
    public_type(phase);
    phase.def_property_readonly("phase", [](const PhaseEvent& value) { return static_cast<state::Phase>(value.phase); });

    auto shuffle = py::class_<ShuffleEvent>(module, "ShuffleEvent");
    public_type(shuffle);
    shuffle
        .def_property_readonly("player", [](const ShuffleEvent& value) { return static_cast<state::Player>(value.player); })
        .def_property_readonly("location", [](const ShuffleEvent& value) { return static_cast<state::Location>(value.location); });

    auto reveal = py::class_<RevealEvent>(module, "RevealEvent");
    public_type(reveal);
    reveal.def_readonly("card", &RevealEvent::card);

    auto draw = py::class_<DrawEvent>(module, "DrawEvent");
    public_type(draw);
    draw
        .def_property_readonly("player", [](const DrawEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("card", &DrawEvent::card);

    auto move = py::class_<MoveEvent>(module, "MoveEvent");
    public_type(move);
    move
        .def_readonly("card", &MoveEvent::card)
        .def_readonly("previous", &MoveEvent::previous)
        .def_readonly("current", &MoveEvent::current)
        .def_readonly("reason", &MoveEvent::reason);

    auto position = py::class_<PositionEvent>(module, "PositionEvent");
    public_type(position);
    position
        .def_readonly("card", &PositionEvent::card)
        .def_property_readonly("controller", [](const PositionEvent& value) { return static_cast<state::Player>(value.controller); })
        .def_property_readonly("location", [](const PositionEvent& value) { return static_cast<state::Location>(value.location); })
        .def_readonly("sequence", &PositionEvent::sequence)
        .def_property_readonly("previous_position", [](const PositionEvent& value) { return static_cast<state::Position>(value.previous_position); })
        .def_property_readonly("position", [](const PositionEvent& value) { return static_cast<state::Position>(value.position); });

    auto set = py::class_<SetEvent>(module, "SetEvent");
    public_type(set);
    set.def_readonly("card", &SetEvent::card);

    auto summon = py::class_<SummonEvent>(module, "SummonEvent");
    public_type(summon);
    summon
        .def_readonly("card", &SummonEvent::card)
        .def_property_readonly("player", [](const SummonEvent& value) { return static_cast<state::Player>(value.player); })
        .def_readonly("kind", &SummonEvent::kind)
        .def_readonly("stage", &SummonEvent::stage);

    auto chain = py::class_<ChainEvent>(module, "ChainEvent");
    public_type(chain);
    chain
        .def_readonly("stage", &ChainEvent::stage)
        .def_readonly("card", &ChainEvent::card)
        .def_property_readonly("player", [](const ChainEvent& value) { return optional_player(value.player); })
        .def_readonly("description", &ChainEvent::description)
        .def_readonly("chain_index", &ChainEvent::chain_index);
}

}
