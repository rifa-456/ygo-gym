#include "protocol/bindings/types.h"

namespace ygo_gym::protocol {

void bind_announcement(py::module_& module) {
    auto race = py::class_<AnnounceRaceDecision>(module, "AnnounceRaceDecision");
    race
        .def_property_readonly("kind", [](const AnnounceRaceDecision&) { return DecisionKind::announce_race; })
        .def_readonly("player", &AnnounceRaceDecision::player)
        .def_readonly("count", &AnnounceRaceDecision::count)
        .def_readonly("available", &AnnounceRaceDecision::available)
        .def("response", &AnnounceRaceDecision::response, py::arg("races"));
    set_public_module(race);

    auto attribute = py::class_<AnnounceAttributeDecision>(module, "AnnounceAttributeDecision");
    attribute
        .def_property_readonly("kind", [](const AnnounceAttributeDecision&) { return DecisionKind::announce_attribute; })
        .def_readonly("player", &AnnounceAttributeDecision::player)
        .def_readonly("count", &AnnounceAttributeDecision::count)
        .def_readonly("available", &AnnounceAttributeDecision::available)
        .def("response", &AnnounceAttributeDecision::response, py::arg("attributes"));
    set_public_module(attribute);

    auto announce_card = py::class_<AnnounceCardDecision>(module, "AnnounceCardDecision");
    announce_card
        .def_property_readonly("kind", [](const AnnounceCardDecision&) { return DecisionKind::announce_card; })
        .def_readonly("player", &AnnounceCardDecision::player)
        .def_readonly("opcodes", &AnnounceCardDecision::opcodes)
        .def("response", &AnnounceCardDecision::response, py::arg("code"));
    set_public_module(announce_card);

    auto number = py::class_<AnnounceNumberDecision>(module, "AnnounceNumberDecision");
    number
        .def_property_readonly("kind", [](const AnnounceNumberDecision&) { return DecisionKind::announce_number; })
        .def_readonly("player", &AnnounceNumberDecision::player)
        .def_readonly("options", &AnnounceNumberDecision::options)
        .def("response", &AnnounceNumberDecision::response, py::arg("index"));
    set_public_module(number);

    auto rps = py::class_<RockPaperScissorsDecision>(module, "RockPaperScissorsDecision");
    rps
        .def_property_readonly("kind", [](const RockPaperScissorsDecision&) { return DecisionKind::rock_paper_scissors; })
        .def_readonly("player", &RockPaperScissorsDecision::player)
        .def("response", &RockPaperScissorsDecision::response, py::arg("choice"));
    set_public_module(rps);
}

}
