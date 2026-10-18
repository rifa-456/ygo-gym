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

}
