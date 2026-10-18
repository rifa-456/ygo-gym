#pragma once

#include <cstddef>
#include <type_traits>

#include <pybind11/stl.h>

#include "event/event.h"
#include "state/types.h"

namespace py = pybind11;

namespace ygo_gym::event {

template<typename T>
void public_type(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.event";
}

inline std::size_t normalize_index(py::ssize_t index, std::size_t size) {
    if(index < 0)
        index += static_cast<py::ssize_t>(size);
    if(index < 0 || static_cast<std::size_t>(index) >= size)
        throw py::index_error("index out of range");
    return static_cast<std::size_t>(index);
}

inline py::object event_object(const Event& event) {
    return std::visit([](const auto& value) { return py::cast(value); }, event);
}

inline py::object optional_player(const std::optional<std::uint8_t>& player) {
    if(!player)
        return py::none();
    return py::cast(static_cast<state::Player>(*player));
}

}
