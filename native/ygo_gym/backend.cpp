#include "backend.h"

#include <stdexcept>
#include <string>
#include <utility>

#include "duel.h"
#include "ocgapi.h"

namespace ygo_gym {

Backend::Backend(
    std::filesystem::path card_database,
    std::vector<std::filesystem::path> script_roots,
    std::vector<CardDefinition> cards
) {
    if(!std::filesystem::is_regular_file(card_database))
        throw std::invalid_argument("card database does not exist: " + card_database.string());
    if(script_roots.empty())
        throw std::invalid_argument("at least one script root is required");
    for(const auto& root : script_roots) {
        if(!std::filesystem::is_directory(root))
            throw std::invalid_argument("script root does not exist: " + root.string());
    }
    if(cards.empty())
        throw std::invalid_argument("card database contains no cards");

    std::unordered_map<std::uint32_t, CardDefinition> card_map;
    card_map.reserve(cards.size());
    for(auto& card : cards) {
        if(!card.setcodes.empty() && card.setcodes.back() != 0)
            card.setcodes.push_back(0);
        card_map.insert_or_assign(card.code, std::move(card));
    }

    state_ = std::make_shared<BackendState>(BackendState{
        std::move(card_database),
        std::move(script_roots),
        std::move(card_map),
    });
}

std::pair<int, int> Backend::core_version() const noexcept {
    int major = 0;
    int minor = 0;
    OCG_GetVersion(&major, &minor);
    return {major, minor};
}

std::unique_ptr<Duel> Backend::create_duel(
    std::uint64_t seed,
    std::vector<std::uint32_t> player1_main,
    std::vector<std::uint32_t> player1_extra,
    std::vector<std::uint32_t> player2_main,
    std::vector<std::uint32_t> player2_extra
) const {
    validate_cards(player1_main);
    validate_cards(player1_extra);
    validate_cards(player2_main);
    validate_cards(player2_extra);
    return std::make_unique<Duel>(
        state_,
        seed,
        std::move(player1_main),
        std::move(player1_extra),
        std::move(player2_main),
        std::move(player2_extra)
    );
}

void Backend::validate_cards(const std::vector<std::uint32_t>& cards) const {
    for(const auto code : cards) {
        if(state_->cards.find(code) == state_->cards.end())
            throw std::invalid_argument("card database has no entry for code " + std::to_string(code));
    }
}

}
