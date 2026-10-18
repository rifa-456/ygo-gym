#include "transition_builder.h"
#include "ocgapi_constants.h"

namespace ygo_gym::event {

void TransitionBuilder::win(Reader& reader) {
    const auto winner = reader.read<std::uint8_t>();
    const auto reason = reader.read<std::uint8_t>();
    transition_.events.emplace_back(WinEvent{winner <= 1 ? std::optional<std::uint8_t>{winner} : std::nullopt, reason});
}

void TransitionBuilder::life(Reader& reader, LifePointKind kind) {
    const auto player = reader.read<std::uint8_t>();
    const auto amount = reader.read<std::uint32_t>();
    transition_.events.emplace_back(LifePointEvent{player, amount, kind});
}

void TransitionBuilder::life_set(Reader& reader) {
    const auto player = reader.read<std::uint8_t>();
    const auto value = reader.read<std::uint32_t>();
    transition_.events.emplace_back(LifePointEvent{player, value, LifePointKind::set});
}

void TransitionBuilder::random(Reader& reader, RandomKind kind_value) {
    const auto player = reader.read<std::uint8_t>();
    const auto count = reader.read<std::uint8_t>();
    std::vector<std::uint8_t> results;
    results.reserve(count);
    for(std::uint8_t i = 0; i < count; ++i)
        results.push_back(reader.read<std::uint8_t>());
    transition_.events.emplace_back(RandomEvent{player, kind_value, std::move(results)});
}

}
