#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "backend.h"

namespace py = pybind11;

PYBIND11_MODULE(_native, module) {
    py::class_<ygo_gym::Duel>(module, "Duel")
        .def("close", &ygo_gym::Duel::close)
        .def_property_readonly("closed", &ygo_gym::Duel::closed);

    py::class_<ygo_gym::Backend>(module, "Backend")
        .def(
            py::init([](const std::string& card_database, const std::vector<std::string>& script_roots) {
                std::vector<std::filesystem::path> roots;
                roots.reserve(script_roots.size());
                for(const auto& root : script_roots)
                    roots.emplace_back(root);
                return std::make_unique<ygo_gym::Backend>(card_database, std::move(roots));
            }),
            py::arg("card_database"),
            py::arg("script_roots")
        )
        .def_property_readonly("core_version", &ygo_gym::Backend::core_version)
        .def("create_duel", &ygo_gym::Backend::create_duel, py::arg("seed"));
}
