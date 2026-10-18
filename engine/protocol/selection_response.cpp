#include "selection.h"
#include "response_encoding.h"

namespace ygo_gym::protocol {

Response CardDecision::response(const std::vector<std::uint32_t>& indices) const {
    if(indices.size() < min || indices.size() > max)
        throw std::invalid_argument("selected card count is outside the allowed range");
    check_unique_indices(indices, cards.size());
    return card_indices_response(DecisionKind::card, indices);
}

Response CardDecision::cancel_response() const {
    if(!cancelable)
        throw std::invalid_argument("card selection is not cancelable");
    return ::ygo_gym::protocol::cancel_response(DecisionKind::card);
}

Response PlaceDecision::response(const std::vector<ZoneRef>& zones) const {
    if(zones.size() != count)
        throw std::invalid_argument("selected zone count does not match the required count");

    auto unavailable_mask = unavailable;
    Response response{disable_field ? DecisionKind::disable_field : DecisionKind::place, {}};
    response.data.reserve(zones.size() * 3);
    for(const auto& zone : zones) {
        if(zone.player > 1)
            throw std::invalid_argument("zone player must be 0 or 1");
        const bool monster_zone = zone.location == LOCATION_MZONE;
        if(!monster_zone && zone.location != LOCATION_SZONE)
            throw std::invalid_argument("zone location must be LOCATION_MZONE or LOCATION_SZONE");
        if(zone.sequence > (monster_zone ? 6 : 7))
            throw std::invalid_argument("zone sequence is out of range");

        std::uint32_t bit = 1u << zone.sequence;
        if(!monster_zone)
            bit <<= 8;
        if(zone.player != player)
            bit <<= 16;
        if((unavailable_mask & bit) != 0)
            throw std::invalid_argument("selected zone is unavailable or duplicated");
        unavailable_mask |= bit;

        append(response.data, zone.player);
        append(response.data, zone.location);
        append(response.data, zone.sequence);
    }
    return response;
}

Response PositionDecision::response(std::uint8_t position) const {
    if(position != POS_FACEUP_ATTACK && position != POS_FACEDOWN_ATTACK
       && position != POS_FACEUP_DEFENSE && position != POS_FACEDOWN_DEFENSE)
        throw std::invalid_argument("position must contain exactly one card position");
    if((positions & position) == 0)
        throw std::invalid_argument("selected position is not available");
    return scalar_response<std::int32_t>(DecisionKind::position, position);
}

Response TributeDecision::response(const std::vector<std::uint32_t>& indices) const {
    if(indices.size() > max)
        throw std::invalid_argument("too many tribute cards selected");
    check_unique_indices(indices, cards.size());
    std::uint32_t total = 0;
    for(const auto index : indices)
        total += cards[index].value;
    if(total < min)
        throw std::invalid_argument("selected cards do not provide enough tribute value");
    return card_indices_response(DecisionKind::tribute, indices);
}

Response TributeDecision::cancel_response() const {
    if(!cancelable)
        throw std::invalid_argument("tribute selection is not cancelable");
    return ::ygo_gym::protocol::cancel_response(DecisionKind::tribute);
}

Response CounterDecision::response(const std::vector<std::uint16_t>& counts) const {
    if(counts.size() != cards.size())
        throw std::invalid_argument("one counter count is required for each candidate card");
    std::uint32_t total = 0;
    Response response{DecisionKind::counter, {}};
    response.data.reserve(counts.size() * sizeof(std::uint16_t));
    for(std::size_t index = 0; index < counts.size(); ++index) {
        if(counts[index] > cards[index].available)
            throw std::invalid_argument("counter selection exceeds the available count");
        total += counts[index];
        append(response.data, counts[index]);
    }
    if(total != count)
        throw std::invalid_argument("selected counters do not match the required total");
    return response;
}

Response SumDecision::response(const std::vector<std::uint32_t>& indices) const {
    check_unique_indices(indices, cards.size());
    if(max != 0 && (indices.size() < min || indices.size() > max))
        throw std::invalid_argument("selected card count is outside the allowed range");
    return card_indices_response(DecisionKind::sum, indices);
}

Response SortDecision::response(const std::vector<std::uint8_t>& order) const {
    if(order.size() != cards.size())
        throw std::invalid_argument("sort response must contain one position for each card");
    std::vector<bool> seen(cards.size(), false);
    for(const auto value : order) {
        if(value >= cards.size() || seen[value])
            throw std::invalid_argument("sort response must be a permutation of card indices");
        seen[value] = true;
    }
    return Response{sort_kind(chain), order};
}

Response SortDecision::cancel_response() const {
    return scalar_response<std::int8_t>(sort_kind(chain), -1);
}

Response UnselectCardDecision::response(std::uint32_t index) const {
    const auto size = selectable.size() + unselectable.size();
    check_index(index, size, "card");
    Response response{DecisionKind::unselect_card, {}};
    append<std::int32_t>(response.data, 1);
    append<std::int32_t>(response.data, static_cast<std::int32_t>(index));
    return response;
}

Response UnselectCardDecision::finish_response() const {
    if(!finishable && !cancelable)
        throw std::invalid_argument("selection cannot be finished or canceled yet");
    return cancel_response(DecisionKind::unselect_card);
}

}
