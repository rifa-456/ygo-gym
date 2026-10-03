#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <variant>
#include <vector>

#include "action.h"
#include "engine.h"
#include "protocol/decision.h"

namespace ygo_gym::action {

class State {
public:
    State(protocol::Decision decision, std::shared_ptr<const EngineState> engine);

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

    [[nodiscard]] std::optional<protocol::Response> apply(const Action& action);

    protocol::Decision decision_;
    std::shared_ptr<const EngineState> engine_;
    Selection selection_;
    std::vector<Action> actions_;
    std::vector<Action> pending_actions_;
};

}
