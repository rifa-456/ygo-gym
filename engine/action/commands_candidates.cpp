#include "candidate_helpers.h"

namespace ygo_gym::action {

void State::add_candidates(const protocol::BattleDecision& decision) {
    add_effect_actions(actions_, *observation_, ActionKind::activate, decision.activatable);
    for(std::uint32_t index = 0; index < decision.attackable.size(); ++index)
        actions_.emplace_back(AttackAction{
            ActionKind::attack,
            observation_->card_id(decision.attackable[index].card),
            decision.attackable[index].direct,
            decision.attackable[index],
            index,
        });
    if(decision.can_main_phase_2)
        actions_.emplace_back(SimpleAction{ActionKind::main_phase_2});
    if(decision.can_end_phase)
        actions_.emplace_back(SimpleAction{ActionKind::end_phase});
}

void State::add_candidates(const protocol::IdleDecision& decision) {
    add_card_actions(actions_, *observation_, ActionKind::summon, decision.summonable);
    add_card_actions(actions_, *observation_, ActionKind::special_summon, decision.special_summonable);
    add_card_actions(actions_, *observation_, ActionKind::reposition, decision.repositionable);
    add_card_actions(actions_, *observation_, ActionKind::set_monster, decision.monster_settable);
    add_card_actions(actions_, *observation_, ActionKind::set_spell_trap, decision.spell_trap_settable);
    add_effect_actions(actions_, *observation_, ActionKind::activate, decision.activatable);
    if(decision.can_battle_phase)
        actions_.emplace_back(SimpleAction{ActionKind::battle_phase});
    if(decision.can_end_phase)
        actions_.emplace_back(SimpleAction{ActionKind::end_phase});
    if(decision.can_shuffle_hand)
        actions_.emplace_back(SimpleAction{ActionKind::shuffle_hand});
}

void State::add_candidates(const protocol::EffectYesNoDecision& decision) {
    actions_.emplace_back(SimpleAction{ActionKind::yes});
    actions_.emplace_back(SimpleAction{ActionKind::no});
}

void State::add_candidates(const protocol::YesNoDecision& decision) {
    actions_.emplace_back(SimpleAction{ActionKind::yes});
    actions_.emplace_back(SimpleAction{ActionKind::no});
}

void State::add_candidates(const protocol::OptionDecision& decision) {
    for(std::uint32_t index = 0; index < decision.options.size(); ++index)
        actions_.emplace_back(OptionAction{ActionKind::option, index, decision.options[index]});
}

void State::add_candidates(const protocol::ChainDecision& decision) {
    add_effect_actions(actions_, *observation_, ActionKind::activate, decision.options);
    if(!decision.forced)
        actions_.emplace_back(SimpleAction{ActionKind::pass});
}

void State::add_candidates(const protocol::PlaceDecision& decision) {
    const auto selected = std::get_if<ZoneSelection>(&selection_);
    const auto zones = available_zones(
        decision,
        selected == nullptr ? std::vector<protocol::ZoneRef>{} : selected->zones
    );
    for(const auto& zone : zones)
        actions_.emplace_back(ZoneAction{ActionKind::select_zone, zone});
}

void State::add_candidates(const protocol::PositionDecision& decision) {
    for(const auto position : positions(decision.positions))
        actions_.emplace_back(PositionAction{ActionKind::select_position, position});
}

}
