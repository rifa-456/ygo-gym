#include "state/observation.h"

#include <stdexcept>
#include <unordered_map>
#include <utility>

#include "ygopro-core/card.h"
#include "ygopro-core/duel.h"

namespace ygo_gym::state {

Observation clone_observation(const Observation& source, OCG_Duel target) {
    const auto* core = static_cast<const ::duel*>(target);
    std::unordered_map<std::uint32_t, ::card*> cards;
    cards.reserve(core->cards.size());
    for(auto* value : core->cards) {
        if(!cards.emplace(value->cardid, value).second)
            throw std::logic_error("cloned core has duplicate card identities");
    }

    auto storage = std::make_shared<ObservationStorage>(*source.storage());
    storage->client_batch.reset();
    for(std::size_t i=0;i<storage->core_cards.size();++i) {
        auto*& value=storage->core_cards[i];
        const auto found = cards.find(storage->core_card_ids.at(i));
        if(found == cards.end())
            throw std::logic_error("observation card is missing from cloned core");
        value = found->second;
    }
    storage->events = event::Batch{
        std::make_shared<event::BatchStorage>(*source.events().storage())
    };
    return Observation{std::move(storage)};
}

}
