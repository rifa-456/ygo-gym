#include "protocol/bindings/register.h"

namespace ygo_gym::protocol {

void bind_protocol(pybind11::module_& module) {
    bind_enums(module);
    bind_references(module);
    bind_commands(module);
    bind_selection(module);
    bind_announcement(module);
}

}
