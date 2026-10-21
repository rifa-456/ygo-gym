#include "duel/duel.h"

#include <new>
#include <stdexcept>
#include <utility>

namespace ygo_gym {

Duel::Duel(std::shared_ptr<const EngineState> engine) : engine_(std::move(engine)) {}

std::unique_ptr<Duel> Duel::clone() const {
    if(closed())
        throw std::runtime_error("cannot clone a closed duel");
    if(terminated_)
        throw std::runtime_error("cannot clone a terminated duel");
    if(status_ != OCG_DUEL_STATUS_AWAITING || !decision_ || !action_state_ || !observation_)
        throw std::runtime_error("duel is not awaiting a decision");
    if(!script_errors_.empty())
        throw std::runtime_error("cannot clone a duel with pending script errors");

    auto result = std::unique_ptr<Duel>(new Duel(engine_));
    const OCG_CloneCallbacks callbacks{
        &Duel::read_card, result.get(),
        &Duel::read_script, result.get(),
        &Duel::handle_log, result.get(),
        nullptr, nullptr,
    };
    const int status = OCG_CloneDuel(&result->duel_, duel_, &callbacks);
    if(status == OCG_CLONE_ALLOCATION_FAILED)
        throw std::bad_alloc();
    result->throw_script_errors("cloning duel");
    if(status != OCG_CLONE_SUCCESS)
        throw std::runtime_error("ocgcore could not clone the awaiting duel (status " + std::to_string(status) + ")");

    result->status_ = status_;
    result->message_buffer_ = message_buffer_;
    result->decision_ = decision_;
    result->transition_events_ = transition_events_;
    result->observation_.emplace(state::clone_observation(*observation_, result->duel_));
    result->action_state_.emplace(action_state_->clone(result->observation_->storage()));
    return result;
}

}
