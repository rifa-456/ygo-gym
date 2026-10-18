#include "state/state.h"
#include "state/construction/full_state/builder.h"
#include "state/construction/card_lookup.h"
#include <stdexcept>
#include <utility>

namespace ygo_gym::state {

std::uint32_t StateStorage::card_id(const protocol::CardRef& ref, OCG_Duel duel) const {
    auto* value = resolve_card(static_cast<::duel*>(duel), ref);
    if(value == nullptr)
        throw std::runtime_error("ocgcore card reference cannot be resolved in full state");
    const auto found = pointer_index.find(value);
    if(found == pointer_index.end())
        throw std::runtime_error("resolved ocgcore card is absent from full state");
    return found->second;
}

StateCardView::StateCardView(std::shared_ptr<const StateStorage> storage, std::uint32_t id)
    : storage_(std::move(storage)), id_(id) {}
std::uint32_t StateCardView::id() const noexcept { return id_; }
const CardRecord& StateCardView::card() const noexcept { return storage_->cards[id_]; }
const CardProperties& StateCardView::properties() const noexcept {
    return storage_->properties[card().properties_index];
}
const MonsterState* StateCardView::monster() const noexcept {
    return card().monster_index == invalid_index ? nullptr : &storage_->monsters[card().monster_index];
}
const PendulumState* StateCardView::pendulum() const noexcept {
    return card().pendulum_index == invalid_index ? nullptr : &storage_->pendulums[card().pendulum_index];
}
const LinkState* StateCardView::link() const noexcept {
    return card().link_index == invalid_index ? nullptr : &storage_->links[card().link_index];
}

StateCardCollection::StateCardCollection(std::shared_ptr<const StateStorage> storage) : storage_(std::move(storage)) {}
std::size_t StateCardCollection::size() const noexcept { return storage_->cards.size(); }
StateCardView StateCardCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("state card index is out of range");
    return StateCardView{storage_, static_cast<std::uint32_t>(index)};
}

State::State(std::shared_ptr<StateStorage> storage) : storage_(std::move(storage)) {}
const GlobalState& State::global() const noexcept { return storage_->global; }
std::uint64_t State::duel_options() const noexcept { return storage_->duel_options; }
const PlayerState& State::player(std::size_t index) const {
    if(index > 1)
        throw std::out_of_range("player index is out of range");
    return storage_->players[index];
}
StateCardCollection State::cards() const { return StateCardCollection{storage_}; }
const std::vector<ZoneState>& State::zones() const noexcept { return storage_->zones; }
const std::vector<std::uint32_t>& State::zone_cards() const noexcept { return storage_->zone_cards; }
const std::vector<CounterState>& State::counters() const noexcept { return storage_->counters; }
const std::vector<RelationState>& State::relations() const noexcept { return storage_->relations; }
const std::vector<ChainState>& State::chain() const noexcept { return storage_->chain; }
const std::vector<std::uint32_t>& State::chain_targets() const noexcept { return storage_->chain_targets; }
const std::vector<action::Action>& State::pending_actions() const noexcept { return storage_->pending_actions; }
const event::Batch& State::events() const noexcept { return storage_->events; }
std::shared_ptr<StateStorage> State::storage() const noexcept { return storage_; }

State build_state(
    OCG_Duel duel,
    const protocol::Decision* decision,
    const std::vector<action::Action>& pending_actions,
    const ObservationStorage* observation,
    const event::Transition& events
) {
    auto state = StateBuilder{static_cast<::duel*>(duel)}.build(decision, pending_actions, observation);
    state.storage()->events = event::full(events, *state.storage());
    return state;
}

}
