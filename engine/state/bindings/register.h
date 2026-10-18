#pragma once

#include <pybind11/pybind11.h>

namespace ygo_gym::state {

void bind_enums(pybind11::module_& module);
void bind_components(pybind11::module_& module);
void bind_observation(pybind11::module_& module);
void bind_full_state(pybind11::module_& module);
void bind_state(pybind11::module_& module);

}
