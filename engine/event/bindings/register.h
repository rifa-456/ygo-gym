#pragma once
#include <pybind11/pybind11.h>
namespace ygo_gym::event { void bind_enums(pybind11::module_& module);
void bind_cards(pybind11::module_& module);
void bind_movement(pybind11::module_& module);
void bind_battle(pybind11::module_& module);
void bind_batch(pybind11::module_& module);
void bind_events(pybind11::module_& module); }
