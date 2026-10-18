#pragma once

#include <pybind11/pybind11.h>

namespace ygo_gym::state {

void bind_state(pybind11::module_& module);

}
