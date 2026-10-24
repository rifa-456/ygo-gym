#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <stdexcept>
#include <string>
#include <vector>

#include "action/action.h"
#include "protocol/decisions/decision.h"
#include "state/observation.h"

namespace ygo_gym::action {

using Matcher = std::function<bool(const Action&)>;

class InvalidChoice : public std::invalid_argument {
public:
    InvalidChoice(std::size_t step, const std::string& reason);
    [[nodiscard]] std::size_t step() const noexcept;

private:
    std::size_t step_;
};

struct Expansion {
    std::vector<std::uint32_t> indices;
    protocol::Response response;
};

[[nodiscard]] bool same(const Action& left, const Action& right);

[[nodiscard]] Expansion expand_prefix(const state::Observation& observation, const std::vector<Matcher>& steps);

[[nodiscard]] std::vector<std::uint32_t> expand(const state::Observation& observation, const std::vector<Action>& actions);

}
