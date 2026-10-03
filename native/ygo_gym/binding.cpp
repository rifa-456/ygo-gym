#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "backend.h"
#include "duel.h"

namespace py = pybind11;

namespace {

using CardRow = std::tuple<
    std::uint32_t,
    std::uint32_t,
    std::vector<std::uint16_t>,
    std::uint32_t,
    std::uint32_t,
    std::uint32_t,
    std::uint64_t,
    std::int32_t,
    std::int32_t,
    std::uint32_t,
    std::uint32_t,
    std::uint32_t
>;

ygo_gym::CardDefinition to_card_definition(CardRow row) {
    return ygo_gym::CardDefinition{
        std::get<0>(row),
        std::get<1>(row),
        std::move(std::get<2>(row)),
        std::get<3>(row),
        std::get<4>(row),
        std::get<5>(row),
        std::get<6>(row),
        std::get<7>(row),
        std::get<8>(row),
        std::get<9>(row),
        std::get<10>(row),
        std::get<11>(row),
    };
}

}

PYBIND11_MODULE(_native, module) {
    py::class_<ygo_gym::Duel>(module, "Duel")
        .def("close", &ygo_gym::Duel::close)
        .def_property_readonly("closed", &ygo_gym::Duel::closed)
        .def_property_readonly("status", &ygo_gym::Duel::status)
        .def_property_readonly("message_buffer", [](const ygo_gym::Duel& duel) {
            const auto& buffer = duel.message_buffer();
            return py::bytes(reinterpret_cast<const char*>(buffer.data()), buffer.size());
        });

    py::class_<ygo_gym::Backend>(module, "Backend")
        .def(
            py::init([](
                const std::string& card_database,
                const std::vector<std::string>& script_roots,
                std::vector<CardRow> card_rows
            ) {
                std::vector<std::filesystem::path> roots;
                roots.reserve(script_roots.size());
                for(const auto& root : script_roots)
                    roots.emplace_back(root);

                std::vector<ygo_gym::CardDefinition> cards;
                cards.reserve(card_rows.size());
                for(auto& row : card_rows)
                    cards.push_back(to_card_definition(std::move(row)));

                return std::make_unique<ygo_gym::Backend>(
                    card_database,
                    std::move(roots),
                    std::move(cards)
                );
            }),
            py::arg("card_database"),
            py::arg("script_roots"),
            py::arg("card_rows")
        )
        .def_property_readonly("core_version", &ygo_gym::Backend::core_version)
        .def(
            "create_duel",
            &ygo_gym::Backend::create_duel,
            py::arg("seed"),
            py::arg("player1_main"),
            py::arg("player1_extra"),
            py::arg("player2_main"),
            py::arg("player2_extra")
        );
}
