#pragma once

#include <pybind11/pybind11.h>

namespace ygo_gym::protocol {

void bind_enums(pybind11::module_& module);
void bind_references(pybind11::module_& module);
void bind_commands(pybind11::module_& module);
void bind_selection(pybind11::module_& module);
void bind_announcement(pybind11::module_& module);
void bind_protocol(pybind11::module_& module);

}
