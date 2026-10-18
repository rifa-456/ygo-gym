#include "decoder.h"
#include "decode_fields.h"

namespace ygo_gym::protocol {
namespace {

std::optional<Decision> decode_payload(const std::uint8_t* data, std::size_t size) {
    if(size == 0)
        return std::nullopt;
    Reader reader(data, size);
    const auto type = reader.read<std::uint8_t>();
    std::optional<Decision> decision;

    switch(type) {
    case MSG_SELECT_BATTLECMD:
        decision = read_battle(reader);
        break;
    case MSG_SELECT_IDLECMD:
        decision = read_idle(reader);
        break;
    case MSG_SELECT_EFFECTYN: {
        EffectYesNoDecision value{};
        value.player = reader.read<std::uint8_t>();
        value.card = read_card(reader, true);
        value.description = reader.read<std::uint64_t>();
        decision = std::move(value);
        break;
    }
    case MSG_SELECT_YESNO:
        decision = YesNoDecision{reader.read<std::uint8_t>(), reader.read<std::uint64_t>()};
        break;
    case MSG_SELECT_OPTION: {
        OptionDecision value{};
        value.player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint8_t>();
        value.options = read_items<std::uint64_t>(reader, count, [](Reader& input) { return input.read<std::uint64_t>(); });
        decision = std::move(value);
        break;
    }
    case MSG_SELECT_CARD:
        decision = read_card_selection(reader);
        break;
    case MSG_SELECT_CHAIN:
        decision = read_chain(reader);
        break;
    case MSG_SELECT_PLACE:
        decision = read_place(reader, false);
        break;
    case MSG_SELECT_DISFIELD:
        decision = read_place(reader, true);
        break;
    case MSG_SELECT_POSITION:
        decision = PositionDecision{
            reader.read<std::uint8_t>(),
            reader.read<std::uint32_t>(),
            reader.read<std::uint8_t>(),
        };
        break;
    case MSG_SELECT_TRIBUTE:
        decision = read_tribute(reader);
        break;
    case MSG_SELECT_COUNTER:
        decision = read_counter(reader);
        break;
    case MSG_SELECT_SUM:
        decision = read_sum(reader);
        break;
    case MSG_SORT_CHAIN:
        decision = read_sort(reader, true);
        break;
    case MSG_SORT_CARD:
        decision = read_sort(reader, false);
        break;
    case MSG_SELECT_UNSELECT_CARD:
        decision = read_unselect(reader);
        break;
    case MSG_ANNOUNCE_RACE:
        decision = AnnounceRaceDecision{
            reader.read<std::uint8_t>(),
            reader.read<std::uint8_t>(),
            reader.read<std::uint64_t>(),
        };
        break;
    case MSG_ANNOUNCE_ATTRIB:
        decision = AnnounceAttributeDecision{
            reader.read<std::uint8_t>(),
            reader.read<std::uint8_t>(),
            reader.read<std::uint32_t>(),
        };
        break;
    case MSG_ANNOUNCE_CARD: {
        AnnounceCardDecision value{};
        value.player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint8_t>();
        value.opcodes = read_items<std::uint64_t>(reader, count, [](Reader& input) { return input.read<std::uint64_t>(); });
        decision = std::move(value);
        break;
    }
    case MSG_ANNOUNCE_NUMBER: {
        AnnounceNumberDecision value{};
        value.player = reader.read<std::uint8_t>();
        const auto count = reader.read<std::uint8_t>();
        value.options = read_items<std::uint64_t>(reader, count, [](Reader& input) { return input.read<std::uint64_t>(); });
        decision = std::move(value);
        break;
    }
    case MSG_ROCK_PAPER_SCISSORS:
        decision = RockPaperScissorsDecision{reader.read<std::uint8_t>()};
        break;
    default:
        return std::nullopt;
    }

    reader.finish();
    return decision;
}

template<typename Visit>
void visit_frames(const std::vector<std::uint8_t>& messages, Visit visit) {
    std::size_t offset = 0;
    while(offset < messages.size()) {
        if(messages.size() - offset < sizeof(std::uint32_t))
            throw std::runtime_error("truncated ocgcore message frame");
        std::uint32_t size = 0;
        std::memcpy(&size, messages.data() + offset, sizeof(size));
        offset += sizeof(size);
        if(size > messages.size() - offset)
            throw std::runtime_error("ocgcore message frame length exceeds the available data");
        visit(messages.data() + offset, size);
        offset += size;
    }
}

}

std::optional<Decision> decode_decision(const std::vector<std::uint8_t>& messages) {
    std::optional<Decision> result;
    visit_frames(messages, [&](const std::uint8_t* data, std::size_t size) {
        if(auto decoded = decode_payload(data, size))
            result = std::move(decoded);
    });
    return result;
}

bool contains_retry(const std::vector<std::uint8_t>& messages) {
    bool retry = false;
    visit_frames(messages, [&](const std::uint8_t* data, std::size_t size) {
        if(size != 0 && data[0] == MSG_RETRY)
            retry = true;
    });
    return retry;
}

}
