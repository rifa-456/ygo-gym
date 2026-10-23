#pragma once

#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
#include <vector>
#include "ygopro-core/ocgapi.h"

namespace ygo_gym::client {

using Packet = std::vector<std::uint8_t>;
struct Batch {
    std::uint64_t session{};
    std::uint64_t index{};
    bool initial{};
    std::vector<Packet> packets;
};

class Capture {
public:
    explicit Capture(OCG_Duel duel);
    void begin();
    void consume(const std::uint8_t* data, std::size_t size);
    [[nodiscard]] std::shared_ptr<const Batch> batch(std::uint8_t viewer) const;
private:
    void initialize();
    void message(Packet packet);
    void send(std::uint8_t viewer, Packet packet);
    void refresh(std::uint8_t player, std::uint8_t location);
    void refresh_fields();
    void refresh_hands();
    OCG_Duel duel_;
    std::uint64_t session_;
    std::uint64_t index_{};
    bool ended_{};
    std::array<std::shared_ptr<Batch>, 2> batches_;
};

[[nodiscard]] bool project(Packet& packet, std::uint8_t viewer);
[[nodiscard]] Packet project_queries(const Packet& bytes, bool opponent);
}
