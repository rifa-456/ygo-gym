#include "protocol/decoding/decode_fields.h"

namespace ygo_gym::protocol {

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

}
