#pragma once

#include <cstdint>
#include <memory>
#include <unordered_map>
#include <vector>

#include "action/action.h"
#include "client/capture.h"
#include "event/event.h"
#include "ygopro-core/ocgapi.h"
#include "protocol/decisions/decision.h"
#include "state/types.h"

class card;

namespace ygo_gym {
struct EngineState;
}

namespace ygo_gym::state {

struct CardLocator {
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    std::uint32_t overlay_sequence{invalid_index};

    bool operator==(const CardLocator& other) const noexcept {
        return controller == other.controller
            && location == other.location
            && sequence == other.sequence
            && overlay_sequence == other.overlay_sequence;
    }
};

struct CardLocatorHash {
    std::size_t operator()(const CardLocator& locator) const noexcept;
};

struct ObservationStorage {
    std::uint8_t viewer{};
    GlobalState global;
    std::vector<ZoneCount> zone_counts;
    std::vector<CardRecord> cards;
    std::vector<card*> core_cards;
    std::vector<std::uint32_t> core_card_ids;
    std::vector<CardProperties> properties;
    std::vector<MonsterState> monsters;
    std::vector<PendulumState> pendulums;
    std::vector<LinkState> links;
    std::vector<CounterState> counters;
    std::vector<RelationState> relations;
    std::vector<ChainState> chain;
    std::vector<std::uint32_t> chain_targets;
    std::vector<action::Action> pending_actions;
    event::Batch events;
    std::shared_ptr<const client::Batch> client_batch;
    std::optional<protocol::Decision> decision;
    std::shared_ptr<const EngineState> engine;
    std::unordered_map<CardLocator, std::uint32_t, CardLocatorHash> card_index;

    [[nodiscard]] std::uint32_t card_id(const protocol::CardRef& card) const;
};

class CardView {
public:
    CardView(std::shared_ptr<const ObservationStorage> storage, std::uint32_t id);

    [[nodiscard]] std::uint32_t id() const noexcept;
    [[nodiscard]] std::uint32_t code() const noexcept;
    [[nodiscard]] std::uint8_t owner() const noexcept;
    [[nodiscard]] std::uint8_t controller() const noexcept;
    [[nodiscard]] std::uint32_t location() const noexcept;
    [[nodiscard]] std::uint32_t sequence() const noexcept;
    [[nodiscard]] std::uint32_t position() const noexcept;
    [[nodiscard]] const CardProperties* properties() const noexcept;
    [[nodiscard]] const MonsterState* monster() const noexcept;
    [[nodiscard]] const PendulumState* pendulum() const noexcept;
    [[nodiscard]] const LinkState* link() const noexcept;

private:
    const CardRecord& record() const noexcept;
    std::shared_ptr<const ObservationStorage> storage_;
    std::uint32_t id_;
};

class CardCollection {
public:
    explicit CardCollection(std::shared_ptr<const ObservationStorage> storage);
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] CardView at(std::size_t index) const;

private:
    std::shared_ptr<const ObservationStorage> storage_;
};

class Observation {
public:
    explicit Observation(std::shared_ptr<ObservationStorage> storage);

    [[nodiscard]] std::uint8_t viewer() const noexcept;
    [[nodiscard]] const GlobalState& global() const noexcept;
    [[nodiscard]] CardCollection cards() const;
    [[nodiscard]] const std::vector<ZoneCount>& zone_counts() const noexcept;
    [[nodiscard]] const std::vector<CounterState>& counters() const noexcept;
    [[nodiscard]] const std::vector<RelationState>& relations() const noexcept;
    [[nodiscard]] const std::vector<ChainState>& chain() const noexcept;
    [[nodiscard]] const std::vector<std::uint32_t>& chain_targets() const noexcept;
    [[nodiscard]] const std::vector<action::Action>& pending_actions() const noexcept;
    [[nodiscard]] const event::Batch& events() const noexcept;
    [[nodiscard]] std::shared_ptr<ObservationStorage> storage() const noexcept;

private:
    std::shared_ptr<ObservationStorage> storage_;
};

[[nodiscard]] Observation clone_observation(const Observation& source, OCG_Duel target);

[[nodiscard]] Observation build_observation(
    OCG_Duel duel,
    std::uint8_t viewer,
    const protocol::Decision* decision,
    const event::Transition& events
);

}
