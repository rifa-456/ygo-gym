#pragma once
#include <algorithm>
#include <cstring>
#include <stdexcept>
#include "client/capture.h"

namespace ygo_gym::client {
template<typename T> T read(const Packet& bytes, std::size_t offset) {
    if(offset + sizeof(T) > bytes.size())
        throw std::runtime_error("truncated client protocol data");
    T result;
    std::memcpy(&result, bytes.data() + offset, sizeof(T));
    return result;
}
template<typename T> void append(Packet& bytes, T value) {
    const auto* data = reinterpret_cast<const std::uint8_t*>(&value);
    bytes.insert(bytes.end(), data, data + sizeof(T));
}
inline void hide(Packet& bytes, std::size_t offset) {
    if(offset + 4 > bytes.size())
        throw std::runtime_error("truncated client card identity");
    std::fill_n(bytes.begin() + static_cast<std::ptrdiff_t>(offset), 4, 0);
}
}
