#pragma once
#include "action/state.h"
#include "action/legality/legality.h"
#include <algorithm>

namespace ygo_gym::action {

template<typename T>
bool contains(const std::vector<T>& values, T value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

inline void add_card_actions(
    std::vector<Action>& actions,
    const state::ObservationStorage& observation,
    ActionKind kind,
    const std::vector<protocol::CardRef>& cards
) {
    for(std::uint32_t index = 0; index < cards.size(); ++index) {
        actions.emplace_back(CardAction{
            kind,
            observation.card_id(cards[index]),
            cards[index],
            index,
        });
    }
}

inline void add_effect_actions(
    std::vector<Action>& actions,
    const state::ObservationStorage& observation,
    ActionKind kind,
    const std::vector<protocol::EffectRef>& effects
) {
    for(std::uint32_t index = 0; index < effects.size(); ++index) {
        const auto& effect = effects[index];
        actions.emplace_back(EffectAction{
            kind,
            observation.card_id(effect.card),
            effect.description,
            effect.client_mode,
            effect,
            index,
        });
    }
}

inline std::vector<std::uint8_t> positions(std::uint8_t mask) {
    std::vector<std::uint8_t> result;
    for(const auto position : {POS_FACEUP_ATTACK, POS_FACEDOWN_ATTACK, POS_FACEUP_DEFENSE, POS_FACEDOWN_DEFENSE}) {
        if((mask & position) != 0)
            result.push_back(static_cast<std::uint8_t>(position));
    }
    return result;
}

inline std::vector<std::uint64_t> bits(std::uint64_t mask) {
    std::vector<std::uint64_t> result;
    for(std::uint8_t bit = 0; bit < 64; ++bit) {
        const auto value = std::uint64_t{1} << bit;
        if((mask & value) != 0)
            result.push_back(value);
    }
    return result;
}

inline std::vector<std::uint32_t> bits(std::uint32_t mask) {
    std::vector<std::uint32_t> result;
    for(std::uint8_t bit = 0; bit < 32; ++bit) {
        const auto value = std::uint32_t{1} << bit;
        if((mask & value) != 0)
            result.push_back(value);
    }
    return result;
}

}
