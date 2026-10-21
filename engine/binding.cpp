#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "action/bindings/register.h"
#include "duel/duel.h"
#include "profiling/binding.h"
#include "event/bindings/register.h"
#include "engine.h"
#include "protocol/bindings/register.h"
#include "state/bindings/register.h"

namespace py = pybind11;

namespace {

ygo_gym::CardDefinition to_card_definition(const py::handle& value) {
    return ygo_gym::CardDefinition{
        py::cast<std::uint32_t>(value.attr("code")),
        py::cast<std::uint32_t>(value.attr("alias")),
        py::cast<std::vector<std::uint16_t>>(value.attr("setcodes")),
        py::cast<std::uint32_t>(value.attr("type")),
        py::cast<std::uint32_t>(value.attr("level")),
        py::cast<std::uint32_t>(value.attr("attribute")),
        py::cast<std::uint64_t>(value.attr("race")),
        py::cast<std::int32_t>(value.attr("attack")),
        py::cast<std::int32_t>(value.attr("defense")),
        py::cast<std::uint32_t>(value.attr("left_scale")),
        py::cast<std::uint32_t>(value.attr("right_scale")),
        py::cast<std::uint32_t>(value.attr("link_marker")),
    };
}

py::object decision_object(const ygo_gym::Duel& duel) {
    const auto& decision = duel.decision();
    if(!decision)
        return py::none();
    return std::visit([](const auto& value) { return py::cast(value); }, *decision);
}

}

PYBIND11_MODULE(_native, module) {
    ygo_gym::profiling::bind(module);
    ygo_gym::protocol::bind_protocol(module);
    ygo_gym::event::bind_events(module);
    ygo_gym::action::bind_actions(module);
    ygo_gym::state::bind_state(module);

    py::class_<ygo_gym::Outcome>(module, "Outcome")
        .def_property_readonly("winner", [](const ygo_gym::Outcome& outcome) -> py::object {
            if(!outcome.winner)
                return py::none();
            return py::cast(static_cast<ygo_gym::state::Player>(*outcome.winner));
        })
        .def_readonly("reason", &ygo_gym::Outcome::reason)
        .def_property_readonly("rewards", [](const ygo_gym::Outcome& outcome) {
            const auto rewards = outcome.rewards();
            return py::make_tuple(rewards[0], rewards[1]);
        });

    py::class_<ygo_gym::Duel>(module, "Duel")
        .def("clone", &ygo_gym::Duel::clone, py::kw_only(),
             py::arg("preserve_rng") = false, py::arg("seed") = py::none())
        .def("close", &ygo_gym::Duel::close)
        .def("respond", &ygo_gym::Duel::respond, py::arg("response"))
        .def("step", &ygo_gym::Duel::step, py::arg("action_index"))
        .def("observe", &ygo_gym::Duel::observe, py::arg("player"))
        .def("state", &ygo_gym::Duel::state)
        .def_property_readonly("observation", [](const ygo_gym::Duel& duel) { return duel.observation(); })
        .def_property_readonly("closed", &ygo_gym::Duel::closed)
        .def_property_readonly("terminated", &ygo_gym::Duel::terminated)
        .def_property_readonly("current_player", [](const ygo_gym::Duel& duel) -> py::object {
            const auto player = duel.current_player();
            if(!player)
                return py::none();
            return py::cast(static_cast<ygo_gym::state::Player>(*player));
        })
        .def_property_readonly("outcome", [](const ygo_gym::Duel& duel) -> py::object {
            const auto& outcome = duel.outcome();
            return outcome ? py::cast(*outcome) : py::none();
        })
        .def_property_readonly("rewards", [](const ygo_gym::Duel& duel) {
            const auto rewards = duel.rewards();
            return py::make_tuple(rewards[0], rewards[1]);
        })
        .def_property_readonly("status", &ygo_gym::Duel::status)
        .def_property_readonly("decision", &decision_object)
        .def_property_readonly("actions", &ygo_gym::Duel::actions)
        .def_property_readonly("pending_actions", &ygo_gym::Duel::pending_actions)
        .def_property_readonly("message_buffer", [](const ygo_gym::Duel& duel) {
            const auto& buffer = duel.message_buffer();
            return py::bytes(reinterpret_cast<const char*>(buffer.data()), buffer.size());
        });

    py::class_<ygo_gym::Engine>(module, "Engine")
        .def(
            py::init([](
                const std::string& card_database,
                const std::vector<std::string>& script_roots,
                const py::iterable& card_definitions
            ) {
                std::vector<std::filesystem::path> roots;
                roots.reserve(script_roots.size());
                for(const auto& root : script_roots)
                    roots.emplace_back(root);

                std::vector<ygo_gym::CardDefinition> cards;
                for(const auto& value : card_definitions)
                    cards.push_back(to_card_definition(value));

                return std::make_unique<ygo_gym::Engine>(
                    card_database,
                    std::move(roots),
                    std::move(cards)
                );
            }),
            py::arg("card_database"),
            py::arg("script_roots"),
            py::arg("card_definitions")
        )
        .def_property_readonly("core_version", &ygo_gym::Engine::core_version)
        .def(
            "create_duel",
            &ygo_gym::Engine::create_duel,
            py::arg("seed"),
            py::arg("player1_main"),
            py::arg("player1_extra"),
            py::arg("player2_main"),
            py::arg("player2_extra")
        );
}
