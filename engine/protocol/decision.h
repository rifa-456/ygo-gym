#pragma once

#include <cstdint>
#include <optional>
#include <variant>
#include <vector>

#include "ocgapi_constants.h"

namespace ygo_gym::protocol {

enum class DecisionKind : std::uint8_t {
    battle_command = MSG_SELECT_BATTLECMD,
    idle_command = MSG_SELECT_IDLECMD,
    effect_yes_no = MSG_SELECT_EFFECTYN,
    yes_no = MSG_SELECT_YESNO,
    option = MSG_SELECT_OPTION,
    card = MSG_SELECT_CARD,
    chain = MSG_SELECT_CHAIN,
    place = MSG_SELECT_PLACE,
    position = MSG_SELECT_POSITION,
    tribute = MSG_SELECT_TRIBUTE,
    sort_chain = MSG_SORT_CHAIN,
    counter = MSG_SELECT_COUNTER,
    sum = MSG_SELECT_SUM,
    disable_field = MSG_SELECT_DISFIELD,
    sort_card = MSG_SORT_CARD,
    unselect_card = MSG_SELECT_UNSELECT_CARD,
    rock_paper_scissors = MSG_ROCK_PAPER_SCISSORS,
    announce_race = MSG_ANNOUNCE_RACE,
    announce_attribute = MSG_ANNOUNCE_ATTRIB,
    announce_card = MSG_ANNOUNCE_CARD,
    announce_number = MSG_ANNOUNCE_NUMBER,
};

enum class IdleCommand : std::uint16_t {
    summon = 0,
    special_summon = 1,
    reposition = 2,
    set_monster = 3,
    set_spell_trap = 4,
    activate = 5,
    battle_phase = 6,
    end_phase = 7,
    shuffle_hand = 8,
};

enum class BattleCommand : std::uint16_t {
    activate = 0,
    attack = 1,
    main_phase_2 = 2,
    end_phase = 3,
};

enum class RpsChoice : std::int32_t {
    rock = 1,
    paper = 2,
    scissors = 3,
};

struct Response {
    DecisionKind kind;
    std::vector<std::uint8_t> data;
};

struct CardRef {
    std::uint32_t code;
    std::uint8_t controller;
    std::uint32_t location;
    std::uint32_t sequence;
    std::optional<std::uint32_t> position;
};

struct EffectRef {
    CardRef card;
    std::uint64_t description;
    std::uint8_t client_mode;
};

struct AttackRef {
    CardRef card;
    bool direct;
};

struct TributeRef {
    CardRef card;
    std::uint8_t value;
};

struct CounterRef {
    CardRef card;
    std::uint16_t available;
};

struct SumRef {
    CardRef card;
    std::uint32_t value;
};

struct ZoneRef {
    std::uint8_t player;
    std::uint8_t location;
    std::uint8_t sequence;
};

struct BattleDecision {
    std::uint8_t player;
    std::vector<EffectRef> activatable;
    std::vector<AttackRef> attackable;
    bool can_main_phase_2;
    bool can_end_phase;

    [[nodiscard]] Response response(BattleCommand command, std::uint32_t index = 0) const;
};

struct IdleDecision {
    std::uint8_t player;
    std::vector<CardRef> summonable;
    std::vector<CardRef> special_summonable;
    std::vector<CardRef> repositionable;
    std::vector<CardRef> monster_settable;
    std::vector<CardRef> spell_trap_settable;
    std::vector<EffectRef> activatable;
    bool can_battle_phase;
    bool can_end_phase;
    bool can_shuffle_hand;

    [[nodiscard]] Response response(IdleCommand command, std::uint32_t index = 0) const;
};

struct EffectYesNoDecision {
    std::uint8_t player;
    CardRef card;
    std::uint64_t description;

    [[nodiscard]] Response response(bool yes) const;
};

struct YesNoDecision {
    std::uint8_t player;
    std::uint64_t description;

    [[nodiscard]] Response response(bool yes) const;
};

struct OptionDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
};

struct CardDecision {
    std::uint8_t player;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<CardRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
    [[nodiscard]] Response cancel_response() const;
};

struct ChainDecision {
    std::uint8_t player;
    std::uint8_t special_count;
    bool forced;
    std::uint32_t hint_timing;
    std::uint32_t opponent_hint_timing;
    std::vector<EffectRef> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
    [[nodiscard]] Response pass_response() const;
};

struct PlaceDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint32_t unavailable;
    bool disable_field;

    [[nodiscard]] Response response(const std::vector<ZoneRef>& zones) const;
};

struct PositionDecision {
    std::uint8_t player;
    std::uint32_t card_code;
    std::uint8_t positions;

    [[nodiscard]] Response response(std::uint8_t position) const;
};

struct TributeDecision {
    std::uint8_t player;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<TributeRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
    [[nodiscard]] Response cancel_response() const;
};

struct CounterDecision {
    std::uint8_t player;
    std::uint16_t counter_type;
    std::uint16_t count;
    std::vector<CounterRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint16_t>& counts) const;
};

struct SumDecision {
    std::uint8_t player;
    std::uint8_t mode;
    std::uint32_t target;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<SumRef> required;
    std::vector<SumRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint32_t>& indices) const;
};

struct SortDecision {
    std::uint8_t player;
    bool chain;
    std::vector<CardRef> cards;

    [[nodiscard]] Response response(const std::vector<std::uint8_t>& order) const;
    [[nodiscard]] Response cancel_response() const;
};

struct UnselectCardDecision {
    std::uint8_t player;
    bool finishable;
    bool cancelable;
    std::uint32_t min;
    std::uint32_t max;
    std::vector<CardRef> selectable;
    std::vector<CardRef> unselectable;

    [[nodiscard]] Response response(std::uint32_t index) const;
    [[nodiscard]] Response finish_response() const;
};

struct AnnounceRaceDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint64_t available;

    [[nodiscard]] Response response(std::uint64_t races) const;
};

struct AnnounceAttributeDecision {
    std::uint8_t player;
    std::uint8_t count;
    std::uint32_t available;

    [[nodiscard]] Response response(std::uint32_t attributes) const;
};

struct AnnounceCardDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> opcodes;

    [[nodiscard]] Response response(std::uint32_t code) const;
};

struct AnnounceNumberDecision {
    std::uint8_t player;
    std::vector<std::uint64_t> options;

    [[nodiscard]] Response response(std::uint32_t index) const;
};

struct RockPaperScissorsDecision {
    std::uint8_t player;

    [[nodiscard]] Response response(RpsChoice choice) const;
};

using Decision = std::variant<
    BattleDecision,
    IdleDecision,
    EffectYesNoDecision,
    YesNoDecision,
    OptionDecision,
    CardDecision,
    ChainDecision,
    PlaceDecision,
    PositionDecision,
    TributeDecision,
    CounterDecision,
    SumDecision,
    SortDecision,
    UnselectCardDecision,
    AnnounceRaceDecision,
    AnnounceAttributeDecision,
    AnnounceCardDecision,
    AnnounceNumberDecision,
    RockPaperScissorsDecision
>;

[[nodiscard]] DecisionKind kind(const Decision& decision) noexcept;
[[nodiscard]] std::uint8_t player(const Decision& decision) noexcept;

}
