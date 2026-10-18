#include "transition_builder.h"
#include "ocgapi_constants.h"

namespace ygo_gym::event {

void TransitionBuilder::confirm(Reader& reader, std::uint8_t type) {
    const auto player = reader.read<std::uint8_t>();
    const auto count = reader.read<std::uint32_t>();
    for(std::uint32_t i = 0; i < count; ++i) {
        const auto code = reader.read<std::uint32_t>();
        Locator location{};
        location.controller = reader.read<std::uint8_t>();
        location.location = reader.read<std::uint8_t>();
        location.sequence = reader.read<std::uint32_t>();
        std::uint8_t visible = 0x3;
        if(type == MSG_CONFIRM_CARDS && (location.location == LOCATION_DECK || location.location == LOCATION_EXTRA))
            visible = static_cast<std::uint8_t>(1u << player);
        const auto id = card(code, visible, location);
        transition_.events.emplace_back(RevealEvent{id});
    }
}

void TransitionBuilder::shuffle_simple(Reader& reader, std::uint32_t location) {
    const auto player = reader.read<std::uint8_t>();
    transition_.events.emplace_back(ShuffleEvent{player, location});
    clear_zone(player, location);
}

void TransitionBuilder::shuffle_cards(Reader& reader, std::uint32_t location) {
    const auto player = reader.read<std::uint8_t>();
    const auto count = reader.read<std::uint32_t>();
    for(std::uint32_t i = 0; i < count; ++i)
        (void)reader.read<std::uint32_t>();
    transition_.events.emplace_back(ShuffleEvent{player, location});
    clear_zone(player, location);
}

void TransitionBuilder::deck_top(Reader& reader) {
    const auto player = reader.read<std::uint8_t>();
    const auto offset = reader.read<std::uint32_t>();
    const auto code = reader.read<std::uint32_t>();
    const auto position = reader.read<std::uint32_t>();
    (void)offset;
    (void)player;
    (void)position;
    const auto id = card(code, 0x3, std::nullopt);
    transition_.events.emplace_back(RevealEvent{id});
}

void TransitionBuilder::move(Reader& reader) {
    const auto code = reader.read<std::uint32_t>();
    const auto previous = read_location(reader);
    const auto current = read_location(reader);
    const auto reason = reader.read<std::uint32_t>();
    std::uint8_t visible = static_cast<std::uint8_t>(1u << current.controller);
    const bool public_destination = (current.location & (LOCATION_GRAVE | LOCATION_OVERLAY)) != 0
        || (((current.location & (LOCATION_DECK | LOCATION_HAND)) == 0) && ((current.position & POS_FACEDOWN) == 0));
    if(public_destination || current.location == 0)
        visible = 0x3;
    const auto id = moved_card(code, visible, previous, current);
    transition_.events.emplace_back(MoveEvent{id, previous, current, reason});
}

void TransitionBuilder::position(Reader& reader) {
    const auto code = reader.read<std::uint32_t>();
    const auto controller = reader.read<std::uint8_t>();
    const auto location = reader.read<std::uint8_t>();
    const auto sequence = reader.read<std::uint8_t>();
    const auto previous = reader.read<std::uint8_t>();
    const auto current = reader.read<std::uint8_t>();
    Locator locator{controller, location, sequence, current};
    const auto id = card(code, 0x3, locator);
    transition_.events.emplace_back(PositionEvent{id, controller, location, sequence, previous, current});
}

void TransitionBuilder::set(Reader& reader) {
    const auto code = reader.read<std::uint32_t>();
    const auto location = read_location(reader);
    const auto visible = static_cast<std::uint8_t>(1u << location.controller);
    const auto id = card(code, visible, location);
    transition_.events.emplace_back(SetEvent{id});
}

void TransitionBuilder::draw(Reader& reader) {
    const auto player = reader.read<std::uint8_t>();
    const auto count = reader.read<std::uint32_t>();
    for(std::uint32_t i = 0; i < count; ++i) {
        const auto code = reader.read<std::uint32_t>();
        const auto position = reader.read<std::uint32_t>();
        auto visible = static_cast<std::uint8_t>(1u << player);
        if((position & POS_FACEUP) != 0)
            visible = 0x3;
        const auto id = card(code, visible, std::nullopt);
        transition_.events.emplace_back(DrawEvent{player, id});
    }
}

}
