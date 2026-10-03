#pragma once

#include <cstdint>
#include <filesystem>
#include <memory>
#include <unordered_map>
#include <utility>
#include <vector>

namespace ygo_gym {

struct CardDefinition {
    std::uint32_t code;
    std::uint32_t alias;
    std::vector<std::uint16_t> setcodes;
    std::uint32_t type;
    std::uint32_t level;
    std::uint32_t attribute;
    std::uint64_t race;
    std::int32_t attack;
    std::int32_t defense;
    std::uint32_t lscale;
    std::uint32_t rscale;
    std::uint32_t link_marker;
};

struct BackendState {
    std::filesystem::path card_database;
    std::vector<std::filesystem::path> script_roots;
    std::unordered_map<std::uint32_t, CardDefinition> cards;
};

class Duel;

class Backend {
public:
    Backend(
        std::filesystem::path card_database,
        std::vector<std::filesystem::path> script_roots,
        std::vector<CardDefinition> cards
    );

    [[nodiscard]] std::pair<int, int> core_version() const noexcept;
    [[nodiscard]] std::unique_ptr<Duel> create_duel(
        std::uint64_t seed,
        std::vector<std::uint32_t> player1_main,
        std::vector<std::uint32_t> player1_extra,
        std::vector<std::uint32_t> player2_main,
        std::vector<std::uint32_t> player2_extra
    ) const;

private:
    void validate_cards(const std::vector<std::uint32_t>& cards) const;

    std::shared_ptr<const BackendState> state_;
};

}
