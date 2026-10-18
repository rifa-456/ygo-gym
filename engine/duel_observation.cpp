#include "duel.h"

#include <stdexcept>
#include <utility>
#include "ocgapi_constants.h"

namespace ygo_gym {

const state::Observation& Duel::observation() const {
    if(!observation_)
        throw std::runtime_error("duel has no current player observation");
    return *observation_;
}

state::Observation Duel::observe(std::uint8_t viewer) const {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    if(observation_ && viewer == observation_->viewer())
        return *observation_;
    auto result = state::build_observation(duel_, viewer, decision_ ? &*decision_ : nullptr, transition_events_);
    return result;
}

state::State Duel::state() const {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    return state::build_state(
        duel_,
        decision_ ? &*decision_ : nullptr,
        action_state_ ? action_state_->pending_actions() : std::vector<action::Action>{},
        observation_ ? observation_->storage().get() : nullptr,
        transition_events_
    );
}

}
