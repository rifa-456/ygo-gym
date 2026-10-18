#include "duel/duel.h"

#include <stdexcept>
#include <utility>
#include "ygopro-core/ocgapi_constants.h"

#include <fstream>
#include <limits>

namespace ygo_gym {
namespace {
bool read_script_source(const EngineState& engine, const char* name, std::string& source) {
    for(const auto& root : engine.script_roots) {
        const auto path = root / name;
        std::ifstream file(path, std::ios::binary | std::ios::ate);
        if(!file)
            continue;

        const auto end = file.tellg();
        if(end < 0)
            return false;
        const auto size = static_cast<std::size_t>(end);
        if(size > std::numeric_limits<std::uint32_t>::max())
            return false;

        source.assign(size, '\0');
        file.seekg(0);
        if(!source.empty() && !file.read(source.data(), static_cast<std::streamsize>(size)))
            return false;
        return true;
    }
    return false;
}
}

void Duel::read_card(void* payload, std::uint32_t code, OCG_CardData* data) noexcept {
    const auto* self = static_cast<const Duel*>(payload);
    const auto found = self->engine_->cards.find(code);
    if(found == self->engine_->cards.end())
        return;

    const auto& card = found->second;
    data->code = card.code;
    data->alias = card.alias;
    data->setcodes = card.setcodes.empty() ? nullptr : const_cast<std::uint16_t*>(card.setcodes.data());
    data->type = card.type;
    data->level = card.level;
    data->attribute = card.attribute;
    data->race = card.race;
    data->attack = card.attack;
    data->defense = card.defense;
    data->lscale = card.lscale;
    data->rscale = card.rscale;
    data->link_marker = card.link_marker;
}

int Duel::read_script(void* payload, OCG_Duel duel, const char* name) noexcept {
    const auto* self = static_cast<const Duel*>(payload);
    try {
        std::string source;
        if(!read_script_source(*self->engine_, name, source))
            return 0;
        return OCG_LoadScript(duel, source.data(), static_cast<std::uint32_t>(source.size()), name);
    } catch(...) {
        return 0;
    }
}

void Duel::handle_log(void* payload, const char* message, int type) noexcept {
    if(type != OCG_LOG_TYPE_ERROR)
        return;
    auto* self = static_cast<Duel*>(payload);
    try {
        self->script_errors_.emplace_back(message == nullptr ? "unknown script error" : message);
    } catch(...) {
    }
}

bool Duel::load_script(const char* name) {
    std::string source;
    if(!read_script_source(*engine_, name, source))
        return false;
    return OCG_LoadScript(duel_, source.data(), static_cast<std::uint32_t>(source.size()), name) != 0;
}

void Duel::throw_script_errors(const char* context) {
    if(script_errors_.empty())
        return;
    const auto message = script_errors_.front();
    script_errors_.clear();
    throw std::runtime_error(std::string(context) + ": " + message);
}

}
