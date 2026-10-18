#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "protocol/decisions/decision.h"

namespace py = pybind11;

namespace ygo_gym::protocol {

template<typename T>
void set_public_module(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.protocol";
}

}
