#include "event/event.h"

#include <stdexcept>

#include "state/observation.h"
#include "state/state.h"
#include "state/types.h"

namespace ygo_gym::event {
namespace {

std::optional<std::uint32_t> observation_card(const state::ObservationStorage& storage, const Locator& locator) {
    const auto found = storage.card_index.find(state::CardLocator{
        locator.controller, locator.location, locator.sequence, state::invalid_index,
    });
    if(found == storage.card_index.end())
        return std::nullopt;
    return found->second;
}

std::optional<std::uint32_t> state_card(const state::StateStorage& storage, const Locator& locator) {
    for(std::uint32_t id = 0; id < storage.cards.size(); ++id) {
        const auto& card = storage.cards[id];
        if(card.controller == locator.controller && card.location == locator.location && card.sequence == locator.sequence)
            return id;
    }
    return std::nullopt;
}

template<typename Resolve, typename Code>
Batch make_batch(const Transition& transition, Resolve resolve, Code code) {
    auto storage = std::make_shared<BatchStorage>();
    storage->cards.reserve(transition.cards.size());
    for(const auto& card : transition.cards) {
        const auto current_card = card.current ? resolve(*card.current) : std::nullopt;
        storage->cards.push_back(EventCardRecord{
            code(card, current_card),
            current_card,
        });
    }
    storage->events = transition.events;
    return Batch{std::move(storage)};
}

}

EventCardView::EventCardView(std::shared_ptr<const BatchStorage> storage, std::uint32_t id)
    : storage_(std::move(storage)), id_(id) {}
std::uint32_t EventCardView::id() const noexcept { return id_; }
std::uint32_t EventCardView::code() const noexcept { return storage_->cards[id_].code; }
const std::optional<std::uint32_t>& EventCardView::current_card() const noexcept { return storage_->cards[id_].current_card; }

EventCardCollection::EventCardCollection(std::shared_ptr<const BatchStorage> storage) : storage_(std::move(storage)) {}
std::size_t EventCardCollection::size() const noexcept { return storage_->cards.size(); }
EventCardView EventCardCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("event card index is out of range");
    return EventCardView{storage_, static_cast<std::uint32_t>(index)};
}

EventCollection::EventCollection(std::shared_ptr<const BatchStorage> storage) : storage_(std::move(storage)) {}
std::size_t EventCollection::size() const noexcept { return storage_->events.size(); }
const Event& EventCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("event index is out of range");
    return storage_->events[index];
}

Batch::Batch() : storage_(std::make_shared<BatchStorage>()) {}
Batch::Batch(std::shared_ptr<BatchStorage> storage) : storage_(std::move(storage)) {}
EventCardCollection Batch::cards() const { return EventCardCollection{storage_}; }
EventCollection Batch::events() const { return EventCollection{storage_}; }
std::size_t Batch::size() const noexcept { return storage_->events.size(); }
std::shared_ptr<BatchStorage> Batch::storage() const noexcept { return storage_; }

Batch project(const Transition& transition, std::uint8_t viewer, const state::ObservationStorage& observation) {
    if(viewer > 1)
        throw std::invalid_argument("viewer must be player 0 or 1");
    const auto bit = static_cast<std::uint8_t>(1u << viewer);
    return make_batch(
        transition,
        [&](const Locator& locator) { return observation_card(observation, locator); },
        [&](const RawCard& card, const std::optional<std::uint32_t>& current_card) {
            if((card.visible_to & bit) == 0)
                return state::unknown_card;
            if(card.code != 0)
                return card.code;
            return current_card ? observation.cards[*current_card].code : state::unknown_card;
        }
    );
}

Batch full(const Transition& transition, const state::StateStorage& state) {
    return make_batch(
        transition,
        [&](const Locator& locator) { return state_card(state, locator); },
        [&](const RawCard& card, const std::optional<std::uint32_t>& current_card) {
            if(card.code != 0)
                return card.code;
            return current_card ? state.cards[*current_card].code : state::unknown_card;
        }
    );
}

}
