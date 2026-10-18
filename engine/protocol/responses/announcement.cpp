#include "protocol/decisions/announcement.h"
#include "protocol/responses/encoding.h"

namespace ygo_gym::protocol {

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

}
