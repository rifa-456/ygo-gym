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

std::uint32_t StateBuilder::add_card(card* value) {
    if(const auto found = storage_->pointer_index.find(value); found != storage_->pointer_index.end())
        return found->second;

    const auto id = static_cast<std::uint32_t>(storage_->cards.size());
    storage_->pointer_index.emplace(value, id);
    storage_->cards.push_back(CardRecord{
        value->data.code,
        value->owner,
        value->current.controler,
        value->current.location,
        value->current.sequence,
        value->current.position,
    });
    add_components(id, *value);
    return id;
}

void StateBuilder::add_components(std::uint32_t id, card& value) {
    auto& row = storage_->cards[id];
    const auto type = value.get_type();
    row.properties_index = static_cast<std::uint32_t>(storage_->properties.size());
    storage_->properties.push_back(CardProperties{
        value.get_code(), type, value.get_attribute(), value.get_race(),
        (value.status & STATUS_DISABLED) != 0, (value.status & STATUS_PROC_COMPLETE) != 0,
    });
    if((type & TYPE_MONSTER) != 0) {
        row.monster_index = static_cast<std::uint32_t>(storage_->monsters.size());
        storage_->monsters.push_back(MonsterState{
            value.get_level(), value.get_rank(), value.get_attack(), value.get_defense(),
            value.get_base_attack(), value.get_base_defense(),
        });
    }
    if((type & TYPE_PENDULUM) != 0) {
        row.pendulum_index = static_cast<std::uint32_t>(storage_->pendulums.size());
        storage_->pendulums.push_back(PendulumState{value.get_lscale(), value.get_rscale()});
    }
    if((type & TYPE_LINK) != 0) {
        row.link_index = static_cast<std::uint32_t>(storage_->links.size());
        storage_->links.push_back(LinkState{value.get_link(), value.get_link_marker()});
    }
}

void StateBuilder::add_materials(card& host) {
    const auto host_id = storage_->pointer_index.at(&host);
    for(std::uint32_t sequence = 0; sequence < host.xyz_materials.size(); ++sequence) {
        auto* material = host.xyz_materials[sequence];
        const auto id = add_card(material);
        auto& row = storage_->cards[id];
        row.location = LOCATION_OVERLAY;
        row.sequence = sequence;
        row.position = 0;
        storage_->relations.push_back(RelationState{RelationKind::material, host_id, id, sequence});
    }
}

action::Action StateBuilder::remap_action(const action::Action& input) const {
    return std::visit([&](const auto& value) -> action::Action {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, action::CardAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_card, core_);
            return copy;
        } else if constexpr(std::is_same_v<T, action::EffectAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_effect.card, core_);
            return copy;
        } else if constexpr(std::is_same_v<T, action::AttackAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_attack.card, core_);
            return copy;
        } else if constexpr(std::is_same_v<T, action::TributeAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_tribute.card, core_);
            return copy;
        } else if constexpr(std::is_same_v<T, action::SumAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_sum.card, core_);
            return copy;
        } else if constexpr(std::is_same_v<T, action::CounterAction>) {
            auto copy = value;
            copy.card = storage_->card_id(copy.core_counter.card, core_);
            return copy;
        } else {
            return value;
        }
    }, input);
}

}
