#include "action/state.h"

namespace ygo_gym::action {

void State::rebuild_actions() {
    actions_.clear();
    std::visit([this](const auto& decision) { add_candidates(decision); }, decision_);
}

}
