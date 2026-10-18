#pragma once

#include <pybind11/pybind11.h>

namespace ygo_gym::action {

void bind_actions(pybind11::module_& module);

}
