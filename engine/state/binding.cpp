#include "binding.h"

namespace ygo_gym::state {

void bind_state(pybind11::module_& module) {
    bind_enums(module);
    bind_components(module);
    bind_observation(module);
    bind_full_state(module);
}

}
