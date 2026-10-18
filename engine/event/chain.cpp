#include "transition_builder.h"
#include "ocgapi_constants.h"

namespace ygo_gym::event {

void TransitionBuilder::summon(Reader& reader, SummonKind kind, SummonStage stage, bool public_code) {
    const auto code = reader.read<std::uint32_t>();
    const auto location = read_location(reader);
    std::uint8_t visible = 0x3;
    if(!public_code && (location.position & POS_FACEDOWN) != 0)
        visible = static_cast<std::uint8_t>(1u << location.controller);
    const auto id = card(code, visible, location);
    latest_summon_[static_cast<std::size_t>(kind)] = std::make_pair(id, location.controller);
    transition_.events.emplace_back(SummonEvent{id, location.controller, kind, stage});
}

void TransitionBuilder::complete_summon(SummonKind kind) {
    const auto& latest = latest_summon_[static_cast<std::size_t>(kind)];
    if(latest)
        transition_.events.emplace_back(SummonEvent{latest->first, latest->second, kind, SummonStage::complete});
}

void TransitionBuilder::chaining(Reader& reader) {
    const auto code = reader.read<std::uint32_t>();
    const auto handler = read_location(reader);
    const auto player = reader.read<std::uint8_t>();
    (void)reader.read<std::uint8_t>();
    (void)reader.read<std::uint32_t>();
    const auto description = reader.read<std::uint64_t>();
    const auto index = reader.read<std::uint32_t>();
    const auto id = card(code, 0x3, handler);
    chain_[index] = ChainMeta{id, player, description};
    transition_.events.emplace_back(ChainEvent{ChainStage::activating, id, player, description, index});
}

void TransitionBuilder::chain_stage(Reader& reader, ChainStage stage) {
    const auto index = static_cast<std::uint32_t>(reader.read<std::uint8_t>());
    const auto found = chain_.find(index);
    if(found == chain_.end()) {
        transition_.events.emplace_back(ChainEvent{stage, std::nullopt, std::nullopt, std::nullopt, index});
        return;
    }
    transition_.events.emplace_back(ChainEvent{stage, found->second.card, found->second.player, found->second.description, index});
}

}
