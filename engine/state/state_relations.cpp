#include "state.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <utility>

#include "../../third_party/ygopro-core/card.h"
#include "../../third_party/ygopro-core/duel.h"
#include "../../third_party/ygopro-core/effect.h"
#include "../../third_party/ygopro-core/field.h"
#include "ocgapi_constants.h"

#include "state_builder.h"
#include "card_lookup.h"

namespace ygo_gym::state {

void StateBuilder::add_relations_and_counters() {
    for(auto* value : core_->cards) {
        const auto source_found = storage_->pointer_index.find(value);
        if(source_found == storage_->pointer_index.end())
            continue;
        const auto source = source_found->second;
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

void StateBuilder::add_relation(RelationKind kind, std::uint32_t source, card* target, std::uint32_t sequence) {
    const auto found = storage_->pointer_index.find(target);
    if(found != storage_->pointer_index.end())
        storage_->relations.push_back(RelationState{kind, source, found->second, sequence});
}

void StateBuilder::add_chain() {
    const auto& current = core_->game_field->core.current_chain;
    for(std::uint32_t index = 0; index < current.size(); ++index) {
        const auto& link = current[index];
        const auto card_id = storage_->pointer_index.at(link.triggering_effect->get_handler());
        const auto target_begin = static_cast<std::uint32_t>(storage_->chain_targets.size());
        if(link.target_cards) {
            for(auto* target : link.target_cards->container)
                storage_->chain_targets.push_back(storage_->pointer_index.at(target));
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

}
