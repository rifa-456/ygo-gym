#include "state/state.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <utility>

#include "ygopro-core/card.h"
#include "ygopro-core/duel.h"
#include "ygopro-core/effect.h"
#include "ygopro-core/field.h"
#include "ygopro-core/ocgapi_constants.h"

#include "state/construction/full_state/builder.h"
#include "state/construction/card_lookup.h"

namespace ygo_gym::state {

StateBuilder::StateBuilder(::duel* core) : core_(core), storage_(std::make_shared<StateStorage>()) {
    auto& field = *core_->game_field;
    storage_->global.turn_player = field.infos.turn_player;
    storage_->global.turn_count = field.infos.turn_id;
    storage_->global.phase = field.infos.phase;
    storage_->global.life_points[0] = field.player[0].lp;
    storage_->global.life_points[1] = field.player[1].lp;
    storage_->duel_options = field.core.duel_options;
    for(std::uint8_t player = 0; player < 2; ++player) {
        const auto& info = field.player[player];
        storage_->players[player] = PlayerState{
            info.lp,
            info.start_lp,
            info.start_count,
            info.draw_count,
            info.used_location,
            info.disabled_location,
            info.extra_p_count,
        };
    }
}

State StateBuilder::build(
    const protocol::Decision* decision,
    const std::vector<action::Action>& pending_actions,
    const ObservationStorage* observation
) {
    if(decision != nullptr)
        storage_->global.decision_player = protocol::player(*decision);
    if(observation != nullptr) {
        for(auto* value : observation->core_cards)
            add_card(value);
    }
    add_zones();
    add_unzoned_cards();
    add_relations_and_counters();
    add_chain();
    for(const auto& pending : pending_actions)
        storage_->pending_actions.push_back(remap_action(pending));
    return State{std::move(storage_)};
}

void StateBuilder::add_zone(std::uint8_t player, std::uint32_t location, const card_vector& cards) {
    const auto begin = static_cast<std::uint32_t>(storage_->zone_cards.size());
    for(auto* value : cards) {
        if(value != nullptr)
            storage_->zone_cards.push_back(add_card(value));
    }
    storage_->zones.push_back(ZoneState{
        player,
        location,
        begin,
        static_cast<std::uint32_t>(storage_->zone_cards.size()) - begin,
    });
}

void StateBuilder::add_zones() {
    for(std::uint8_t player = 0; player < 2; ++player) {
        auto& info = core_->game_field->player[player];
        add_zone(player, LOCATION_DECK, info.list_main);
        add_zone(player, LOCATION_HAND, info.list_hand);
        add_zone(player, LOCATION_MZONE, info.list_mzone);
        add_zone(player, LOCATION_SZONE, info.list_szone);
        add_zone(player, LOCATION_GRAVE, info.list_grave);
        add_zone(player, LOCATION_REMOVED, info.list_remove);
        add_zone(player, LOCATION_EXTRA, info.list_extra);
        for(auto* host : info.list_mzone) {
            if(host != nullptr)
                add_materials(*host);
        }
    }
}

void StateBuilder::add_unzoned_cards() {
    std::vector<card*> remaining;
    for(auto* value : core_->cards) {
        if(value->data.code != 0 && storage_->pointer_index.find(value) == storage_->pointer_index.end())
            remaining.push_back(value);
    }
    std::sort(remaining.begin(), remaining.end(), [](const card* lhs, const card* rhs) {
        return lhs->cardid < rhs->cardid;
    });
    for(auto* value : remaining)
        add_card(value);
}

}
