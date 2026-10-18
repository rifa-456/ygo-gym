#include "binding.h"

namespace ygo_gym::event {

void bind_events(pybind11::module_& module) {
    bind_enums(module);
    bind_cards(module);
    bind_movement(module);
    bind_battle(module);
    bind_batch(module);
}

}
