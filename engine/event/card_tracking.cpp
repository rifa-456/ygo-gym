#include "transition_builder.h"
#include "ocgapi_constants.h"

namespace ygo_gym::event {

std::uint32_t TransitionBuilder::card(std::uint32_t code, std::uint8_t visible_to, std::optional<Locator> current) {
    if(current && current->location != 0) {
        const auto found = located_.find(key(*current));
        if(found != located_.end()) {
            auto& existing = transition_.cards[found->second];
            existing.visible_to |= visible_to;
            existing.current = current;
            if(existing.code == 0)
                existing.code = code;
            return found->second;
        }
    }
    const auto id = static_cast<std::uint32_t>(transition_.cards.size());
    transition_.cards.push_back(RawCard{code, visible_to, current});
    if(current && current->location != 0)
        located_[key(*current)] = id;
    return id;
}

std::uint32_t TransitionBuilder::moved_card(std::uint32_t code, std::uint8_t visible_to, const Locator& previous, const Locator& current) {
    std::optional<std::uint32_t> found_id;
    if(previous.location != 0) {
        const auto found = located_.find(key(previous));
        if(found != located_.end()) {
            found_id = found->second;
            located_.erase(found);
        }
    }
    if(!found_id)
        return card(code, visible_to, current.location == 0 ? std::nullopt : std::optional<Locator>{current});
    auto& existing = transition_.cards[*found_id];
    existing.code = code;
    existing.visible_to |= visible_to;
    existing.current = current.location == 0 ? std::nullopt : std::optional<Locator>{current};
    if(current.location != 0)
        located_[key(current)] = *found_id;
    return *found_id;
}

void TransitionBuilder::clear_zone(std::uint8_t player, std::uint32_t location) {
    for(auto it = located_.begin(); it != located_.end();) {
        if((player == 0xff || it->first.controller == player) && it->first.location == location)
            it = located_.erase(it);
        else
            ++it;
    }
}

}
