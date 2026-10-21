#pragma once

#include <array>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "action/state.h"
#include "engine.h"
#include "event/event.h"
#include "ygopro-core/ocgapi.h"
#include "protocol/decisions/decision.h"
#include "state/observation.h"
#include "state/state.h"

namespace ygo_gym {

struct Outcome {
    std::optional<std::uint8_t> winner;
    std::uint8_t reason{};

    [[nodiscard]] std::array<float, 2> rewards() const noexcept;
};

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

    [[nodiscard]] std::unique_ptr<Duel> clone() const;
    void close() noexcept;
    void respond(const protocol::Response& response);
    void step(std::uint32_t action_index);

    [[nodiscard]] bool closed() const noexcept;
    [[nodiscard]] bool terminated() const noexcept;
    [[nodiscard]] std::optional<std::uint8_t> current_player() const noexcept;
    [[nodiscard]] const std::optional<Outcome>& outcome() const noexcept;
    [[nodiscard]] std::array<float, 2> rewards() const noexcept;
    [[nodiscard]] int status() const noexcept;
    [[nodiscard]] const std::vector<std::uint8_t>& message_buffer() const noexcept;
    [[nodiscard]] const std::optional<protocol::Decision>& decision() const noexcept;
    [[nodiscard]] const std::vector<action::Action>& actions() const noexcept;
    [[nodiscard]] const std::vector<action::Action>& pending_actions() const noexcept;
    [[nodiscard]] const state::Observation& observation() const;
    [[nodiscard]] state::Observation observe(std::uint8_t viewer) const;
    [[nodiscard]] state::State state() const;

private:
    explicit Duel(std::shared_ptr<const EngineState> engine);

    static void read_card(void* payload, std::uint32_t code, OCG_CardData* data) noexcept;
    static int read_script(void* payload, OCG_Duel duel, const char* name) noexcept;
    static void handle_log(void* payload, const char* message, int type) noexcept;

    bool load_script(const char* name);
    void add_deck(std::uint8_t player, const std::vector<std::uint32_t>& main, const std::vector<std::uint32_t>& extra);
    void process_until_blocked();
    void submit_response(const protocol::Response& response, bool semantic_action);
    void update_decision();
    void update_outcome();
    void throw_script_errors(const char* context);

    std::shared_ptr<const EngineState> engine_;
    OCG_Duel duel_{nullptr};
    int status_{OCG_DUEL_STATUS_END};
    std::vector<std::uint8_t> message_buffer_;
    bool terminated_{false};
    std::optional<Outcome> outcome_;
    std::optional<protocol::Decision> decision_;
    std::optional<action::State> action_state_;
    std::optional<state::Observation> observation_;
    event::Transition transition_events_;
    std::vector<std::string> script_errors_;
};

}
