#include "action/expansion.h"

#include <algorithm>
#include <type_traits>

#include "action/state.h"

namespace ygo_gym::action {
namespace {

template<typename T>
constexpr bool has_source = std::is_same_v<T, CardAction> || std::is_same_v<T, EffectAction> ||
    std::is_same_v<T, AttackAction> || std::is_same_v<T, TributeAction> || std::is_same_v<T, SumAction>;

std::uint32_t find(const State& state, const Matcher& matcher) {
    const auto& actions = state.actions();
    const auto found = std::find_if(actions.begin(), actions.end(), matcher);
    if(found == actions.end())
        return static_cast<std::uint32_t>(actions.size());
    return static_cast<std::uint32_t>(found - actions.begin());
}

State start(const state::Observation& observation) {
    const auto& storage = observation.storage();
    if(!storage->decision || !storage->engine)
        throw std::invalid_argument("observation has no decision to expand");
    State state(*storage->decision, storage->engine, storage);
    for(const auto& pending : observation.pending_actions()) {
        const auto index = find(state, [&pending](const Action& action) { return same(action, pending); });
        if(index == state.actions().size() || state.step(index))
            throw std::logic_error("observation pending actions do not replay");
    }
    return state;
}

}

InvalidChoice::InvalidChoice(std::size_t step, const std::string& reason)
    : std::invalid_argument("action " + std::to_string(step) + ": " + reason), step_(step) {}

std::size_t InvalidChoice::step() const noexcept {
    return step_;
}

bool same(const Action& left, const Action& right) {
    if(left.index() != right.index() || kind(left) != kind(right))
        return false;
    return std::visit([&right](const auto& value) {
        using T = std::decay_t<decltype(value)>;
        const auto& other = std::get<T>(right);
        if constexpr(has_source<T>)
            return value.source_index == other.source_index;
        else if constexpr(std::is_same_v<T, CounterAction>)
            return value.source_index == other.source_index && value.count == other.count;
        else if constexpr(std::is_same_v<T, ZoneAction>)
            return value.zone.player == other.zone.player && value.zone.location == other.zone.location &&
                value.zone.sequence == other.zone.sequence;
        else if constexpr(std::is_same_v<T, PositionAction>)
            return value.position == other.position;
        else if constexpr(std::is_same_v<T, OptionAction> || std::is_same_v<T, NumberAction>)
            return value.index == other.index;
        else if constexpr(std::is_same_v<T, RaceAction>)
            return value.race == other.race;
        else if constexpr(std::is_same_v<T, AttributeAction>)
            return value.attribute == other.attribute;
        else if constexpr(std::is_same_v<T, CardCodeAction>)
            return value.code == other.code;
        else if constexpr(std::is_same_v<T, RpsAction>)
            return value.choice == other.choice;
        else
            return true;
    }, left);
}

Expansion expand_prefix(const state::Observation& observation, const std::vector<Matcher>& steps) {
    auto state = start(observation);
    Expansion result;
    for(std::size_t step = 0; step < steps.size(); ++step) {
        const auto index = find(state, steps[step]);
        if(index == state.actions().size())
            throw InvalidChoice(step, "not legal after the previous actions");
        result.indices.push_back(index);
        if(auto response = state.step(index)) {
            result.response = std::move(*response);
            return result;
        }
    }
    throw InvalidChoice(steps.size(), "the decision is not complete");
}

std::vector<std::uint32_t> expand(const state::Observation& observation, const std::vector<Action>& actions) {
    std::vector<Matcher> steps;
    steps.reserve(actions.size() + 1);
    for(const auto& target : actions)
        steps.emplace_back([target](const Action& action) { return same(action, target); });
    Expansion result;
    try {
        result = expand_prefix(observation, steps);
    } catch(const InvalidChoice& error) {
        if(error.step() != actions.size())
            throw;
        steps.emplace_back([](const Action& action) { return kind(action) == ActionKind::confirm; });
        try {
            result = expand_prefix(observation, steps);
        } catch(const InvalidChoice&) {
            throw error;
        }
    }
    if(result.indices.size() < actions.size())
        throw InvalidChoice(result.indices.size(), "the decision is already complete");
    return result.indices;
}

}
