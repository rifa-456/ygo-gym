#include "observation.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include "../../third_party/ygopro-core/card.h"
#include "../../third_party/ygopro-core/duel.h"
#include "../../third_party/ygopro-core/effect.h"
#include "../../third_party/ygopro-core/effect_constants.h"
#include "../../third_party/ygopro-core/field.h"
#include "ocgapi_constants.h"

#include "observation_builder.h"
#include "card_lookup.h"

namespace ygo_gym::state {

namespace {
template<typename F>
void for_each_decision_card(const protocol::Decision& decision, F&& visit) {
    std::visit([&](const auto& value) {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, protocol::BattleDecision>) {
            for(const auto& item : value.activatable) visit(item.card);
            for(const auto& item : value.attackable) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::IdleDecision>) {
            for(const auto& item : value.summonable) visit(item);
            for(const auto& item : value.special_summonable) visit(item);
            for(const auto& item : value.repositionable) visit(item);
            for(const auto& item : value.monster_settable) visit(item);
            for(const auto& item : value.spell_trap_settable) visit(item);
            for(const auto& item : value.activatable) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::EffectYesNoDecision>) {
            visit(value.card);
        } else if constexpr(std::is_same_v<T, protocol::CardDecision>) {
            for(const auto& item : value.cards) visit(item);
        } else if constexpr(std::is_same_v<T, protocol::ChainDecision>) {
            for(const auto& item : value.options) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::TributeDecision>) {
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::SumDecision>) {
            for(const auto& item : value.required) visit(item.card);
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            for(const auto& item : value.cards) visit(item);
        } else if constexpr(std::is_same_v<T, protocol::UnselectCardDecision>) {
            for(const auto& item : value.selectable) visit(item);
            for(const auto& item : value.unselectable) visit(item);
        }
    }, decision);
}
}

ObservationBuilder::ObservationBuilder(::duel* core, std::uint8_t viewer, const protocol::Decision* decision)
    : core_(core), viewer_(viewer), decision_(decision), storage_(std::make_shared<ObservationStorage>()) {
    storage_->viewer = viewer;
    storage_->global.turn_player = core_->game_field->infos.turn_player;
    storage_->global.turn_count = core_->game_field->infos.turn_id;
    storage_->global.phase = core_->game_field->infos.phase;
    storage_->global.life_points[0] = core_->game_field->player[0].lp;
    storage_->global.life_points[1] = core_->game_field->player[1].lp;
    if(decision_ != nullptr)
        storage_->global.decision_player = protocol::player(*decision_);
}

Observation ObservationBuilder::build(const event::Transition& events) {
    add_zone_counts();
    add_visible_cards();
    if(decision_ != nullptr && protocol::player(*decision_) == viewer_)
        add_decision_cards();
    add_chain();
    add_relations_and_counters();
    storage_->events = event::project(events, viewer_, *storage_);
    return Observation{std::move(storage_)};
}

void ObservationBuilder::add_zone_counts() {
    constexpr std::uint32_t locations[] = {
        LOCATION_DECK, LOCATION_HAND, LOCATION_MZONE, LOCATION_SZONE,
        LOCATION_GRAVE, LOCATION_REMOVED, LOCATION_EXTRA,
    };
    for(std::uint8_t player = 0; player < 2; ++player) {
        for(const auto location : locations) {
            storage_->zone_counts.push_back(ZoneCount{
                player,
                location,
                OCG_DuelQueryCount(core_, player, location),
            });
        }
    }
}

void ObservationBuilder::add_visible_cards() {
    for(std::uint8_t player = 0; player < 2; ++player) {
        const auto& info = core_->game_field->player[player];
        for(auto* value : info.list_hand)
            add_card(value, identity_visible(*value, viewer_));
        for(auto* value : info.list_mzone) {
            if(value != nullptr) {
                const auto host = add_card(value, identity_visible(*value, viewer_));
                add_materials(*value, host);
            }
        }
        for(auto* value : info.list_szone) {
            if(value != nullptr)
                add_card(value, identity_visible(*value, viewer_));
        }
        for(auto* value : info.list_grave)
            add_card(value, identity_visible(*value, viewer_));
        for(auto* value : info.list_remove)
            add_card(value, identity_visible(*value, viewer_));
        for(auto* value : info.list_extra) {
            const bool visible = identity_visible(*value, viewer_);
            if(value->owner == viewer_ || visible)
                add_card(value, visible);
        }
    }
}

void ObservationBuilder::add_decision_cards() {
    for_each_decision_card(*decision_, [&](const protocol::CardRef& ref) {
        auto* value = resolve_card(core_, ref);
        if(value == nullptr)
            throw std::runtime_error("ocgcore decision references a card that cannot be resolved");
        const auto id = add_card(value, decision_reveals_identity(ref));
        storage_->card_index.insert_or_assign(locator(ref), id);
    });
}

bool ObservationBuilder::decision_reveals_identity(const protocol::CardRef& ref) const {
    // EDOPro masks these selection packet codes when the card is controlled by the other player.
    return std::visit([&](const auto& value) {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, protocol::CardDecision>
            || std::is_same_v<T, protocol::TributeDecision>
            || std::is_same_v<T, protocol::UnselectCardDecision>) {
            return ref.controller == value.player;
        }
        return true;
    }, *decision_);
}

}
