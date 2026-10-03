#include "duel.h"

#include <algorithm>
#include <array>
#include <fstream>
#include <limits>
#include <random>
#include <stdexcept>
#include <string>
#include <utility>

#include "ocgapi_constants.h"
#include "protocol/decoder.h"

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

Duel::~Duel() {
    close();
}

void Duel::close() noexcept {
    if(duel_ != nullptr) {
        OCG_DestroyDuel(duel_);
        duel_ = nullptr;
    }
    status_ = OCG_DUEL_STATUS_END;
    decision_.reset();
    action_state_.reset();
}

bool Duel::closed() const noexcept {
    return duel_ == nullptr;
}

int Duel::status() const noexcept {
    return status_;
}

const std::vector<std::uint8_t>& Duel::message_buffer() const noexcept {
    return message_buffer_;
}

const std::optional<protocol::Decision>& Duel::decision() const noexcept {
    return decision_;
}

const std::vector<action::Action>& Duel::actions() const noexcept {
    static const std::vector<action::Action> empty;
    return action_state_ ? action_state_->actions() : empty;
}

const std::vector<action::Action>& Duel::pending_actions() const noexcept {
    static const std::vector<action::Action> empty;
    return action_state_ ? action_state_->pending_actions() : empty;
}

void Duel::respond(const protocol::Response& response) {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    if(status_ != OCG_DUEL_STATUS_AWAITING || !decision_)
        throw std::runtime_error("duel is not awaiting a response");
    if(response.kind != protocol::kind(*decision_))
        throw std::invalid_argument("response does not match the current decision");
    submit_response(response, false);
}

void Duel::step(std::uint32_t action_index) {
    if(duel_ == nullptr)
        throw std::runtime_error("duel is closed");
    if(status_ != OCG_DUEL_STATUS_AWAITING || !action_state_)
        throw std::runtime_error("duel has no legal action to step");
    if(auto response = action_state_->step(action_index))
        submit_response(*response, true);
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

void Duel::process_until_blocked() {
    message_buffer_.clear();
    do {
        status_ = OCG_DuelProcess(duel_);
        std::uint32_t length = 0;
        const auto* buffer = static_cast<const std::uint8_t*>(OCG_DuelGetMessage(duel_, &length));
        if(length != 0)
            message_buffer_.insert(message_buffer_.end(), buffer, buffer + length);
        throw_script_errors("processing duel");
    } while(status_ == OCG_DUEL_STATUS_CONTINUE);
}

void Duel::submit_response(const protocol::Response& response, bool semantic_action) {
    OCG_DuelSetResponse(duel_, response.data.data(), static_cast<std::uint32_t>(response.data.size()));
    process_until_blocked();
    if(protocol::contains_retry(message_buffer_)) {
        if(semantic_action)
            throw std::runtime_error("generated semantic action was rejected by ocgcore");
        throw std::invalid_argument("ocgcore rejected the response");
    }
    update_decision();
}

void Duel::update_decision() {
    if(status_ == OCG_DUEL_STATUS_END) {
        decision_.reset();
        action_state_.reset();
        return;
    }
    if(status_ != OCG_DUEL_STATUS_AWAITING)
        throw std::runtime_error("ocgcore stopped with an unexpected duel status");
    auto decision = protocol::decode_decision(message_buffer_);
    if(!decision)
        throw std::runtime_error("ocgcore is awaiting input without a supported decision message");
    decision_ = std::move(decision);
    action_state_.emplace(*decision_, engine_);
}

void Duel::throw_script_errors(const char* context) {
    if(script_errors_.empty())
        return;
    const auto message = script_errors_.front();
    script_errors_.clear();
    throw std::runtime_error(std::string(context) + ": " + message);
}

}
