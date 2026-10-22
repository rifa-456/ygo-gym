#include "duel/duel.h"

#include <limits>
#include <stdexcept>
#include <utility>

namespace ygo_gym {

Duel::Duel(std::shared_ptr<const EngineState> engine, std::uint64_t seed,
           const std::string& source, const std::string& name)
    : engine_(std::move(engine)) {
    if(source.size() > std::numeric_limits<std::uint32_t>::max())
        throw std::invalid_argument("setup script exceeds the core size limit");
    try {
        initialize(seed);
        const auto loaded = OCG_LoadScript(duel_, source.data(),
            static_cast<std::uint32_t>(source.size()), name.c_str());
        throw_script_errors("loading duel setup");
        if(!loaded)
            throw std::runtime_error("failed to load duel setup: " + name);
        OCG_StartDuel(duel_);
        process_until_blocked();
        update_decision();
        throw_script_errors("starting duel setup");
    } catch(...) {
        close();
        throw;
    }
}

}
