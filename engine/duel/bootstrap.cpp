#include "duel/duel.h"

#include <stdexcept>
#include <utility>
#include "ygopro-core/ocgapi_constants.h"

#include <algorithm>
#include <random>

namespace ygo_gym {
namespace {
std::string creation_error(int status) {
    switch(status) {
    case OCG_DUEL_CREATION_NO_OUTPUT: return "ocgcore did not receive an output pointer";
    case OCG_DUEL_CREATION_NOT_CREATED: return "ocgcore could not allocate a duel";
    case OCG_DUEL_CREATION_NULL_DATA_READER: return "ocgcore requires a card data reader";
    case OCG_DUEL_CREATION_NULL_SCRIPT_READER: return "ocgcore requires a script reader";
    case OCG_DUEL_CREATION_INCOMPATIBLE_LUA_API: return "ocgcore rejected the linked Lua runtime";
    case OCG_DUEL_CREATION_NULL_RNG_SEED: return "ocgcore requires a non-zero RNG seed";
    default: return "ocgcore duel creation failed with status " + std::to_string(status);
    }
}
}

Duel::Duel(
    std::shared_ptr<const EngineState> engine,
    std::uint64_t seed,
    std::vector<std::uint32_t> player1_main,
    std::vector<std::uint32_t> player1_extra,
    std::vector<std::uint32_t> player2_main,
    std::vector<std::uint32_t> player2_extra
) : engine_(std::move(engine)) {
    std::mt19937_64 random(seed);
    std::array<std::uint64_t, 4> core_seed{};
    for(auto& word : core_seed)
        word = random();
    if(std::all_of(core_seed.begin(), core_seed.end(), [](std::uint64_t word) { return word == 0; }))
        core_seed[0] = 1;

    std::shuffle(player1_main.begin(), player1_main.end(), random);
    std::shuffle(player2_main.begin(), player2_main.end(), random);

    OCG_DuelOptions options{};
    std::copy(core_seed.begin(), core_seed.end(), options.seed);
    options.flags = DUEL_MODE_MR5;
    options.team1 = OCG_Player{8000, 5, 1};
    options.team2 = OCG_Player{8000, 5, 1};
    options.cardReader = &Duel::read_card;
    options.payload1 = this;
    options.scriptReader = &Duel::read_script;
    options.payload2 = this;
    options.logHandler = &Duel::handle_log;
    options.payload3 = this;
    options.enableUnsafeLibraries = 0;

    const int creation_status = OCG_CreateDuel(&duel_, &options);
    if(creation_status != OCG_DUEL_CREATION_SUCCESS)
        throw std::runtime_error(creation_error(creation_status));

    try {
        const auto lua_seed = "math.randomseed(" + std::to_string(seed & 0xffffffffULL)
            + "," + std::to_string(seed >> 32) + ")";
        if(!OCG_LoadScript(duel_, lua_seed.data(), static_cast<std::uint32_t>(lua_seed.size()),
                          "ygo-gym.randomseed"))
            throw std::runtime_error("failed to initialize Lua randomness");
        if(!load_script("constant.lua"))
            throw std::runtime_error("failed to load constant.lua");
        if(!load_script("utility.lua"))
            throw std::runtime_error("failed to load utility.lua");
        throw_script_errors("loading base scripts");

        add_deck(0, player1_main, player1_extra);
        add_deck(1, player2_main, player2_extra);
        throw_script_errors("loading card scripts");

        OCG_StartDuel(duel_);
        process_until_blocked();
        update_decision();
        throw_script_errors("starting duel");
    } catch(...) {
        close();
        throw;
    }
}

void Duel::add_deck(
    std::uint8_t player,
    const std::vector<std::uint32_t>& main,
    const std::vector<std::uint32_t>& extra
) {
    OCG_NewCardInfo info{};
    info.team = player;
    info.duelist = 0;
    info.con = player;
    info.seq = 0;
    info.pos = POS_FACEDOWN_DEFENSE;

    info.loc = LOCATION_DECK;
    for(auto card = main.rbegin(); card != main.rend(); ++card) {
        info.code = *card;
        OCG_DuelNewCard(duel_, &info);
    }

    info.loc = LOCATION_EXTRA;
    for(auto card = extra.rbegin(); card != extra.rend(); ++card) {
        info.code = *card;
        OCG_DuelNewCard(duel_, &info);
    }
}

}
