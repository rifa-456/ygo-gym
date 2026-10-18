#include "event/decoding/transition_builder.h"
#include "ygopro-core/ocgapi_constants.h"

namespace ygo_gym::event {

void TransitionBuilder::message(const std::uint8_t* data, std::size_t size) {
    if(size == 0)
        return;
    Reader reader(data, size);
    const auto type = reader.read<std::uint8_t>();
    switch(type) {
    case MSG_WIN:
        win(reader);
        break;
    case MSG_CONFIRM_DECKTOP:
    case MSG_CONFIRM_EXTRATOP:
    case MSG_CONFIRM_CARDS:
        confirm(reader, type);
        break;
    case MSG_SHUFFLE_DECK:
        shuffle_simple(reader, LOCATION_DECK);
        break;
    case MSG_SHUFFLE_HAND:
        shuffle_cards(reader, LOCATION_HAND);
        break;
    case MSG_SHUFFLE_EXTRA:
        shuffle_cards(reader, LOCATION_EXTRA);
        break;
    case MSG_SWAP_GRAVE_DECK: {
        const auto player = reader.read<std::uint8_t>();
        transition_.events.emplace_back(GraveDeckSwapEvent{player});
        clear_zone(player, LOCATION_DECK);
        clear_zone(player, LOCATION_GRAVE);
        break;
    }
    case MSG_REVERSE_DECK:
        transition_.events.emplace_back(DeckReverseEvent{});
        clear_zone(0xff, LOCATION_DECK);
        break;
    case MSG_DECK_TOP:
        deck_top(reader);
        break;
    case MSG_NEW_TURN:
        transition_.events.emplace_back(TurnEvent{reader.read<std::uint8_t>()});
        break;
    case MSG_NEW_PHASE:
        transition_.events.emplace_back(PhaseEvent{reader.read<std::uint16_t>()});
        break;
    case MSG_MOVE:
        move(reader);
        break;
    case MSG_POS_CHANGE:
        position(reader);
        break;
    case MSG_SET:
        set(reader);
        break;
    case MSG_SUMMONING:
        summon(reader, SummonKind::normal, SummonStage::attempt, true);
        break;
    case MSG_SUMMONED:
        complete_summon(SummonKind::normal);
        break;
    case MSG_SPSUMMONING:
        summon(reader, SummonKind::special, SummonStage::attempt, false);
        break;
    case MSG_SPSUMMONED:
        complete_summon(SummonKind::special);
        break;
    case MSG_FLIPSUMMONING:
        summon(reader, SummonKind::flip, SummonStage::attempt, true);
        break;
    case MSG_FLIPSUMMONED:
        complete_summon(SummonKind::flip);
        break;
    case MSG_CHAINING:
        chaining(reader);
        break;
    case MSG_CHAINED:
        chain_stage(reader, ChainStage::added);
        break;
    case MSG_CHAIN_SOLVING:
        chain_stage(reader, ChainStage::resolving);
        break;
    case MSG_CHAIN_SOLVED:
        chain_stage(reader, ChainStage::resolved);
        break;
    case MSG_CHAIN_NEGATED:
        chain_stage(reader, ChainStage::negated);
        break;
    case MSG_CHAIN_DISABLED:
        chain_stage(reader, ChainStage::disabled);
        break;
    case MSG_CHAIN_END:
        transition_.events.emplace_back(ChainEvent{ChainStage::ended, std::nullopt, std::nullopt, std::nullopt, std::nullopt});
        chain_.clear();
        break;
    case MSG_DRAW:
        draw(reader);
        break;
    case MSG_DAMAGE:
        life(reader, LifePointKind::damage);
        break;
    case MSG_RECOVER:
        life(reader, LifePointKind::recover);
        break;
    case MSG_PAY_LPCOST:
        life(reader, LifePointKind::pay);
        break;
    case MSG_LPUPDATE:
        life_set(reader);
        break;
    case MSG_ADD_COUNTER:
        counter(reader, 1);
        break;
    case MSG_REMOVE_COUNTER:
        counter(reader, -1);
        break;
    case MSG_EQUIP:
        relation(reader, RelationEventKind::equip);
        break;
    case MSG_CARD_TARGET:
        relation(reader, RelationEventKind::target);
        break;
    case MSG_CANCEL_TARGET:
        relation(reader, RelationEventKind::cancel_target);
        break;
    case MSG_ATTACK:
        attack(reader);
        break;
    case MSG_BATTLE:
        battle(reader);
        break;
    case MSG_TOSS_COIN:
        random(reader, RandomKind::coin);
        break;
    case MSG_TOSS_DICE:
        random(reader, RandomKind::dice);
        break;
    case MSG_DAMAGE_STEP_START:
        transition_.events.emplace_back(DamageStepEvent{DamageStepStage::start});
        break;
    case MSG_DAMAGE_STEP_END:
        transition_.events.emplace_back(DamageStepEvent{DamageStepStage::end});
        break;
    default:
        break;
    }
}

}
