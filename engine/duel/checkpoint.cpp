#include "duel/duel.h"
#include <random>
#include <stdexcept>
#include <utility>
namespace ygo_gym {
struct Checkpoint::Data {
    struct Delete {
        void operator()(void *p) const noexcept {
            OCG_DestroyCheckpoint(p);
        }
    };
    std::unique_ptr<void, Delete> core;
    std::weak_ptr<int> owner;
    int status;
    std::vector<std::uint8_t> messages;
    protocol::Decision decision;
    event::Transition events;
    state::Observation observation;
    action::State actions;
    Data(std::unique_ptr<void, Delete> checkpoint, std::weak_ptr<int> identity, int value,
         std::vector<std::uint8_t> buffer, protocol::Decision prompt, event::Transition transition,
         state::Observation obs, action::State legal)
        : core(std::move(checkpoint)), owner(identity), status(value), messages(std::move(buffer)),
          decision(std::move(prompt)), events(std::move(transition)), observation(std::move(obs)),
          actions(std::move(legal)) {
    }
};
Checkpoint::Checkpoint(std::unique_ptr<Data> data) : data_(std::move(data)) {
}
Checkpoint::~Checkpoint() = default;
std::unique_ptr<Checkpoint> Duel::checkpoint() {
    if (closed())
        throw std::runtime_error("cannot checkpoint a closed duel");
    if (terminated_)
        throw std::runtime_error("cannot checkpoint a terminated duel");
    if (status_ != OCG_DUEL_STATUS_AWAITING || !decision_ || !action_state_ || !observation_)
        throw std::runtime_error("duel is not awaiting a decision");
    if (!script_errors_.empty())
        throw std::runtime_error("cannot checkpoint a duel with pending script errors");
    auto frozen = state::clone_observation(*observation_, duel_);
    auto actions = action_state_->clone(frozen.storage());
    OCG_Checkpoint raw = nullptr;
    const int status = OCG_CreateCheckpoint(&raw, duel_);
    std::unique_ptr<void, Checkpoint::Data::Delete> guard(raw);
    if (status == OCG_CHECKPOINT_ALLOCATION_FAILED)
        throw std::bad_alloc();
    throw_script_errors("capturing checkpoint");
    if (status != OCG_CHECKPOINT_SUCCESS)
        throw std::runtime_error("ocgcore could not capture the awaiting duel (status " +
                                 std::to_string(status) + ")");
    auto data = std::make_unique<Checkpoint::Data>(std::move(guard), checkpoint_identity_, status_,
                                                   message_buffer_, *decision_, transition_events_,
                                                   std::move(frozen), std::move(actions));
    return std::unique_ptr<Checkpoint>(new Checkpoint(std::move(data)));
}
void Duel::restore(const Checkpoint &checkpoint, bool preserve_rng,
                   std::optional<std::uint64_t> seed) {
    if (preserve_rng && seed)
        throw std::invalid_argument("seed and preserve_rng=True cannot be combined");
    if (closed())
        throw std::runtime_error("cannot restore a closed duel");
    const auto &saved = *checkpoint.data_;
    if (saved.owner.expired() || saved.owner.lock() != checkpoint_identity_)
        throw std::invalid_argument("checkpoint belongs to a different or closed duel");
    if (!preserve_rng && !seed) {
        std::random_device entropy;
        std::uniform_int_distribution<std::uint64_t> distribution;
        seed = distribution(entropy);
    }
    const int status = preserve_rng ? OCG_RestoreCheckpoint(duel_, saved.core.get())
                                    : OCG_RestoreCheckpointWithSeed(duel_, saved.core.get(), *seed);
    if (status == OCG_CHECKPOINT_WRONG_OWNER || status == OCG_CHECKPOINT_NOT_AWAITING ||
        status == OCG_CHECKPOINT_INVALID_ARGUMENT)
        throw std::invalid_argument("checkpoint cannot restore this duel at the current boundary");
    if (status != OCG_CHECKPOINT_SUCCESS) {
        close();
        if (status == OCG_CHECKPOINT_ALLOCATION_FAILED)
            throw std::bad_alloc();
        throw std::runtime_error("checkpoint reconstruction failed; the duel was closed");
    }
    try {
        status_ = saved.status;
        message_buffer_ = saved.messages;
        decision_ = saved.decision;
        transition_events_ = saved.events;
        observation_.emplace(state::clone_observation(saved.observation, duel_));
        action_state_.emplace(saved.actions.clone(observation_->storage()));
        terminated_ = false;
        outcome_.reset();
        script_errors_.clear();
    } catch (...) {
        close();
        throw;
    }
}
} // namespace ygo_gym
