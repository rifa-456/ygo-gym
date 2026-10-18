#include "event/decoding/transition_builder.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::event {

void TransitionBuilder::counter(Reader& reader, int sign) {
    const auto type = reader.read<std::uint16_t>();
    Locator location{};
    location.controller = reader.read<std::uint8_t>();
    location.location = reader.read<std::uint8_t>();
    location.sequence = reader.read<std::uint8_t>();
    const auto count = reader.read<std::uint16_t>();
    const auto id = card(0, 0x3, location);
    transition_.events.emplace_back(CounterEvent{id, type, static_cast<std::int32_t>(count) * sign});
}

void TransitionBuilder::relation(Reader& reader, RelationEventKind kind_value) {
    const auto source_location = read_location(reader);
    const auto target_location = read_location(reader);
    const auto source = card(0, 0x3, source_location);
    const auto target = card(0, 0x3, target_location);
    transition_.events.emplace_back(RelationEvent{kind_value, source, target});
}

void TransitionBuilder::attack(Reader& reader) {
    const auto attacker_location = read_location(reader);
    const auto target_location = read_location(reader);
    const auto attacker = card(0, 0x3, attacker_location);
    std::optional<std::uint32_t> target;
    if(target_location.location != 0)
        target = card(0, 0x3, target_location);
    transition_.events.emplace_back(AttackEvent{attacker, target});
}

void TransitionBuilder::battle(Reader& reader) {
    const auto attacker_location = read_location(reader);
    const auto attacker = card(0, 0x3, attacker_location);
    const auto attacker_attack = reader.read<std::uint32_t>();
    const auto attacker_defense = reader.read<std::uint32_t>();
    const auto attacker_destroyed = reader.read<std::uint8_t>() != 0;
    const auto target_location = read_location(reader);
    const auto target_attack = reader.read<std::uint32_t>();
    const auto target_defense = reader.read<std::uint32_t>();
    const auto target_destroyed = reader.read<std::uint8_t>() != 0;
    std::optional<std::uint32_t> target;
    if(target_location.location != 0)
        target = card(0, 0x3, target_location);
    transition_.events.emplace_back(BattleEvent{
        attacker,
        static_cast<std::int32_t>(attacker_attack),
        static_cast<std::int32_t>(attacker_defense),
        attacker_destroyed,
        target,
        static_cast<std::int32_t>(target_attack),
        static_cast<std::int32_t>(target_defense),
        target_destroyed,
    });
}

}
