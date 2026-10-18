#pragma once

#include <cstdint>
#include <memory>
#include <unordered_map>
#include <vector>

#include "action/action.h"
#include "state/observation.h"
#include "ygopro-core/ocgapi.h"
#include "protocol/decisions/decision.h"
#include "state/types.h"

namespace ygo_gym::state {

struct PlayerState {
    std::int32_t life_points{};
    std::int32_t starting_life_points{};
    std::int32_t starting_hand_size{};
    std::int32_t draw_count{};
    std::uint32_t used_locations{};
    std::uint32_t disabled_locations{};
    std::uint32_t faceup_extra_count{};
};

struct ZoneState {
    std::uint8_t player{};
    std::uint32_t location{};
    std::uint32_t begin{};
    std::uint32_t count{};
};

struct StateStorage {
    GlobalState global;
    std::uint64_t duel_options{};
    PlayerState players[2]{};
    std::vector<CardRecord> cards;
    std::vector<CardProperties> properties;
    std::vector<MonsterState> monsters;
    std::vector<PendulumState> pendulums;
    std::vector<LinkState> links;
    std::vector<ZoneState> zones;
    std::vector<std::uint32_t> zone_cards;
    std::vector<CounterState> counters;
    std::vector<RelationState> relations;
    std::vector<ChainState> chain;
    std::vector<std::uint32_t> chain_targets;
    std::vector<action::Action> pending_actions;
    event::Batch events;
    std::unordered_map<const void*, std::uint32_t> pointer_index;

    [[nodiscard]] std::uint32_t card_id(const protocol::CardRef& card, OCG_Duel duel) const;
};

class StateCardView {
public:
    StateCardView(std::shared_ptr<const StateStorage> storage, std::uint32_t id);

    [[nodiscard]] std::uint32_t id() const noexcept;
    [[nodiscard]] const CardRecord& card() const noexcept;
    [[nodiscard]] const CardProperties& properties() const noexcept;
    [[nodiscard]] const MonsterState* monster() const noexcept;
    [[nodiscard]] const PendulumState* pendulum() const noexcept;
    [[nodiscard]] const LinkState* link() const noexcept;

private:
    std::shared_ptr<const StateStorage> storage_;
    std::uint32_t id_;
};

class StateCardCollection {
public:
    explicit StateCardCollection(std::shared_ptr<const StateStorage> storage);
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] StateCardView at(std::size_t index) const;

private:
    std::shared_ptr<const StateStorage> storage_;
};

class State {
public:
    explicit State(std::shared_ptr<StateStorage> storage);

    [[nodiscard]] const GlobalState& global() const noexcept;
    [[nodiscard]] std::uint64_t duel_options() const noexcept;
    [[nodiscard]] const PlayerState& player(std::size_t index) const;
    [[nodiscard]] StateCardCollection cards() const;
    [[nodiscard]] const std::vector<ZoneState>& zones() const noexcept;
    [[nodiscard]] const std::vector<std::uint32_t>& zone_cards() const noexcept;
    [[nodiscard]] const std::vector<CounterState>& counters() const noexcept;
    [[nodiscard]] const std::vector<RelationState>& relations() const noexcept;
    [[nodiscard]] const std::vector<ChainState>& chain() const noexcept;
    [[nodiscard]] const std::vector<std::uint32_t>& chain_targets() const noexcept;
    [[nodiscard]] const std::vector<action::Action>& pending_actions() const noexcept;
    [[nodiscard]] const event::Batch& events() const noexcept;
    [[nodiscard]] std::shared_ptr<StateStorage> storage() const noexcept;

private:
    std::shared_ptr<StateStorage> storage_;
};

[[nodiscard]] State build_state(
    OCG_Duel duel,
    const protocol::Decision* decision,
    const std::vector<action::Action>& pending_actions,
    const ObservationStorage* observation,
    const event::Transition& events
);

}
