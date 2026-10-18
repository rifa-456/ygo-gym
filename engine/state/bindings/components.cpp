#include "state/bindings/types.h"

namespace ygo_gym::state {

void bind_components(py::module_& module) {
    auto global = py::class_<GlobalState>(module, "GlobalState");
    global
        .def_property_readonly("turn_player", [](const GlobalState& value) {
            return static_cast<Player>(value.turn_player);
        })
        .def_property_readonly("decision_player", [](const GlobalState& value) -> py::object {
            if(!value.decision_player)
                return py::none();
            return py::cast(static_cast<Player>(*value.decision_player));
        })
        .def_readonly("turn_count", &GlobalState::turn_count)
        .def_property_readonly("phase", [](const GlobalState& value) {
            return static_cast<Phase>(value.phase);
        })
        .def_property_readonly("life_points", [](const GlobalState& value) {
            return py::make_tuple(value.life_points[0], value.life_points[1]);
        });
    public_type(global);

    auto properties = py::class_<CardProperties>(module, "CardProperties");
    properties
        .def_readonly("alias", &CardProperties::alias)
        .def_readonly("type", &CardProperties::type)
        .def_readonly("attribute", &CardProperties::attribute)
        .def_readonly("race", &CardProperties::race);
    public_type(properties);

    auto monster = py::class_<MonsterState>(module, "MonsterState");
    monster
        .def_readonly("level", &MonsterState::level)
        .def_readonly("rank", &MonsterState::rank)
        .def_readonly("attack", &MonsterState::attack)
        .def_readonly("defense", &MonsterState::defense)
        .def_readonly("base_attack", &MonsterState::base_attack)
        .def_readonly("base_defense", &MonsterState::base_defense);
    public_type(monster);

    auto pendulum = py::class_<PendulumState>(module, "PendulumState");
    pendulum
        .def_readonly("left_scale", &PendulumState::left_scale)
        .def_readonly("right_scale", &PendulumState::right_scale);
    public_type(pendulum);

    auto link = py::class_<LinkState>(module, "LinkState");
    link
        .def_readonly("rating", &LinkState::rating)
        .def_readonly("markers", &LinkState::markers);
    public_type(link);

    auto zone_count = py::class_<ZoneCount>(module, "ZoneCount");
    zone_count
        .def_property_readonly("player", [](const ZoneCount& value) { return static_cast<Player>(value.player); })
        .def_property_readonly("location", [](const ZoneCount& value) { return static_cast<Location>(value.location); })
        .def_readonly("count", &ZoneCount::count);
    public_type(zone_count);

    auto counter = py::class_<CounterState>(module, "CounterState");
    counter
        .def_readonly("card", &CounterState::card)
        .def_readonly("type", &CounterState::type)
        .def_readonly("count", &CounterState::count);
    public_type(counter);

    auto relation = py::class_<RelationState>(module, "RelationState");
    relation
        .def_readonly("kind", &RelationState::kind)
        .def_readonly("source", &RelationState::source)
        .def_readonly("target", &RelationState::target)
        .def_readonly("sequence", &RelationState::sequence);
    public_type(relation);

    auto chain = py::class_<ChainState>(module, "ChainState");
    chain
        .def_readonly("index", &ChainState::index)
        .def_readonly("card", &ChainState::card)
        .def_property_readonly("triggering_player", [](const ChainState& value) { return static_cast<Player>(value.triggering_player); })
        .def_property_readonly("triggering_controller", [](const ChainState& value) { return static_cast<Player>(value.triggering_controller); })
        .def_property_readonly("triggering_location", [](const ChainState& value) { return static_cast<Location>(value.triggering_location); })
        .def_readonly("triggering_sequence", &ChainState::triggering_sequence)
        .def_readonly("description", &ChainState::description);
    public_type(chain);
}

}
