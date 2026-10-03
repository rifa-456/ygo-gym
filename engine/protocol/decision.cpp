#include "decision.h"

#include <algorithm>
#include <cstring>
#include <stdexcept>
#include <type_traits>
#include <unordered_set>

namespace ygo_gym::protocol {
namespace {

template<typename T>
void append(std::vector<std::uint8_t>& data, T value) {
    static_assert(std::is_trivially_copyable_v<T>);
    const auto offset = data.size();
    data.resize(offset + sizeof(T));
    std::memcpy(data.data() + offset, &value, sizeof(T));
}

template<typename T>
Response scalar_response(DecisionKind kind, T value) {
    Response response{kind, {}};
    append(response.data, value);
    return response;
}

void check_index(std::uint32_t index, std::size_t size, const char* label) {
    if(index >= size)
        throw std::invalid_argument(std::string(label) + " index is out of range");
}

void check_unique_indices(const std::vector<std::uint32_t>& indices, std::size_t size) {
    std::unordered_set<std::uint32_t> seen;
    seen.reserve(indices.size());
    for(const auto index : indices) {
        check_index(index, size, "card");
        if(!seen.insert(index).second)
            throw std::invalid_argument("card indices must be unique");
    }
}

Response card_indices_response(DecisionKind kind, const std::vector<std::uint32_t>& indices) {
    Response response{kind, {}};
    append<std::int32_t>(response.data, 0);
    append<std::uint32_t>(response.data, static_cast<std::uint32_t>(indices.size()));
    for(const auto index : indices)
        append(response.data, index);
    return response;
}

Response cancel_response(DecisionKind kind) {
    return scalar_response<std::int32_t>(kind, -1);
}

std::uint32_t command_response_value(std::uint16_t command, std::uint32_t index) {
    if(index > 0xffff)
        throw std::invalid_argument("command index does not fit in the ocgcore response format");
    return (index << 16) | command;
}

std::uint32_t bit_count(std::uint64_t value) {
    std::uint32_t count = 0;
    while(value != 0) {
        value &= value - 1;
        ++count;
    }
    return count;
}

DecisionKind sort_kind(bool chain) {
    return chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
}

}

Response BattleDecision::response(BattleCommand command, std::uint32_t index) const {
    switch(command) {
    case BattleCommand::activate:
        check_index(index, activatable.size(), "activation");
        break;
    case BattleCommand::attack:
        check_index(index, attackable.size(), "attack");
        break;
    case BattleCommand::main_phase_2:
        if(!can_main_phase_2)
            throw std::invalid_argument("main phase 2 is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case BattleCommand::end_phase:
        if(!can_end_phase)
            throw std::invalid_argument("end phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    }
    const auto value = command_response_value(static_cast<std::uint16_t>(command), index);
    return scalar_response<std::int32_t>(DecisionKind::battle_command, static_cast<std::int32_t>(value));
}

Response IdleDecision::response(IdleCommand command, std::uint32_t index) const {
    switch(command) {
    case IdleCommand::summon:
        check_index(index, summonable.size(), "summon");
        break;
    case IdleCommand::special_summon:
        check_index(index, special_summonable.size(), "special summon");
        break;
    case IdleCommand::reposition:
        check_index(index, repositionable.size(), "reposition");
        break;
    case IdleCommand::set_monster:
        check_index(index, monster_settable.size(), "monster set");
        break;
    case IdleCommand::set_spell_trap:
        check_index(index, spell_trap_settable.size(), "spell/trap set");
        break;
    case IdleCommand::activate:
        check_index(index, activatable.size(), "activation");
        break;
    case IdleCommand::battle_phase:
        if(!can_battle_phase)
            throw std::invalid_argument("battle phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case IdleCommand::end_phase:
        if(!can_end_phase)
            throw std::invalid_argument("end phase is not available");
        if(index != 0)
            throw std::invalid_argument("phase commands do not take an index");
        break;
    case IdleCommand::shuffle_hand:
        if(!can_shuffle_hand)
            throw std::invalid_argument("hand shuffle is not available");
        if(index != 0)
            throw std::invalid_argument("shuffle hand does not take an index");
        break;
    }
    const auto value = command_response_value(static_cast<std::uint16_t>(command), index);
    return scalar_response<std::int32_t>(DecisionKind::idle_command, static_cast<std::int32_t>(value));
}

Response EffectYesNoDecision::response(bool yes) const {
    return scalar_response<std::int32_t>(DecisionKind::effect_yes_no, yes ? 1 : 0);
}

Response YesNoDecision::response(bool yes) const {
    return scalar_response<std::int32_t>(DecisionKind::yes_no, yes ? 1 : 0);
}

Response OptionDecision::response(std::uint32_t index) const {
    check_index(index, options.size(), "option");
    return scalar_response<std::int32_t>(DecisionKind::option, static_cast<std::int32_t>(index));
}

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

Response ChainDecision::response(std::uint32_t index) const {
    check_index(index, options.size(), "chain");
    return scalar_response<std::int32_t>(DecisionKind::chain, static_cast<std::int32_t>(index));
}

Response ChainDecision::pass_response() const {
    if(forced)
        throw std::invalid_argument("chain selection is forced");
    return cancel_response(DecisionKind::chain);
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

Response AnnounceRaceDecision::response(std::uint64_t races) const {
    if((races & ~available) != 0 || bit_count(races) != count)
        throw std::invalid_argument("announced races do not match the available choices");
    return scalar_response(DecisionKind::announce_race, races);
}

Response AnnounceAttributeDecision::response(std::uint32_t attributes) const {
    if((attributes & ~available) != 0 || bit_count(attributes) != count)
        throw std::invalid_argument("announced attributes do not match the available choices");
    return scalar_response(DecisionKind::announce_attribute, attributes);
}

Response AnnounceCardDecision::response(std::uint32_t code) const {
    return scalar_response(DecisionKind::announce_card, code);
}

Response AnnounceNumberDecision::response(std::uint32_t index) const {
    check_index(index, options.size(), "number");
    return scalar_response<std::int32_t>(DecisionKind::announce_number, static_cast<std::int32_t>(index));
}

Response RockPaperScissorsDecision::response(RpsChoice choice) const {
    return scalar_response<std::int32_t>(DecisionKind::rock_paper_scissors, static_cast<std::int32_t>(choice));
}

DecisionKind kind(const Decision& decision) noexcept {
    return std::visit([](const auto& value) -> DecisionKind {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, BattleDecision>) return DecisionKind::battle_command;
        if constexpr(std::is_same_v<T, IdleDecision>) return DecisionKind::idle_command;
        if constexpr(std::is_same_v<T, EffectYesNoDecision>) return DecisionKind::effect_yes_no;
        if constexpr(std::is_same_v<T, YesNoDecision>) return DecisionKind::yes_no;
        if constexpr(std::is_same_v<T, OptionDecision>) return DecisionKind::option;
        if constexpr(std::is_same_v<T, CardDecision>) return DecisionKind::card;
        if constexpr(std::is_same_v<T, ChainDecision>) return DecisionKind::chain;
        if constexpr(std::is_same_v<T, PlaceDecision>) return value.disable_field ? DecisionKind::disable_field : DecisionKind::place;
        if constexpr(std::is_same_v<T, PositionDecision>) return DecisionKind::position;
        if constexpr(std::is_same_v<T, TributeDecision>) return DecisionKind::tribute;
        if constexpr(std::is_same_v<T, CounterDecision>) return DecisionKind::counter;
        if constexpr(std::is_same_v<T, SumDecision>) return DecisionKind::sum;
        if constexpr(std::is_same_v<T, SortDecision>) return value.chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
        if constexpr(std::is_same_v<T, UnselectCardDecision>) return DecisionKind::unselect_card;
        if constexpr(std::is_same_v<T, AnnounceRaceDecision>) return DecisionKind::announce_race;
        if constexpr(std::is_same_v<T, AnnounceAttributeDecision>) return DecisionKind::announce_attribute;
        if constexpr(std::is_same_v<T, AnnounceCardDecision>) return DecisionKind::announce_card;
        if constexpr(std::is_same_v<T, AnnounceNumberDecision>) return DecisionKind::announce_number;
        return DecisionKind::rock_paper_scissors;
    }, decision);
}

std::uint8_t player(const Decision& decision) noexcept {
    return std::visit([](const auto& value) { return value.player; }, decision);
}

}
