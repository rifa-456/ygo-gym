#include "binding_types.h"

namespace ygo_gym::event {

void bind_cards(py::module_& module) {
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
}

}
