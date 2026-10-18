#pragma once
#include <cstring>
#include <stdexcept>
#include <type_traits>
#include "decision.h"

namespace ygo_gym::protocol {

class Reader {
public:
    Reader(const std::uint8_t* data, std::size_t size) : data_(data), size_(size) {}

    template<typename T>
    T read() {
        static_assert(std::is_trivially_copyable_v<T>);
        if(position_ + sizeof(T) > size_)
            throw std::runtime_error("truncated ocgcore decision message");
        T value{};
        std::memcpy(&value, data_ + position_, sizeof(T));
        position_ += sizeof(T);
        return value;
    }

    void finish() const {
        if(position_ != size_)
            throw std::runtime_error("ocgcore decision message has unexpected trailing data");
    }

private:
    const std::uint8_t* data_;
    std::size_t size_;
    std::size_t position_{0};
};

inline CardRef read_card(Reader& reader, bool position, bool wide_sequence = true, bool wide_location = false) {
    CardRef card{};
    card.code = reader.read<std::uint32_t>();
    card.controller = reader.read<std::uint8_t>();
    card.location = wide_location ? reader.read<std::uint32_t>() : reader.read<std::uint8_t>();
    card.sequence = wide_sequence ? reader.read<std::uint32_t>() : reader.read<std::uint8_t>();
    if(position)
        card.position = reader.read<std::uint32_t>();
    return card;
}

inline EffectRef read_effect(Reader& reader, bool position) {
    auto card = read_card(reader, position);
    return EffectRef{std::move(card), reader.read<std::uint64_t>(), reader.read<std::uint8_t>()};
}

template<typename T, typename ReadItem>
std::vector<T> read_items(Reader& reader, std::uint32_t count, ReadItem read_item) {
    std::vector<T> items;
    items.reserve(count);
    for(std::uint32_t index = 0; index < count; ++index)
        items.push_back(read_item(reader));
    return items;
}

}
