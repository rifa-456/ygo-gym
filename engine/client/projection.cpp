#include "client/bytes.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::client {
namespace {
bool decision(std::uint8_t type) {
    switch(type) {
    case MSG_SELECT_BATTLECMD: case MSG_SELECT_IDLECMD: case MSG_SELECT_EFFECTYN:
    case MSG_SELECT_YESNO: case MSG_SELECT_OPTION: case MSG_SELECT_CARD:
    case MSG_SELECT_CHAIN: case MSG_SELECT_PLACE: case MSG_SELECT_POSITION:
    case MSG_SELECT_TRIBUTE: case MSG_SORT_CHAIN: case MSG_SELECT_COUNTER:
    case MSG_SELECT_SUM: case MSG_SELECT_DISFIELD: case MSG_SORT_CARD:
    case MSG_SELECT_UNSELECT_CARD: case MSG_ROCK_PAPER_SCISSORS:
    case MSG_ANNOUNCE_RACE: case MSG_ANNOUNCE_ATTRIB: case MSG_ANNOUNCE_CARD:
    case MSG_ANNOUNCE_NUMBER: return true;
    default: return false;
    }
}
void selection(Packet& packet, std::size_t& offset, std::uint8_t viewer, bool tribute) {
    auto count = read<std::uint32_t>(packet, offset);
    offset += 4;
    for(std::uint32_t i = 0; i < count; ++i) {
        if(packet.at(offset + 4) != viewer) hide(packet, offset);
        offset += tribute ? 11 : 14;
        if(offset > packet.size()) throw std::runtime_error("truncated client selection");
    }
}
}

bool project(Packet& packet, std::uint8_t viewer) {
    const auto type = packet.at(0);
    if(decision(type)) {
        if(packet.at(1) != viewer) return false;
        std::size_t offset = type == MSG_SELECT_UNSELECT_CARD ? 12 : 11;
        if(type == MSG_SELECT_CARD || type == MSG_SELECT_TRIBUTE)
            selection(packet, offset, viewer, type == MSG_SELECT_TRIBUTE);
        if(type == MSG_SELECT_UNSELECT_CARD) {
            selection(packet, offset, viewer, false);
            selection(packet, offset, viewer, false);
        }
        return true;
    }
    switch(type) {
    case MSG_HINT: {
        const auto hint = packet.at(1);
        const auto player = packet.at(2);
        switch(hint) {
        case 1: case 2: case 3: case 5: case 200: return player == viewer;
        case 4: case 6: case 7: case 8: case 9: case 11: return player != viewer;
        case 10: case 201: case 202: case 203: return true;
        default: return false;
        }
    }
    case MSG_CONFIRM_CARDS:
        if(read<std::uint32_t>(packet, 2) && (packet.at(11) == LOCATION_DECK || packet.at(11) == LOCATION_EXTRA))
            return packet.at(1) == viewer;
        return true;
    case MSG_SHUFFLE_HAND: case MSG_SHUFFLE_EXTRA:
        if(packet.at(1) != viewer)
            for(std::uint32_t i = 0, count = read<std::uint32_t>(packet, 2); i < count; ++i)
                hide(packet, 6 + 4 * i);
        return true;
    case MSG_DRAW:
        if(packet.at(1) != viewer)
            for(std::uint32_t i = 0, count = read<std::uint32_t>(packet, 2); i < count; ++i)
                if(!(read<std::uint32_t>(packet, 10 + 8 * i) & POS_FACEUP)) hide(packet, 6 + 8 * i);
        return true;
    case MSG_SET:
        hide(packet, 1); return true;
    case MSG_MOVE: {
        const auto controller = packet.at(15);
        const auto location = packet.at(16);
        const auto position = read<std::uint32_t>(packet, 21);
        if(controller != viewer && !(location & (LOCATION_GRAVE | LOCATION_OVERLAY)) &&
           ((location & (LOCATION_DECK | LOCATION_HAND)) || (position & POS_FACEDOWN))) hide(packet, 1);
        return true;
    }
    case MSG_SPSUMMONING:
        if(packet.at(5) != viewer && (read<std::uint32_t>(packet, 11) & POS_FACEDOWN)) hide(packet, 1);
        return true;
    case MSG_MISSED_EFFECT:
        return packet.at(1) == viewer;
    case MSG_TAG_SWAP:
        throw std::runtime_error("WindBot transport supports two-player duels without tag swaps");
    default:
        return true;
    }
}
}
