#include "state/bindings/types.h"

namespace ygo_gym::state {

void bind_full_state(py::module_& module) {
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
