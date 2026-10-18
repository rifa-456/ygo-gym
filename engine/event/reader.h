#pragma once

#include <cstring>
#include <stdexcept>
#include "event.h"

namespace ygo_gym::event {

class Reader {
public:
    Reader(const std::uint8_t* data, std::size_t size) : data_(data), size_(size) {}

    template<typename T>
    T read() {
        if(position_ + sizeof(T) > size_)
            throw std::runtime_error("truncated ocgcore event message");
        T value{};
        std::memcpy(&value, data_ + position_, sizeof(T));
        position_ += sizeof(T);
        return value;
    }

    [[nodiscard]] std::size_t remaining() const noexcept { return size_ - position_; }

private:
    const std::uint8_t* data_;
    std::size_t size_;
    std::size_t position_{0};
};

inline Locator read_location(Reader& reader) {
    return Locator{
        reader.read<std::uint8_t>(),
        reader.read<std::uint8_t>(),
        reader.read<std::uint32_t>(),
        reader.read<std::uint32_t>(),
    };
}

}
