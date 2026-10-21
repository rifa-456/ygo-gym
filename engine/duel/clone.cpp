#include "duel/duel.h"

#include <new>
#include <random>
#include <stdexcept>
#include <utility>

namespace ygo_gym {

Duel::Duel(std::shared_ptr<const EngineState> engine) : engine_(std::move(engine)) {}

std::unique_ptr<Duel> Duel::clone(bool preserve_rng, std::optional<std::uint64_t> seed) const {
    if(preserve_rng && seed)
        throw std::invalid_argument("seed and preserve_rng=True cannot be combined");
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
    if(!preserve_rng && !seed) {
        std::random_device entropy;
        std::uniform_int_distribution<std::uint64_t> distribution;
        seed = distribution(entropy);
    }
    const int status = preserve_rng
        ? OCG_CloneDuel(&result->duel_, duel_, &callbacks)
        : OCG_CloneDuelWithSeed(&result->duel_, duel_, &callbacks, *seed);
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
