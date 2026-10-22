#include "action/state.h"

#include <stdexcept>
#include <type_traits>
#include <utility>

namespace ygo_gym::action {

State::State(
    protocol::Decision decision,
    std::shared_ptr<const EngineState> engine,
    std::shared_ptr<const state::ObservationStorage> observation
) : decision_(std::move(decision)), engine_(std::move(engine)), observation_(std::move(observation)) {
    initialize_selection();
    rebuild_actions();
}

State State::clone(std::shared_ptr<const state::ObservationStorage> observation) const {
    State result(*this);
    result.observation_ = std::move(observation);
    return result;
}

const std::vector<std::uint32_t>& State::selection_indices() const noexcept {
    return selection_indices_;
}

const protocol::Decision& State::decision() const noexcept {
    return decision_;
}

const std::vector<Action>& State::actions() const noexcept {
    return actions_;
}

const std::vector<Action>& State::pending_actions() const noexcept {
    return pending_actions_;
}

std::optional<protocol::Response> State::step(std::uint32_t action_index) {
    if(action_index >= actions_.size())
        throw std::invalid_argument("action index is out of range");
    const auto chosen = actions_[action_index];
    auto response = apply(chosen);
    if(!response) {
        selection_indices_.push_back(action_index);
        pending_actions_.push_back(chosen);
        rebuild_actions();
        if(actions_.empty())
            throw std::runtime_error("semantic action selection reached a dead end");
    }
    return response;
}

void State::initialize_selection() {
    std::visit([this](const auto& decision) {
        using T = std::decay_t<decltype(decision)>;
        if constexpr(std::is_same_v<T, protocol::CardDecision>) {
            if(decision.max > 1)
                selection_ = CardSelection{};
        } else if constexpr(std::is_same_v<T, protocol::PlaceDecision>) {
            if(decision.count > 1)
                selection_ = ZoneSelection{};
        } else if constexpr(std::is_same_v<T, protocol::TributeDecision>) {
            if(decision.max > 1)
                selection_ = CardSelection{};
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            if(decision.count > 1) {
                selection_ = CounterSelection{
                    std::vector<std::uint16_t>(decision.cards.size(), 0),
                    std::vector<bool>(decision.cards.size(), false),
                    0,
                };
            }
        } else if constexpr(std::is_same_v<T, protocol::SumDecision>) {
            selection_ = CardSelection{};
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            if(decision.cards.size() > 1)
                selection_ = SortSelection{{}, std::vector<bool>(decision.cards.size(), false)};
        } else if constexpr(std::is_same_v<T, protocol::AnnounceRaceDecision>) {
            if(decision.count > 1)
                selection_ = BitSelection{};
        } else if constexpr(std::is_same_v<T, protocol::AnnounceAttributeDecision>) {
            if(decision.count > 1)
                selection_ = BitSelection{};
        }
    }, decision_);
}

}
