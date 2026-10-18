#include "protocol/bindings/types.h"

namespace ygo_gym::protocol {

void bind_selection(py::module_& module) {
    auto card = py::class_<CardDecision>(module, "CardDecision");
    card
        .def_property_readonly("kind", [](const CardDecision&) { return DecisionKind::card; })
        .def_readonly("player", &CardDecision::player)
        .def_readonly("cancelable", &CardDecision::cancelable)
        .def_readonly("min", &CardDecision::min)
        .def_readonly("max", &CardDecision::max)
        .def_readonly("cards", &CardDecision::cards)
        .def("response", &CardDecision::response, py::arg("indices"))
        .def("cancel_response", &CardDecision::cancel_response);
    set_public_module(card);

    auto place = py::class_<PlaceDecision>(module, "PlaceDecision");
    place
        .def_property_readonly("kind", [](const PlaceDecision& value) {
            return value.disable_field ? DecisionKind::disable_field : DecisionKind::place;
        })
        .def_readonly("player", &PlaceDecision::player)
        .def_readonly("count", &PlaceDecision::count)
        .def_readonly("unavailable", &PlaceDecision::unavailable)
        .def_readonly("disable_field", &PlaceDecision::disable_field)
        .def("response", &PlaceDecision::response, py::arg("zones"));
    set_public_module(place);

    auto position = py::class_<PositionDecision>(module, "PositionDecision");
    position
        .def_property_readonly("kind", [](const PositionDecision&) { return DecisionKind::position; })
        .def_readonly("player", &PositionDecision::player)
        .def_readonly("card_code", &PositionDecision::card_code)
        .def_readonly("positions", &PositionDecision::positions)
        .def("response", &PositionDecision::response, py::arg("position"));
    set_public_module(position);

    auto tribute = py::class_<TributeDecision>(module, "TributeDecision");
    tribute
        .def_property_readonly("kind", [](const TributeDecision&) { return DecisionKind::tribute; })
        .def_readonly("player", &TributeDecision::player)
        .def_readonly("cancelable", &TributeDecision::cancelable)
        .def_readonly("min", &TributeDecision::min)
        .def_readonly("max", &TributeDecision::max)
        .def_readonly("cards", &TributeDecision::cards)
        .def("response", &TributeDecision::response, py::arg("indices"))
        .def("cancel_response", &TributeDecision::cancel_response);
    set_public_module(tribute);

    auto counter = py::class_<CounterDecision>(module, "CounterDecision");
    counter
        .def_property_readonly("kind", [](const CounterDecision&) { return DecisionKind::counter; })
        .def_readonly("player", &CounterDecision::player)
        .def_readonly("counter_type", &CounterDecision::counter_type)
        .def_readonly("count", &CounterDecision::count)
        .def_readonly("cards", &CounterDecision::cards)
        .def("response", &CounterDecision::response, py::arg("counts"));
    set_public_module(counter);

    auto sum = py::class_<SumDecision>(module, "SumDecision");
    sum
        .def_property_readonly("kind", [](const SumDecision&) { return DecisionKind::sum; })
        .def_readonly("player", &SumDecision::player)
        .def_readonly("mode", &SumDecision::mode)
        .def_readonly("target", &SumDecision::target)
        .def_readonly("min", &SumDecision::min)
        .def_readonly("max", &SumDecision::max)
        .def_readonly("required", &SumDecision::required)
        .def_readonly("cards", &SumDecision::cards)
        .def("response", &SumDecision::response, py::arg("indices"));
    set_public_module(sum);

    auto sort = py::class_<SortDecision>(module, "SortDecision");
    sort
        .def_property_readonly("kind", [](const SortDecision& value) {
            return value.chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
        })
        .def_readonly("player", &SortDecision::player)
        .def_readonly("chain", &SortDecision::chain)
        .def_readonly("cards", &SortDecision::cards)
        .def("response", &SortDecision::response, py::arg("order"))
        .def("cancel_response", &SortDecision::cancel_response);
    set_public_module(sort);

    auto unselect = py::class_<UnselectCardDecision>(module, "UnselectCardDecision");
    unselect
        .def_property_readonly("kind", [](const UnselectCardDecision&) { return DecisionKind::unselect_card; })
        .def_readonly("player", &UnselectCardDecision::player)
        .def_readonly("finishable", &UnselectCardDecision::finishable)
        .def_readonly("cancelable", &UnselectCardDecision::cancelable)
        .def_readonly("min", &UnselectCardDecision::min)
        .def_readonly("max", &UnselectCardDecision::max)
        .def_readonly("selectable", &UnselectCardDecision::selectable)
        .def_readonly("unselectable", &UnselectCardDecision::unselectable)
        .def("response", &UnselectCardDecision::response, py::arg("index"))
        .def("finish_response", &UnselectCardDecision::finish_response);
    set_public_module(unselect);
}

}
