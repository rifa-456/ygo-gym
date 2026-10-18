#pragma once

#include "decision.h"
#include <cstring>
#include <stdexcept>
#include <type_traits>
#include <unordered_set>

namespace ygo_gym::protocol {

template<typename T>
void append(std::vector<std::uint8_t>& data, T value) {
    static_assert(std::is_trivially_copyable_v<T>);
    const auto offset = data.size();
    data.resize(offset + sizeof(T));
    std::memcpy(data.data() + offset, &value, sizeof(T));
}

template<typename T>
Response scalar_response(DecisionKind kind, T value) {
    Response response{kind, {}};
    append(response.data, value);
    return response;
}

inline void check_index(std::uint32_t index, std::size_t size, const char* label) {
    if(index >= size)
        throw std::invalid_argument(std::string(label) + " index is out of range");
}

inline void check_unique_indices(const std::vector<std::uint32_t>& indices, std::size_t size) {
    std::unordered_set<std::uint32_t> seen;
    seen.reserve(indices.size());
    for(const auto index : indices) {
        check_index(index, size, "card");
        if(!seen.insert(index).second)
            throw std::invalid_argument("card indices must be unique");
    }
}

inline Response card_indices_response(DecisionKind kind, const std::vector<std::uint32_t>& indices) {
    Response response{kind, {}};
    append<std::int32_t>(response.data, 0);
    append<std::uint32_t>(response.data, static_cast<std::uint32_t>(indices.size()));
    for(const auto index : indices)
        append(response.data, index);
    return response;
}

inline Response cancel_response(DecisionKind kind) {
    return scalar_response<std::int32_t>(kind, -1);
}

inline std::uint32_t command_response_value(std::uint16_t command, std::uint32_t index) {
    if(index > 0xffff)
        throw std::invalid_argument("command index does not fit in the ocgcore response format");
    return (index << 16) | command;
}

inline std::uint32_t bit_count(std::uint64_t value) {
    std::uint32_t count = 0;
    while(value != 0) {
        value &= value - 1;
        ++count;
    }
    return count;
}

inline DecisionKind sort_kind(bool chain) {
    return chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
}

}
