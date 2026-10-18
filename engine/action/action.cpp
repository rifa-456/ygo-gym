#include "action/action.h"

namespace ygo_gym::action {

ActionKind kind(const Action& action) noexcept {
    return std::visit([](const auto& value) { return value.kind; }, action);
}

}
