#include "event/decoding/decoder.h"
#include "event/decoding/transition_builder.h"

namespace ygo_gym::event {

Transition decode(const std::vector<std::uint8_t>& messages) {
    TransitionBuilder builder;
    std::size_t offset = 0;
    while(offset < messages.size()) {
        if(messages.size() - offset < sizeof(std::uint32_t))
            throw std::runtime_error("truncated ocgcore message frame");
        std::uint32_t size = 0;
        std::memcpy(&size, messages.data() + offset, sizeof(size));
        offset += sizeof(size);
        if(size > messages.size() - offset)
            throw std::runtime_error("ocgcore message frame length exceeds the available data");
        builder.message(messages.data() + offset, size);
        offset += size;
    }
    return builder.finish();
}

}
