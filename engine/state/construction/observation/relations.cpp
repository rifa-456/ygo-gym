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

void ObservationBuilder::add_chain() {
    const auto& current = core_->game_field->core.current_chain;
    for(std::uint32_t index = 0; index < current.size(); ++index) {
        const auto& link = current[index];
        auto* handler = link.triggering_effect->get_handler();
        const auto card_id = add_card(handler, true);
        const auto target_begin = static_cast<std::uint32_t>(storage_->chain_targets.size());
        if(link.target_cards) {
            for(auto* target : link.target_cards->container)
                storage_->chain_targets.push_back(add_card(target, identity_visible(*target, viewer_)));
        }
        storage_->chain.push_back(ChainState{
            index,
            card_id,
            link.triggering_player,
            link.triggering_controler,
            link.triggering_location,
            link.triggering_sequence,
            link.triggering_effect->description,
            target_begin,
            static_cast<std::uint32_t>(storage_->chain_targets.size()) - target_begin,
        });
    }
}

void ObservationBuilder::add_relations_and_counters() {
    for(const auto& [value, source] : by_pointer_) {
        for(const auto& counter : value->counters) {
            const auto count = static_cast<std::uint16_t>(counter.second[0] + counter.second[1]);
            storage_->counters.push_back(CounterState{source, counter.first, count});
        }
        if(value->equiping_target != nullptr)
            add_relation(RelationKind::equip, source, value->equiping_target, 0);
        std::uint32_t sequence = 0;
        for(auto* target : value->effect_target_cards)
            add_relation(RelationKind::target, source, target, sequence++);
        if(value->current.reason_card != nullptr)
            add_relation(RelationKind::reason, source, value->current.reason_card, 0);
    }
}

void ObservationBuilder::add_relation(RelationKind kind, std::uint32_t source, card* target, std::uint32_t sequence) {
    const auto found = by_pointer_.find(target);
    if(found != by_pointer_.end())
        storage_->relations.push_back(RelationState{kind, source, found->second, sequence});
}

}
