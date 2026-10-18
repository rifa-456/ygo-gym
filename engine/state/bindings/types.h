#pragma once

#include <cstddef>
#include <cstdint>
#include <stdexcept>

#include <pybind11/stl.h>

#include "state/observation.h"
#include "state/state.h"

namespace py = pybind11;

namespace ygo_gym::state {

template<typename T>
void public_type(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.state";
}

template<typename T>
py::object optional_component(const T* value) {
    if(value == nullptr)
        return py::none();
    return py::cast(*value);
}

inline std::size_t normalize_index(py::ssize_t index, std::size_t size) {
    if(index < 0)
        index += static_cast<py::ssize_t>(size);
    if(index < 0 || static_cast<std::size_t>(index) >= size)
        throw py::index_error("index out of range");
    return static_cast<std::size_t>(index);
}

template<typename Storage>
py::tuple slice_ids(const Storage& values, std::uint32_t begin, std::uint32_t count) {
    py::tuple result(count);
    for(std::uint32_t index = 0; index < count; ++index)
        result[index] = values[begin + index];
    return result;
}

}
