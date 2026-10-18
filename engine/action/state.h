#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <variant>
#include <vector>

#include "action/action.h"
#include "engine.h"
#include "protocol/decisions/decision.h"
#include "state/observation.h"

namespace ygo_gym::action {

class State {
public:
    State(
        protocol::Decision decision,
        std::shared_ptr<const EngineState> engine,
        std::shared_ptr<const state::ObservationStorage> observation
    );

    [[nodiscard]] const protocol::Decision& decision() const noexcept;
    [[nodiscard]] const std::vector<Action>& actions() const noexcept;
    [[nodiscard]] const std::vector<Action>& pending_actions() const noexcept;
    [[nodiscard]] std::optional<protocol::Response> step(std::uint32_t action_index);

private:
    struct CardSelection {
        std::vector<std::uint32_t> indices;
    };

    struct ZoneSelection {
        std::vector<protocol::ZoneRef> zones;
    };

    struct CounterSelection {
        std::vector<std::uint16_t> counts;
        std::vector<bool> assigned;
        std::uint16_t total{0};
    };

    struct SortSelection {
        std::vector<std::uint8_t> order;
        std::vector<bool> selected;
    };

    struct BitSelection {
        std::uint64_t mask{0};
        std::uint8_t count{0};
    };

    using Selection = std::variant<
        std::monostate,
        CardSelection,
        ZoneSelection,
        CounterSelection,
        SortSelection,
        BitSelection
    >;

    void initialize_selection();
    void rebuild_actions();
    void add_candidates(const protocol::BattleDecision& decision);
    void add_candidates(const protocol::IdleDecision& decision);
    void add_candidates(const protocol::EffectYesNoDecision& decision);
    void add_candidates(const protocol::YesNoDecision& decision);
    void add_candidates(const protocol::OptionDecision& decision);
    void add_candidates(const protocol::CardDecision& decision);
    void add_candidates(const protocol::ChainDecision& decision);
    void add_candidates(const protocol::PlaceDecision& decision);
    void add_candidates(const protocol::PositionDecision& decision);
    void add_candidates(const protocol::TributeDecision& decision);
    void add_candidates(const protocol::CounterDecision& decision);
    void add_candidates(const protocol::SumDecision& decision);
    void add_candidates(const protocol::SortDecision& decision);
    void add_candidates(const protocol::UnselectCardDecision& decision);
    void add_candidates(const protocol::AnnounceRaceDecision& decision);
    void add_candidates(const protocol::AnnounceAttributeDecision& decision);
    void add_candidates(const protocol::AnnounceCardDecision& decision);
    void add_candidates(const protocol::AnnounceNumberDecision& decision);
    void add_candidates(const protocol::RockPaperScissorsDecision& decision);

    [[nodiscard]] std::optional<protocol::Response> apply(const Action& action);

    protocol::Decision decision_;
    std::shared_ptr<const EngineState> engine_;
    std::shared_ptr<const state::ObservationStorage> observation_;
    Selection selection_;
    std::vector<Action> actions_;
    std::vector<Action> pending_actions_;
};

}
