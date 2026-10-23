#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <variant>
#include <vector>

namespace ygo_gym::state {
struct ObservationStorage;
struct StateStorage;
}

namespace ygo_gym::event {

constexpr std::uint32_t no_card = 0xffffffffu;

enum class SummonKind : std::uint8_t { normal, special, flip };
enum class SummonStage : std::uint8_t { attempt, complete };
enum class ChainStage : std::uint8_t { activating, added, resolving, resolved, negated, disabled, ended };
enum class LifePointKind : std::uint8_t { damage, recover, pay, set };
enum class RelationEventKind : std::uint8_t { equip, unequip, target, cancel_target };
enum class RandomKind : std::uint8_t { coin, dice };
enum class DamageStepStage : std::uint8_t { start, end };

struct Locator {
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    std::uint32_t position{};
};

struct EventCardRecord {
    std::uint32_t code{};
    std::optional<std::uint32_t> current_card;
};

struct TurnEvent { std::uint8_t player{}; };
struct PhaseEvent { std::uint16_t phase{}; };
struct ShuffleEvent { std::uint8_t player{}; std::uint32_t location{}; };
struct RevealEvent { std::uint32_t card{}; };
struct DrawEvent { std::uint8_t player{}; std::uint32_t card{}; };
struct MoveEvent {
    std::uint32_t card{};
    Locator previous;
    Locator current;
    std::uint32_t reason{};
};
struct PositionEvent {
    std::uint32_t card{};
    std::uint8_t controller{};
    std::uint32_t location{};
    std::uint32_t sequence{};
    std::uint32_t previous_position{};
    std::uint32_t position{};
};
struct SetEvent { std::uint32_t card{}; };
struct SummonEvent {
    std::uint32_t card{};
    std::uint8_t player{};
    SummonKind kind{};
    SummonStage stage{};
};
struct ChainEvent {
    ChainStage stage{};
    std::optional<std::uint32_t> card;
    std::optional<std::uint8_t> player;
    std::optional<std::uint64_t> description;
    std::optional<std::uint32_t> chain_index;
};
struct LifePointEvent {
    std::uint8_t player{};
    std::uint32_t amount{};
    LifePointKind kind{};
};
struct CounterEvent {
    std::uint32_t card{};
    std::uint16_t type{};
    std::int32_t change{};
};
struct RelationEvent {
    RelationEventKind kind{};
    std::uint32_t source{};
    std::uint32_t target{};
};
struct AttackEvent {
    std::uint32_t attacker{};
    std::optional<std::uint32_t> target;
};
struct BattleEvent {
    std::uint32_t attacker{};
    std::int32_t attacker_attack{};
    std::int32_t attacker_defense{};
    bool attacker_destroyed{};
    std::optional<std::uint32_t> target;
    std::int32_t target_attack{};
    std::int32_t target_defense{};
    bool target_destroyed{};
};
struct RandomEvent {
    std::uint8_t player{};
    RandomKind kind{};
    std::vector<std::uint8_t> results;
};
struct DamageStepEvent { DamageStepStage stage{}; };
struct GraveDeckSwapEvent { std::uint8_t player{}; };
struct DeckReverseEvent {};
struct MatchKillEvent { std::uint32_t code{}; };
struct WinEvent { std::optional<std::uint8_t> winner; std::uint8_t reason{}; };

using Event = std::variant<
    TurnEvent, PhaseEvent, ShuffleEvent, RevealEvent, DrawEvent, MoveEvent,
    PositionEvent, SetEvent, SummonEvent, ChainEvent, LifePointEvent,
    CounterEvent, RelationEvent, AttackEvent, BattleEvent, RandomEvent,
    DamageStepEvent, GraveDeckSwapEvent, DeckReverseEvent, WinEvent, MatchKillEvent
>;

struct RawCard {
    std::uint32_t code{};
    std::uint8_t visible_to{0x3};
    std::optional<Locator> current;
};

struct Transition {
    std::vector<RawCard> cards;
    std::vector<Event> events;
};

struct BatchStorage {
    std::vector<EventCardRecord> cards;
    std::vector<Event> events;
};

class EventCardView {
public:
    EventCardView(std::shared_ptr<const BatchStorage> storage, std::uint32_t id);
    [[nodiscard]] std::uint32_t id() const noexcept;
    [[nodiscard]] std::uint32_t code() const noexcept;
    [[nodiscard]] const std::optional<std::uint32_t>& current_card() const noexcept;
private:
    std::shared_ptr<const BatchStorage> storage_;
    std::uint32_t id_{};
};

class EventCardCollection {
public:
    explicit EventCardCollection(std::shared_ptr<const BatchStorage> storage);
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] EventCardView at(std::size_t index) const;
private:
    std::shared_ptr<const BatchStorage> storage_;
};

class EventCollection {
public:
    explicit EventCollection(std::shared_ptr<const BatchStorage> storage);
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] const Event& at(std::size_t index) const;
private:
    std::shared_ptr<const BatchStorage> storage_;
};

class Batch {
public:
    Batch();
    explicit Batch(std::shared_ptr<BatchStorage> storage);
    [[nodiscard]] EventCardCollection cards() const;
    [[nodiscard]] EventCollection events() const;
    [[nodiscard]] std::size_t size() const noexcept;
    [[nodiscard]] std::shared_ptr<BatchStorage> storage() const noexcept;
private:
    std::shared_ptr<BatchStorage> storage_;
};

[[nodiscard]] Batch project(const Transition& transition, std::uint8_t viewer, const state::ObservationStorage& observation);
[[nodiscard]] Batch full(const Transition& transition, const state::StateStorage& state);

}
