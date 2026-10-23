#include "client/bytes.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::client {
namespace {
struct Field {
    std::uint32_t flag;
    Packet bytes;
};
constexpr auto private_flags = QUERY_CODE | QUERY_ALIAS | QUERY_TYPE | QUERY_LEVEL |
    QUERY_RANK | QUERY_ATTRIBUTE | QUERY_RACE | QUERY_ATTACK | QUERY_DEFENSE |
    QUERY_BASE_ATTACK | QUERY_BASE_DEFENSE | QUERY_STATUS | QUERY_LSCALE | QUERY_RSCALE | QUERY_LINK;
}

Packet project_queries(const Packet& bytes, bool opponent) {
    Packet result;
    std::size_t offset = 4;
    if(read<std::uint32_t>(bytes, 0) != bytes.size() - 4) throw std::runtime_error("invalid client query stream length");
    while(offset < bytes.size()) {
        std::vector<Field> fields;
        bool faceup = false, public_card = false, hidden = false;
        while(true) {
            auto start = offset;
            auto size = read<std::uint16_t>(bytes, offset);
            offset += 2;
            if(size == 0) {
                append<std::uint16_t>(result, 0);
                break;
            }
            if(size < 4 || size > bytes.size() - offset)
                throw std::runtime_error("invalid client query field length");
            auto flag = read<std::uint32_t>(bytes, offset);
            if(flag == QUERY_POSITION) faceup = (read<std::uint32_t>(bytes, offset + 4) & POS_FACEUP) != 0;
            if(flag == QUERY_IS_PUBLIC) public_card = read<std::uint8_t>(bytes, offset + 4) != 0;
            if(flag == QUERY_IS_HIDDEN) hidden = read<std::uint8_t>(bytes, offset + 4) != 0;
            offset += size;
            fields.push_back({flag, Packet(bytes.begin() + static_cast<std::ptrdiff_t>(start), bytes.begin() + static_cast<std::ptrdiff_t>(offset))});
            if(flag == QUERY_END) {
                const bool mask = (opponent || hidden) && !faceup && !public_card;
                for(const auto& field : fields) {
                    if(mask && (field.flag & private_flags)) continue;
                    result.insert(result.end(), field.bytes.begin(), field.bytes.end());
                }
                break;
            }
        }
    }
    Packet framed;
    append<std::uint32_t>(framed, static_cast<std::uint32_t>(result.size()));
    framed.insert(framed.end(), result.begin(), result.end());
    return framed;
}
}
