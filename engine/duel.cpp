#include "duel.h"

#include <stdexcept>
#include <utility>
#include "ocgapi_constants.h"
#include "event/decoder.h"
#include "protocol/decoder.h"

namespace ygo_gym {

std::array<float, 2> Outcome::rewards() const noexcept {
    if(!winner)
        return {0.0f, 0.0f};
    return *winner == 0 ? std::array<float, 2>{1.0f, -1.0f} : std::array<float, 2>{-1.0f, 1.0f};
}

Duel::~Duel() {
    close();
}

void Duel::close() noexcept {
    if(duel_ != nullptr) {
        OCG_DestroyDuel(duel_);
        duel_ = nullptr;
    }
    status_ = OCG_DUEL_STATUS_END;
    decision_.reset();
    action_state_.reset();
    observation_.reset();
    transition_events_ = {};
}

bool Duel::closed() const noexcept {
    return duel_ == nullptr;
}

bool Duel::terminated() const noexcept {
    return terminated_;
}

std::optional<std::uint8_t> Duel::current_player() const noexcept {
    if(terminated_ || !decision_)
        return std::nullopt;
    return protocol::player(*decision_);
}

const std::optional<Outcome>& Duel::outcome() const noexcept {
    return outcome_;
}

std::array<float, 2> Duel::rewards() const noexcept {
    return outcome_ ? outcome_->rewards() : std::array<float, 2>{0.0f, 0.0f};
}

int Duel::status() const noexcept {
    return status_;
}

const std::vector<std::uint8_t>& Duel::message_buffer() const noexcept {
    return message_buffer_;
}

const std::optional<protocol::Decision>& Duel::decision() const noexcept {
    return decision_;
}

const std::vector<action::Action>& Duel::actions() const noexcept {
    static const std::vector<action::Action> empty;
    return action_state_ ? action_state_->actions() : empty;
}

const std::vector<action::Action>& Duel::pending_actions() const noexcept {
    static const std::vector<action::Action> empty;
    return action_state_ ? action_state_->pending_actions() : empty;
}

void Duel::respond(const protocol::Response& response) {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    if(status_ != OCG_DUEL_STATUS_AWAITING || !decision_)
        throw std::runtime_error("duel is not awaiting a response");
    if(response.kind != protocol::kind(*decision_))
        throw std::invalid_argument("response does not match the current decision");
    submit_response(response, false);
}

void Duel::step(std::uint32_t action_index) {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    if(status_ != OCG_DUEL_STATUS_AWAITING || !action_state_)
        throw std::runtime_error("duel has no legal action to step");
    if(auto response = action_state_->step(action_index)) {
        submit_response(*response, true);
    } else if(observation_) {
        auto storage = std::make_shared<state::ObservationStorage>(*observation_->storage());
        storage->pending_actions = action_state_->pending_actions();
        storage->events = event::Batch{};
        observation_.emplace(state::Observation{std::move(storage)});
        transition_events_ = {};
    }
}

void Duel::process_until_blocked() {
    message_buffer_.clear();
    do {
        status_ = OCG_DuelProcess(duel_);
        std::uint32_t length = 0;
        const auto* buffer = static_cast<const std::uint8_t*>(OCG_DuelGetMessage(duel_, &length));
        if(length != 0)
            message_buffer_.insert(message_buffer_.end(), buffer, buffer + length);
        throw_script_errors("processing duel");
    } while(status_ == OCG_DUEL_STATUS_CONTINUE);
    transition_events_ = event::decode(message_buffer_);
    update_outcome();
}

void Duel::submit_response(const protocol::Response& response, bool semantic_action) {
    OCG_DuelSetResponse(duel_, response.data.data(), static_cast<std::uint32_t>(response.data.size()));
    process_until_blocked();
    if(protocol::contains_retry(message_buffer_)) {
        if(semantic_action)
            throw std::runtime_error("generated semantic action was rejected by ocgcore");
        throw std::invalid_argument("ocgcore rejected the response");
    }
    update_decision();
}

void Duel::update_outcome() {
    for(const auto& value : transition_events_.events) {
        if(const auto* win = std::get_if<event::WinEvent>(&value)) {
            outcome_ = Outcome{win->winner, win->reason};
            terminated_ = true;
        }
    }
}

void Duel::update_decision() {
    if(status_ == OCG_DUEL_STATUS_END) {
        terminated_ = true;
        if(!outcome_)
            throw std::runtime_error("ocgcore ended the duel without a win event");
        decision_.reset();
        action_state_.reset();
        observation_.reset();
        return;
    }
    if(status_ != OCG_DUEL_STATUS_AWAITING)
        throw std::runtime_error("ocgcore stopped with an unexpected duel status");
    auto decision = protocol::decode_decision(message_buffer_);
    if(!decision)
        throw std::runtime_error("ocgcore is awaiting input without a supported decision message");
    decision_ = std::move(decision);
    observation_.emplace(state::build_observation(duel_, protocol::player(*decision_), &*decision_, transition_events_));
    action_state_.emplace(*decision_, engine_, observation_->storage());
    observation_->storage()->pending_actions.clear();
}

}
