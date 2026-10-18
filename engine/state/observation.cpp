#include "observation.h"
#include "observation_builder.h"
#include "card_lookup.h"
#include <stdexcept>
#include <utility>

namespace ygo_gym::state {

std::size_t CardLocatorHash::operator()(const CardLocator& value) const noexcept {
    std::size_t hash = value.controller;
    hash = hash * 1315423911u + value.location;
    hash = hash * 1315423911u + value.sequence;
    hash = hash * 1315423911u + value.overlay_sequence;
    return hash;
}

std::uint32_t ObservationStorage::card_id(const protocol::CardRef& card) const {
    const auto found = card_index.find(locator(card));
    if(found == card_index.end())
        throw std::runtime_error("semantic action references a card absent from the observation");
    return found->second;
}

CardView::CardView(std::shared_ptr<const ObservationStorage> storage, std::uint32_t id)
    : storage_(std::move(storage)), id_(id) {}

const CardRecord& CardView::record() const noexcept { return storage_->cards[id_]; }
std::uint32_t CardView::id() const noexcept { return id_; }
std::uint32_t CardView::code() const noexcept { return record().code; }
std::uint8_t CardView::owner() const noexcept { return record().owner; }
std::uint8_t CardView::controller() const noexcept { return record().controller; }
std::uint32_t CardView::location() const noexcept { return record().location; }
std::uint32_t CardView::sequence() const noexcept { return record().sequence; }
std::uint32_t CardView::position() const noexcept { return record().position; }

const CardProperties* CardView::properties() const noexcept {
    return record().properties_index == invalid_index ? nullptr : &storage_->properties[record().properties_index];
}
const MonsterState* CardView::monster() const noexcept {
    return record().monster_index == invalid_index ? nullptr : &storage_->monsters[record().monster_index];
}
const PendulumState* CardView::pendulum() const noexcept {
    return record().pendulum_index == invalid_index ? nullptr : &storage_->pendulums[record().pendulum_index];
}
const LinkState* CardView::link() const noexcept {
    return record().link_index == invalid_index ? nullptr : &storage_->links[record().link_index];
}

CardCollection::CardCollection(std::shared_ptr<const ObservationStorage> storage) : storage_(std::move(storage)) {}
std::size_t CardCollection::size() const noexcept { return storage_->cards.size(); }
CardView CardCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("card index is out of range");
    return CardView{storage_, static_cast<std::uint32_t>(index)};
}

Observation::Observation(std::shared_ptr<ObservationStorage> storage) : storage_(std::move(storage)) {}
std::uint8_t Observation::viewer() const noexcept { return storage_->viewer; }
const GlobalState& Observation::global() const noexcept { return storage_->global; }
CardCollection Observation::cards() const { return CardCollection{storage_}; }
const std::vector<ZoneCount>& Observation::zone_counts() const noexcept { return storage_->zone_counts; }
const std::vector<CounterState>& Observation::counters() const noexcept { return storage_->counters; }
const std::vector<RelationState>& Observation::relations() const noexcept { return storage_->relations; }
const std::vector<ChainState>& Observation::chain() const noexcept { return storage_->chain; }
const std::vector<std::uint32_t>& Observation::chain_targets() const noexcept { return storage_->chain_targets; }
const std::vector<action::Action>& Observation::pending_actions() const noexcept { return storage_->pending_actions; }
const event::Batch& Observation::events() const noexcept { return storage_->events; }
std::shared_ptr<ObservationStorage> Observation::storage() const noexcept { return storage_; }

Observation build_observation(OCG_Duel duel, std::uint8_t viewer, const protocol::Decision* decision, const event::Transition& events) {
    if(viewer > 1)
        throw std::invalid_argument("viewer must be player 0 or 1");
    return ObservationBuilder{static_cast<::duel*>(duel), viewer, decision}.build(events);
}

}
