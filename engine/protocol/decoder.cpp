#include "decoder.h"

#include <cstring>
#include <stdexcept>
#include <type_traits>

namespace ygo_gym::protocol {
namespace {

class Reader {
public:
    Reader(const std::uint8_t* data, std::size_t size) : data_(data), size_(size) {}

    template<typename T>
    T read() {
        static_assert(std::is_trivially_copyable_v<T>);
        if(position_ + sizeof(T) > size_)
            throw std::runtime_error("truncated ocgcore decision message");
        T value{};
        std::memcpy(&value, data_ + position_, sizeof(T));
        position_ += sizeof(T);
        return value;
    }

    void finish() const {
        if(position_ != size_)
            throw std::runtime_error("ocgcore decision message has unexpected trailing data");
    }

private:
    const std::uint8_t* data_;
    std::size_t size_;
    std::size_t position_{0};
};

CardRef read_card(Reader& reader, bool position, bool wide_sequence = true, bool wide_location = false) {
    CardRef card{};
    card.code = reader.read<std::uint32_t>();
    card.controller = reader.read<std::uint8_t>();
    card.location = wide_location ? reader.read<std::uint32_t>() : reader.read<std::uint8_t>();
    card.sequence = wide_sequence ? reader.read<std::uint32_t>() : reader.read<std::uint8_t>();
    if(position)
        card.position = reader.read<std::uint32_t>();
    return card;
}

EffectRef read_effect(Reader& reader, bool position) {
    auto card = read_card(reader, position);
    return EffectRef{std::move(card), reader.read<std::uint64_t>(), reader.read<std::uint8_t>()};
}

template<typename T, typename ReadItem>
std::vector<T> read_items(Reader& reader, std::uint32_t count, ReadItem read_item) {
    std::vector<T> items;
    items.reserve(count);
    for(std::uint32_t index = 0; index < count; ++index)
        items.push_back(read_item(reader));
    return items;
}

BattleDecision read_battle(Reader& reader) {
    BattleDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.activatable = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, false);
    });
    decision.attackable = read_items<AttackRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        auto card = read_card(input, false, false);
        return AttackRef{std::move(card), input.read<std::uint8_t>() != 0};
    });
    decision.can_main_phase_2 = reader.read<std::uint8_t>() != 0;
    decision.can_end_phase = reader.read<std::uint8_t>() != 0;
    return decision;
}

IdleDecision read_idle(Reader& reader) {
    IdleDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    const auto normal_card = [](Reader& input) { return read_card(input, false); };
    decision.summonable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.special_summonable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.repositionable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_card(input, false, false);
    });
    decision.monster_settable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.spell_trap_settable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), normal_card);
    decision.activatable = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, false);
    });
    decision.can_battle_phase = reader.read<std::uint8_t>() != 0;
    decision.can_end_phase = reader.read<std::uint8_t>() != 0;
    decision.can_shuffle_hand = reader.read<std::uint8_t>() != 0;
    return decision;
}

CardDecision read_card_selection(Reader& reader) {
    CardDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.cancelable = reader.read<std::uint8_t>() != 0;
    decision.min = reader.read<std::uint32_t>();
    decision.max = reader.read<std::uint32_t>();
    decision.cards = read_items<CardRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_card(input, true);
    });
    return decision;
}

ChainDecision read_chain(Reader& reader) {
    ChainDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.special_count = reader.read<std::uint8_t>();
    decision.forced = reader.read<std::uint8_t>() != 0;
    decision.hint_timing = reader.read<std::uint32_t>();
    decision.opponent_hint_timing = reader.read<std::uint32_t>();
    decision.options = read_items<EffectRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_effect(input, true);
    });
    return decision;
}

PlaceDecision read_place(Reader& reader, bool disable_field) {
    return PlaceDecision{
        reader.read<std::uint8_t>(),
        reader.read<std::uint8_t>(),
        reader.read<std::uint32_t>(),
        disable_field,
    };
}

TributeDecision read_tribute(Reader& reader) {
    TributeDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.cancelable = reader.read<std::uint8_t>() != 0;
    decision.min = reader.read<std::uint32_t>();
    decision.max = reader.read<std::uint32_t>();
    decision.cards = read_items<TributeRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        auto card = read_card(input, false);
        return TributeRef{std::move(card), input.read<std::uint8_t>()};
    });
    return decision;
}

CounterDecision read_counter(Reader& reader) {
    CounterDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.counter_type = reader.read<std::uint16_t>();
    decision.count = reader.read<std::uint16_t>();
    decision.cards = read_items<CounterRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        auto card = read_card(input, false, false);
        return CounterRef{std::move(card), input.read<std::uint16_t>()};
    });
    return decision;
}

SumDecision read_sum(Reader& reader) {
    SumDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.mode = reader.read<std::uint8_t>();
    decision.target = reader.read<std::uint32_t>();
    decision.min = reader.read<std::uint32_t>();
    decision.max = reader.read<std::uint32_t>();
    const auto read_sum_ref = [](Reader& input) {
        auto card = read_card(input, true);
        return SumRef{std::move(card), input.read<std::uint32_t>()};
    };
    decision.required = read_items<SumRef>(reader, reader.read<std::uint32_t>(), read_sum_ref);
    decision.cards = read_items<SumRef>(reader, reader.read<std::uint32_t>(), read_sum_ref);
    return decision;
}

SortDecision read_sort(Reader& reader, bool chain) {
    SortDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.chain = chain;
    decision.cards = read_items<CardRef>(reader, reader.read<std::uint32_t>(), [](Reader& input) {
        return read_card(input, false, true, true);
    });
    return decision;
}

UnselectCardDecision read_unselect(Reader& reader) {
    UnselectCardDecision decision{};
    decision.player = reader.read<std::uint8_t>();
    decision.finishable = reader.read<std::uint8_t>() != 0;
    decision.cancelable = reader.read<std::uint8_t>() != 0;
    decision.min = reader.read<std::uint32_t>();
    decision.max = reader.read<std::uint32_t>();
    const auto read_located = [](Reader& input) { return read_card(input, true); };
    decision.selectable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), read_located);
    decision.unselectable = read_items<CardRef>(reader, reader.read<std::uint32_t>(), read_located);
    return decision;
}

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
