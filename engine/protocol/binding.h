#pragma once

#include <pybind11/pybind11.h>

namespace ygo_gym::protocol {

void bind_protocol(pybind11::module_& module);

}
