#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "engine.h"
#include "ocgapi.h"
#include "protocol/decision.h"

namespace ygo_gym {

class Duel {
public:
    Duel(
        std::shared_ptr<const EngineState> engine,
        std::uint64_t seed,
        std::vector<std::uint32_t> player1_main,
        std::vector<std::uint32_t> player1_extra,
        std::vector<std::uint32_t> player2_main,
        std::vector<std::uint32_t> player2_extra
    );
    ~Duel();

    Duel(const Duel&) = delete;
    Duel& operator=(const Duel&) = delete;
    Duel(Duel&&) = delete;
    Duel& operator=(Duel&&) = delete;

    void close() noexcept;
    void respond(const protocol::Response& response);

    [[nodiscard]] bool closed() const noexcept;
    [[nodiscard]] int status() const noexcept;
    [[nodiscard]] const std::vector<std::uint8_t>& message_buffer() const noexcept;
    [[nodiscard]] const std::optional<protocol::Decision>& decision() const noexcept;

private:
    static void read_card(void* payload, std::uint32_t code, OCG_CardData* data) noexcept;
    static int read_script(void* payload, OCG_Duel duel, const char* name) noexcept;
    static void handle_log(void* payload, const char* message, int type) noexcept;

    bool load_script(const char* name);
    void add_deck(std::uint8_t player, const std::vector<std::uint32_t>& main, const std::vector<std::uint32_t>& extra);
    void process_until_blocked();
    void update_decision();
    void throw_script_errors(const char* context);

    std::shared_ptr<const EngineState> engine_;
    OCG_Duel duel_{nullptr};
    int status_{OCG_DUEL_STATUS_END};
    std::vector<std::uint8_t> message_buffer_;
    std::optional<protocol::Decision> decision_;
    std::vector<std::string> script_errors_;
};

}
