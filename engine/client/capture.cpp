#include "client/capture.h"
#include "client/bytes.h"
#include "ygopro-core/duel.h"
#include "ygopro-core/field.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::client {
namespace {
std::atomic<std::uint64_t> sessions{1};
constexpr std::uint32_t query_flags = 0x03781fff;
}

Capture::Capture(OCG_Duel duel) : duel_(duel), session_(sessions.fetch_add(1)) {
    begin();
    for(auto& batch : batches_)
        batch->initial = true;
    initialize();
}

void Capture::begin() {
    for(auto& batch : batches_)
        batch = std::make_shared<Batch>(Batch{session_, index_, false, {}});
    ++index_;
}

std::shared_ptr<const Batch> Capture::batch(std::uint8_t viewer) const {
    return batches_.at(viewer);
}

void Capture::send(std::uint8_t viewer, Packet packet) {
    packet.insert(packet.begin(), 1);
    batches_.at(viewer)->packets.push_back(std::move(packet));
}

void Capture::initialize() {
    const auto& field = *static_cast<::duel*>(duel_)->game_field;
    for(std::uint8_t viewer = 0; viewer < 2; ++viewer) {
        Packet join{0x12};
        append<std::uint32_t>(join, 0);
        join.insert(join.end(), {0, 0, 5, 1, 0, 0, 0, 0});
        append<std::uint32_t>(join, 8000);
        join.insert(join.end(), {5, 1, 0, 0, 0, 0, 0, 0});
        append<std::uint32_t>(join, 4043399681u);
        append<std::uint32_t>(join, 0);
        for(auto value : {1, 1, 1}) append<std::int32_t>(join, value);
        append<std::uint32_t>(join, static_cast<std::uint32_t>(field.core.duel_options));
        append<std::uint64_t>(join, 0);
        batches_[viewer]->packets.push_back(std::move(join));
        Packet start{MSG_START, viewer};
        for(const auto& player : field.player) append<std::int32_t>(start, player.lp);
        for(const auto& player : field.player) {
            append<std::uint16_t>(start, static_cast<std::uint16_t>(player.list_main.size()));
            append<std::uint16_t>(start, static_cast<std::uint16_t>(player.list_extra.size()));
        }
        send(viewer, std::move(start));
    }
}

void Capture::refresh(std::uint8_t player, std::uint8_t location) {
    OCG_QueryInfo info{};
    info.flags = query_flags;
    info.con = player;
    info.loc = location;
    std::uint32_t length = 0;
    const auto* raw = static_cast<const std::uint8_t*>(OCG_DuelQueryLocation(duel_, &length, &info));
    if(!length) return;
    Packet query(raw, raw + length);
    for(std::uint8_t viewer = 0; viewer < 2; ++viewer) {
        Packet message{MSG_UPDATE_DATA, player, location};
        auto projected = project_queries(query, viewer != player);
        message.insert(message.end(), projected.begin(), projected.end());
        send(viewer, std::move(message));
    }
}

void Capture::refresh_fields() {
    for(std::uint8_t player = 0; player < 2; ++player) {
        refresh(player, LOCATION_MZONE);
        refresh(player, LOCATION_SZONE);
    }
}
void Capture::refresh_hands() {
    for(std::uint8_t player = 0; player < 2; ++player)
        refresh(player, LOCATION_HAND);
}

void Capture::message(Packet packet) {
    const auto type = packet.at(0);
    if(type == MSG_SELECT_IDLECMD || type == MSG_SELECT_BATTLECMD || type == MSG_SELECT_CHAIN || type == MSG_NEW_TURN) {
        refresh_fields();
        if(type != MSG_NEW_TURN && type != MSG_SELECT_CHAIN) refresh_hands();
    }
    for(std::uint8_t viewer = 0; viewer < 2; ++viewer) {
        auto copy = packet;
        if(project(copy, viewer)) send(viewer, std::move(copy));
    }
    switch(type) {
    case MSG_DRAW: case MSG_SHUFFLE_HAND:
        refresh(packet.at(1), LOCATION_HAND); break;
    case MSG_SHUFFLE_EXTRA:
        refresh(packet.at(1), LOCATION_EXTRA); break;
    case MSG_NEW_PHASE: case MSG_CHAINED: case MSG_CHAIN_END: case MSG_RELOAD_FIELD:
        refresh_hands();
        [[fallthrough]];
    case MSG_SUMMONED: case MSG_SPSUMMONED: case MSG_FLIPSUMMONED:
    case MSG_CHAIN_SOLVED: case MSG_DAMAGE_STEP_START: case MSG_DAMAGE_STEP_END:
    case MSG_MOVE: case MSG_POS_CHANGE: case MSG_SWAP: case MSG_SHUFFLE_SET_CARD:
        refresh_fields();
        for(std::uint8_t player = 0; player < 2; ++player) {
            refresh(player, LOCATION_GRAVE);
            refresh(player, LOCATION_REMOVED);
            refresh(player, LOCATION_EXTRA);
        }
        break;
    case MSG_SWAP_GRAVE_DECK:
        refresh(packet.at(1), LOCATION_GRAVE); break;
    default: break;
    }
}

void Capture::consume(const std::uint8_t* data, std::size_t size) {
    if(ended_) return;
    Packet bytes(data, data + size);
    for(std::size_t offset = 0; offset < bytes.size();) {
        const auto length = read<std::uint32_t>(bytes, offset);
        offset += 4;
        if(length == 0 || length > bytes.size() - offset)
            throw std::runtime_error("invalid client protocol frame length");
        message(Packet(bytes.begin() + static_cast<std::ptrdiff_t>(offset), bytes.begin() + static_cast<std::ptrdiff_t>(offset + length)));
        if(bytes.at(offset) == MSG_WIN) { ended_ = true; return; }
        offset += length;
    }
}
}
