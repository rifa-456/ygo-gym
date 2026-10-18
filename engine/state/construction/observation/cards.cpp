#include "state/observation.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include "ygopro-core/card.h"
#include "ygopro-core/duel.h"
#include "ygopro-core/effect.h"
#include "ygopro-core/effect_constants.h"
#include "ygopro-core/field.h"
#include "ygopro-core/ocgapi_constants.h"

#include "state/construction/observation/builder.h"
#include "state/construction/card_lookup.h"

namespace ygo_gym::state {

std::uint32_t ObservationBuilder::add_card(card* value, bool reveal) {
    if(const auto found = by_pointer_.find(value); found != by_pointer_.end()) {
        if(reveal && storage_->cards[found->second].code == unknown_card)
            reveal_card(found->second, *value);
        return found->second;
    }

    const auto id = static_cast<std::uint32_t>(storage_->cards.size());
    by_pointer_.emplace(value, id);
    storage_->cards.push_back(CardRecord{
        reveal ? value->data.code : unknown_card,
        value->owner,
        value->current.controler,
        value->current.location,
        value->current.sequence,
        value->current.position,
    });
    storage_->core_cards.push_back(value);
    storage_->card_index.emplace(CardLocator{
        value->current.controler,
        value->current.location,
        value->current.sequence,
        invalid_index,
    }, id);
    if(reveal)
        add_components(id, *value);
    return id;
}

void ObservationBuilder::reveal_card(std::uint32_t id, card& value) {
    storage_->cards[id].code = value.data.code;
    add_components(id, value);
}

void ObservationBuilder::add_components(std::uint32_t id, card& value) {
    auto& row = storage_->cards[id];
    if(row.properties_index != invalid_index)
        return;

    const auto type = value.get_type();
    row.properties_index = static_cast<std::uint32_t>(storage_->properties.size());
    storage_->properties.push_back(CardProperties{
        value.get_code(), type, value.get_attribute(), value.get_race(),
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

void ObservationBuilder::add_materials(card& host, std::uint32_t host_id) {
    for(std::uint32_t sequence = 0; sequence < host.xyz_materials.size(); ++sequence) {
        auto* material = host.xyz_materials[sequence];
        const auto id = add_card(material, true);
        auto& row = storage_->cards[id];
        row.location = LOCATION_OVERLAY;
        row.sequence = sequence;
        row.position = 0;
        storage_->card_index.emplace(CardLocator{
            host.current.controler,
            static_cast<std::uint32_t>(host.current.location | LOCATION_OVERLAY),
            host.current.sequence,
            sequence,
        }, id);
        storage_->relations.push_back(RelationState{RelationKind::material, host_id, id, sequence});
    }
}

}
