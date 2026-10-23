#include "state/bindings/types.h"

namespace ygo_gym::state {

void bind_observation(py::module_& module) {
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
        .def_property_readonly("events", &Observation::events)
        .def_property_readonly("_client_batch", [](const Observation& value) -> py::object {
            const auto& batch = value.storage()->client_batch;
            if(!batch) return py::none();
            py::list packets;
            for(const auto& packet : batch->packets)
                packets.append(py::bytes(reinterpret_cast<const char*>(packet.data()), packet.size()));
            return py::make_tuple(batch->session, batch->index, batch->initial, packets);
        });
    public_type(observation);
}

}
