#include "backend.h"

#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>

namespace ygo_gym {
namespace {

std::string creation_error(int status) {
    switch(status) {
    case OCG_DUEL_CREATION_NO_OUTPUT:
        return "ocgcore did not receive an output pointer";
    case OCG_DUEL_CREATION_NOT_CREATED:
        return "ocgcore could not allocate a duel";
    case OCG_DUEL_CREATION_NULL_DATA_READER:
        return "ocgcore requires a card data reader";
    case OCG_DUEL_CREATION_NULL_SCRIPT_READER:
        return "ocgcore requires a script reader";
    case OCG_DUEL_CREATION_INCOMPATIBLE_LUA_API:
        return "ocgcore rejected the linked Lua runtime";
    case OCG_DUEL_CREATION_NULL_RNG_SEED:
        return "ocgcore requires a non-zero RNG seed";
    default:
        return "ocgcore duel creation failed with status " + std::to_string(status);
    }
}

}

Duel::Duel(std::shared_ptr<const BackendState> backend, const std::array<std::uint64_t, 4>& seed)
    : backend_(std::move(backend)) {
    OCG_DuelOptions options{};
    for(std::size_t index = 0; index < seed.size(); ++index)
        options.seed[index] = seed[index];
    options.team1 = OCG_Player{8000, 5, 1};
    options.team2 = OCG_Player{8000, 5, 1};
    options.cardReader = &Duel::read_card;
    options.payload1 = const_cast<BackendState*>(backend_.get());
    options.scriptReader = &Duel::read_script;
    options.payload2 = const_cast<BackendState*>(backend_.get());
    options.enableUnsafeLibraries = 0;

    const int status = OCG_CreateDuel(&duel_, &options);
    if(status != OCG_DUEL_CREATION_SUCCESS)
        throw std::runtime_error(creation_error(status));
}

Duel::~Duel() {
    close();
}

void Duel::close() noexcept {
    if(duel_ == nullptr)
        return;
    OCG_DestroyDuel(duel_);
    duel_ = nullptr;
}

bool Duel::closed() const noexcept {
    return duel_ == nullptr;
}

void Duel::read_card(void*, std::uint32_t code, OCG_CardData* data) noexcept {
    *data = OCG_CardData{};
    data->code = code;
}

int Duel::read_script(void* payload, OCG_Duel duel, const char* name) noexcept {
    const auto* backend = static_cast<const BackendState*>(payload);
    try {
        for(const auto& root : backend->script_roots) {
            const auto path = root / name;
            std::ifstream file(path, std::ios::binary | std::ios::ate);
            if(!file)
                continue;

            const auto end = file.tellg();
            if(end < 0)
                return 0;
            const auto size = static_cast<std::size_t>(end);
            if(size > std::numeric_limits<std::uint32_t>::max())
                return 0;

            std::string source(size, '\0');
            file.seekg(0);
            if(!source.empty() && !file.read(source.data(), static_cast<std::streamsize>(size)))
                return 0;

            return OCG_LoadScript(
                duel,
                source.data(),
                static_cast<std::uint32_t>(source.size()),
                name
            );
        }
    } catch(...) {
        return 0;
    }
    return 0;
}

Backend::Backend(std::filesystem::path card_database, std::vector<std::filesystem::path> script_roots) {
    if(!std::filesystem::is_regular_file(card_database))
        throw std::invalid_argument("card database does not exist: " + card_database.string());
    if(script_roots.empty())
        throw std::invalid_argument("at least one script root is required");
    for(const auto& root : script_roots) {
        if(!std::filesystem::is_directory(root))
            throw std::invalid_argument("script root does not exist: " + root.string());
    }

    state_ = std::make_shared<BackendState>(BackendState{
        std::move(card_database),
        std::move(script_roots),
    });
}

std::pair<int, int> Backend::core_version() const noexcept {
    int major = 0;
    int minor = 0;
    OCG_GetVersion(&major, &minor);
    return {major, minor};
}

std::unique_ptr<Duel> Backend::create_duel(const std::array<std::uint64_t, 4>& seed) const {
    return std::make_unique<Duel>(state_, seed);
}

}
