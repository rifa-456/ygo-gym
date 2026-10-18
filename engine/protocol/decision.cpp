#include "decision.h"
#include <type_traits>

namespace ygo_gym::protocol {

DecisionKind kind(const Decision& decision) noexcept {
    return std::visit([](const auto& value) -> DecisionKind {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, BattleDecision>) return DecisionKind::battle_command;
        if constexpr(std::is_same_v<T, IdleDecision>) return DecisionKind::idle_command;
        if constexpr(std::is_same_v<T, EffectYesNoDecision>) return DecisionKind::effect_yes_no;
        if constexpr(std::is_same_v<T, YesNoDecision>) return DecisionKind::yes_no;
        if constexpr(std::is_same_v<T, OptionDecision>) return DecisionKind::option;
        if constexpr(std::is_same_v<T, CardDecision>) return DecisionKind::card;
        if constexpr(std::is_same_v<T, ChainDecision>) return DecisionKind::chain;
        if constexpr(std::is_same_v<T, PlaceDecision>) return value.disable_field ? DecisionKind::disable_field : DecisionKind::place;
        if constexpr(std::is_same_v<T, PositionDecision>) return DecisionKind::position;
        if constexpr(std::is_same_v<T, TributeDecision>) return DecisionKind::tribute;
        if constexpr(std::is_same_v<T, CounterDecision>) return DecisionKind::counter;
        if constexpr(std::is_same_v<T, SumDecision>) return DecisionKind::sum;
        if constexpr(std::is_same_v<T, SortDecision>) return value.chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
        if constexpr(std::is_same_v<T, UnselectCardDecision>) return DecisionKind::unselect_card;
        if constexpr(std::is_same_v<T, AnnounceRaceDecision>) return DecisionKind::announce_race;
        if constexpr(std::is_same_v<T, AnnounceAttributeDecision>) return DecisionKind::announce_attribute;
        if constexpr(std::is_same_v<T, AnnounceCardDecision>) return DecisionKind::announce_card;
        if constexpr(std::is_same_v<T, AnnounceNumberDecision>) return DecisionKind::announce_number;
        return DecisionKind::rock_paper_scissors;
    }, decision);
}

std::uint8_t player(const Decision& decision) noexcept {
    return std::visit([](const auto& value) { return value.player; }, decision);
}

}
