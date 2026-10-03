#pragma once

#include <array>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "ocgapi.h"

namespace ygo_gym {

struct BackendState {
    std::filesystem::path card_database;
    std::vector<std::filesystem::path> script_roots;
};

class Duel {
public:
    Duel(std::shared_ptr<const BackendState> backend, const std::array<std::uint64_t, 4>& seed);
    ~Duel();

    Duel(const Duel&) = delete;
    Duel& operator=(const Duel&) = delete;
    Duel(Duel&&) = delete;
    Duel& operator=(Duel&&) = delete;

    void close() noexcept;
    [[nodiscard]] bool closed() const noexcept;

private:
    static void read_card(void* payload, std::uint32_t code, OCG_CardData* data) noexcept;
    static int read_script(void* payload, OCG_Duel duel, const char* name) noexcept;

    std::shared_ptr<const BackendState> backend_;
    OCG_Duel duel_{nullptr};
};

class Backend {
public:
    Backend(std::filesystem::path card_database, std::vector<std::filesystem::path> script_roots);

    [[nodiscard]] std::pair<int, int> core_version() const noexcept;
    [[nodiscard]] std::unique_ptr<Duel> create_duel(const std::array<std::uint64_t, 4>& seed) const;

private:
    std::shared_ptr<const BackendState> state_;
};

}
