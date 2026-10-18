#include "action/legality/legality.h"

#include <algorithm>
#include <functional>

#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::action {
namespace {

bool contains(const std::vector<std::uint32_t>& values, std::uint32_t value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

}

std::vector<protocol::ZoneRef> available_zones(
    const protocol::PlaceDecision& decision,
    const std::vector<protocol::ZoneRef>& selected
) {
    auto unavailable = decision.unavailable;
    for(const auto& zone : selected) {
        std::uint32_t bit = 1u << zone.sequence;
        if(zone.location == LOCATION_SZONE)
            bit <<= 8;
        if(zone.player != decision.player)
            bit <<= 16;
        unavailable |= bit;
    }

    std::vector<protocol::ZoneRef> zones;
    for(std::uint8_t side = 0; side < 2; ++side) {
        const auto player = side == 0 ? decision.player : static_cast<std::uint8_t>(1 - decision.player);
        const auto base = side == 0 ? 0u : 16u;
        for(std::uint8_t sequence = 0; sequence <= 6; ++sequence) {
            if((unavailable & (1u << (base + sequence))) == 0)
                zones.push_back(protocol::ZoneRef{player, LOCATION_MZONE, sequence});
        }
        for(std::uint8_t sequence = 0; sequence <= 7; ++sequence) {
            if((unavailable & (1u << (base + 8u + sequence))) == 0)
                zones.push_back(protocol::ZoneRef{player, LOCATION_SZONE, sequence});
        }
    }
    return zones;
}

bool tribute_complete(
    const protocol::TributeDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    if(selected.size() > decision.max)
        return false;
    std::uint32_t total = 0;
    for(const auto index : selected)
        total += decision.cards[index].value;
    return total >= decision.min;
}

bool tribute_can_complete(
    const protocol::TributeDecision& decision,
    const std::vector<std::uint32_t>& selected
) {
    if(selected.size() > decision.max)
        return false;
    std::uint32_t total = 0;
    for(const auto index : selected)
        total += decision.cards[index].value;
    if(total >= decision.min)
        return true;

    std::vector<std::uint8_t> remaining;
    for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
        if(!contains(selected, index))
            remaining.push_back(decision.cards[index].value);
    }
    std::sort(remaining.begin(), remaining.end(), std::greater<>());
    const auto slots = decision.max - static_cast<std::uint32_t>(selected.size());
    for(std::uint32_t index = 0; index < std::min<std::uint32_t>(slots, remaining.size()); ++index)
        total += remaining[index];
    return total >= decision.min;
}

}
