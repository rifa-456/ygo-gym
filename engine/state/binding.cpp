#include "binding.h"

#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include <pybind11/stl.h>

#include "observation.h"
#include "state.h"

namespace py = pybind11;

namespace ygo_gym::state {
namespace {

template<typename T>
void public_type(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.state";
}

template<typename T>
py::object optional_component(const T* value) {
    if(value == nullptr)
        return py::none();
    return py::cast(*value);
}

std::size_t normalize_index(py::ssize_t index, std::size_t size) {
    if(index < 0)
        index += static_cast<py::ssize_t>(size);
    if(index < 0 || static_cast<std::size_t>(index) >= size)
        throw py::index_error("index out of range");
    return static_cast<std::size_t>(index);
}

template<typename Storage>
py::tuple slice_ids(const Storage& values, std::uint32_t begin, std::uint32_t count) {
    py::tuple result(count);
    for(std::uint32_t index = 0; index < count; ++index)
        result[index] = values[begin + index];
    return result;
}

}

void bind_state(py::module_& module) {
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

    auto cards = py::class_<CardCollection>(module, "CardCollection");
    cards
        .def("__len__", &CardCollection::size)
        .def("__getitem__", [](const CardCollection& values, py::ssize_t index) {
            return values.at(normalize_index(index, values.size()));
        });
    public_type(cards);

    auto card = py::class_<CardView>(module, "Card");
    card
        .def_property_readonly("id", &CardView::id)
        .def_property_readonly("code", &CardView::code)
        .def_property_readonly("owner", [](const CardView& value) { return static_cast<Player>(value.owner()); })
        .def_property_readonly("controller", [](const CardView& value) { return static_cast<Player>(value.controller()); })
        .def_property_readonly("location", [](const CardView& value) { return static_cast<Location>(value.location()); })
        .def_property_readonly("sequence", &CardView::sequence)
        .def_property_readonly("position", [](const CardView& value) { return static_cast<Position>(value.position()); })
        .def_property_readonly("properties", [](const CardView& value) { return optional_component(value.properties()); })
        .def_property_readonly("monster", [](const CardView& value) { return optional_component(value.monster()); })
        .def_property_readonly("pendulum", [](const CardView& value) { return optional_component(value.pendulum()); })
        .def_property_readonly("link", [](const CardView& value) { return optional_component(value.link()); });
    public_type(card);

    auto observation = py::class_<Observation>(module, "Observation");
    observation
        .def_property_readonly("viewer", [](const Observation& value) { return static_cast<Player>(value.viewer()); })
        .def_property_readonly("global_state", &Observation::global)
        .def_property_readonly("cards", &Observation::cards)
        .def_property_readonly("zone_counts", &Observation::zone_counts)
        .def("zone_count", [](const Observation& value, std::uint8_t player, std::uint32_t location) {
            for(const auto& zone : value.zone_counts()) {
                if(zone.player == player && zone.location == location)
                    return zone.count;
            }
            throw std::invalid_argument("unknown player/location pair");
        })
        .def_property_readonly("counters", &Observation::counters)
        .def_property_readonly("relations", &Observation::relations)
        .def_property_readonly("chain", &Observation::chain)
        .def("chain_targets", [](const Observation& value, std::size_t index) {
            if(index >= value.chain().size())
                throw py::index_error("chain index out of range");
            const auto& link = value.chain()[index];
            return slice_ids(value.chain_targets(), link.target_begin, link.target_count);
        })
        .def_property_readonly("pending_actions", &Observation::pending_actions)
        .def_property_readonly("events", &Observation::events);
    public_type(observation);

    auto player_state = py::class_<PlayerState>(module, "PlayerState");
    player_state
        .def_readonly("life_points", &PlayerState::life_points)
        .def_readonly("starting_life_points", &PlayerState::starting_life_points)
        .def_readonly("starting_hand_size", &PlayerState::starting_hand_size)
        .def_readonly("draw_count", &PlayerState::draw_count)
        .def_readonly("used_locations", &PlayerState::used_locations)
        .def_readonly("disabled_locations", &PlayerState::disabled_locations)
        .def_readonly("faceup_extra_count", &PlayerState::faceup_extra_count);
    public_type(player_state);

    auto state_cards = py::class_<StateCardCollection>(module, "StateCardCollection");
    state_cards
        .def("__len__", &StateCardCollection::size)
        .def("__getitem__", [](const StateCardCollection& values, py::ssize_t index) {
            return values.at(normalize_index(index, values.size()));
        });
    public_type(state_cards);

    auto state_card = py::class_<StateCardView>(module, "StateCard");
    state_card
        .def_property_readonly("id", &StateCardView::id)
        .def_property_readonly("code", [](const StateCardView& value) { return value.card().code; })
        .def_property_readonly("owner", [](const StateCardView& value) { return static_cast<Player>(value.card().owner); })
        .def_property_readonly("controller", [](const StateCardView& value) { return static_cast<Player>(value.card().controller); })
        .def_property_readonly("location", [](const StateCardView& value) { return static_cast<Location>(value.card().location); })
        .def_property_readonly("sequence", [](const StateCardView& value) { return value.card().sequence; })
        .def_property_readonly("position", [](const StateCardView& value) { return static_cast<Position>(value.card().position); })
        .def_property_readonly("properties", [](const StateCardView& value) { return value.properties(); })
        .def_property_readonly("monster", [](const StateCardView& value) { return optional_component(value.monster()); })
        .def_property_readonly("pendulum", [](const StateCardView& value) { return optional_component(value.pendulum()); })
        .def_property_readonly("link", [](const StateCardView& value) { return optional_component(value.link()); });
    public_type(state_card);

    auto state = py::class_<State>(module, "State");
    state
        .def_property_readonly("global_state", &State::global)
        .def_property_readonly("duel_options", &State::duel_options)
        .def("player", &State::player, py::arg("player"))
        .def_property_readonly("cards", &State::cards)
        .def("zone", [](const State& value, std::uint8_t player, std::uint32_t location) {
            for(const auto& zone : value.zones()) {
                if(zone.player == player && zone.location == location)
                    return slice_ids(value.zone_cards(), zone.begin, zone.count);
            }
            throw std::invalid_argument("unknown player/location pair");
        })
        .def_property_readonly("counters", &State::counters)
        .def_property_readonly("relations", &State::relations)
        .def_property_readonly("chain", &State::chain)
        .def("chain_targets", [](const State& value, std::size_t index) {
            if(index >= value.chain().size())
                throw py::index_error("chain index out of range");
            const auto& link = value.chain()[index];
            return slice_ids(value.chain_targets(), link.target_begin, link.target_count);
        })
        .def_property_readonly("pending_actions", &State::pending_actions)
        .def_property_readonly("events", &State::events);
    public_type(state);

    module.attr("UNKNOWN_CARD") = py::int_(unknown_card);
}

}
