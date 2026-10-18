#include "state.h"

#include <algorithm>
#include <cstdint>
#include <type_traits>
#include <vector>

#include "legality.h"
#include "ocgapi_constants.h"

namespace ygo_gym::action {
namespace {

template<typename T>
bool contains(const std::vector<T>& values, T value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

void add_card_actions(
    std::vector<Action>& actions,
    const state::ObservationStorage& observation,
    ActionKind kind,
    const std::vector<protocol::CardRef>& cards
) {
    for(std::uint32_t index = 0; index < cards.size(); ++index) {
        actions.emplace_back(CardAction{
            kind,
            observation.card_id(cards[index]),
            cards[index],
            index,
        });
    }
}

void add_effect_actions(
    std::vector<Action>& actions,
    const state::ObservationStorage& observation,
    ActionKind kind,
    const std::vector<protocol::EffectRef>& effects
) {
    for(std::uint32_t index = 0; index < effects.size(); ++index) {
        const auto& effect = effects[index];
        actions.emplace_back(EffectAction{
            kind,
            observation.card_id(effect.card),
            effect.description,
            effect.client_mode,
            effect,
            index,
        });
    }
}

std::vector<std::uint8_t> positions(std::uint8_t mask) {
    std::vector<std::uint8_t> result;
    for(const auto position : {POS_FACEUP_ATTACK, POS_FACEDOWN_ATTACK, POS_FACEUP_DEFENSE, POS_FACEDOWN_DEFENSE}) {
        if((mask & position) != 0)
            result.push_back(static_cast<std::uint8_t>(position));
    }
    return result;
}

std::vector<std::uint64_t> bits(std::uint64_t mask) {
    std::vector<std::uint64_t> result;
    for(std::uint8_t bit = 0; bit < 64; ++bit) {
        const auto value = std::uint64_t{1} << bit;
        if((mask & value) != 0)
            result.push_back(value);
    }
    return result;
}

std::vector<std::uint32_t> bits(std::uint32_t mask) {
    std::vector<std::uint32_t> result;
    for(std::uint8_t bit = 0; bit < 32; ++bit) {
        const auto value = std::uint32_t{1} << bit;
        if((mask & value) != 0)
            result.push_back(value);
    }
    return result;
}

}

void State::rebuild_actions() {
    actions_.clear();
    std::visit([this](const auto& decision) {
        using T = std::decay_t<decltype(decision)>;
        if constexpr(std::is_same_v<T, protocol::BattleDecision>) {
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
        } else if constexpr(std::is_same_v<T, protocol::IdleDecision>) {
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
        } else if constexpr(std::is_same_v<T, protocol::EffectYesNoDecision>) {
            actions_.emplace_back(SimpleAction{ActionKind::yes});
            actions_.emplace_back(SimpleAction{ActionKind::no});
        } else if constexpr(std::is_same_v<T, protocol::YesNoDecision>) {
            actions_.emplace_back(SimpleAction{ActionKind::yes});
            actions_.emplace_back(SimpleAction{ActionKind::no});
        } else if constexpr(std::is_same_v<T, protocol::OptionDecision>) {
            for(std::uint32_t index = 0; index < decision.options.size(); ++index)
                actions_.emplace_back(OptionAction{ActionKind::option, index, decision.options[index]});
        } else if constexpr(std::is_same_v<T, protocol::CardDecision>) {
            if(auto* selected = std::get_if<CardSelection>(&selection_)) {
                if(selected->indices.size() < decision.max) {
                    for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                        if(!contains(selected->indices, index))
                            actions_.emplace_back(CardAction{
                                ActionKind::select_card,
                                observation_->card_id(decision.cards[index]),
                                decision.cards[index],
                                index,
                            });
                    }
                }
                if(selected->indices.size() >= decision.min)
                    actions_.emplace_back(SimpleAction{ActionKind::confirm});
            } else {
                add_card_actions(actions_, *observation_, ActionKind::select_card, decision.cards);
                if(decision.min == 0)
                    actions_.emplace_back(SimpleAction{ActionKind::confirm});
            }
            if(decision.cancelable)
                actions_.emplace_back(SimpleAction{ActionKind::cancel});
        } else if constexpr(std::is_same_v<T, protocol::ChainDecision>) {
            add_effect_actions(actions_, *observation_, ActionKind::activate, decision.options);
            if(!decision.forced)
                actions_.emplace_back(SimpleAction{ActionKind::pass});
        } else if constexpr(std::is_same_v<T, protocol::PlaceDecision>) {
            const auto selected = std::get_if<ZoneSelection>(&selection_);
            const auto zones = available_zones(
                decision,
                selected == nullptr ? std::vector<protocol::ZoneRef>{} : selected->zones
            );
            for(const auto& zone : zones)
                actions_.emplace_back(ZoneAction{ActionKind::select_zone, zone});
        } else if constexpr(std::is_same_v<T, protocol::PositionDecision>) {
            for(const auto position : positions(decision.positions))
                actions_.emplace_back(PositionAction{ActionKind::select_position, position});
        } else if constexpr(std::is_same_v<T, protocol::TributeDecision>) {
            if(auto* selected = std::get_if<CardSelection>(&selection_)) {
                if(selected->indices.size() < decision.max) {
                    for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                        if(contains(selected->indices, index))
                            continue;
                        auto candidate = selected->indices;
                        candidate.push_back(index);
                        if(tribute_can_complete(decision, candidate))
                            actions_.emplace_back(TributeAction{
                                ActionKind::select_tribute,
                                observation_->card_id(decision.cards[index].card),
                                decision.cards[index].value,
                                decision.cards[index],
                                index,
                            });
                    }
                }
                if(tribute_complete(decision, selected->indices))
                    actions_.emplace_back(SimpleAction{ActionKind::confirm});
            } else {
                for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                    if(decision.cards[index].value >= decision.min)
                        actions_.emplace_back(TributeAction{
                                ActionKind::select_tribute,
                                observation_->card_id(decision.cards[index].card),
                                decision.cards[index].value,
                                decision.cards[index],
                                index,
                            });
                }
            }
            if(decision.cancelable)
                actions_.emplace_back(SimpleAction{ActionKind::cancel});
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            if(auto* selected = std::get_if<CounterSelection>(&selection_)) {
                const auto remaining = static_cast<std::uint16_t>(decision.count - selected->total);
                for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                    if(selected->assigned[index])
                        continue;
                    std::uint32_t capacity_elsewhere = 0;
                    for(std::uint32_t other = 0; other < decision.cards.size(); ++other) {
                        if(other != index && !selected->assigned[other])
                            capacity_elsewhere += decision.cards[other].available;
                    }
                    const auto maximum = std::min<std::uint16_t>(decision.cards[index].available, remaining);
                    for(std::uint16_t count = 1; count <= maximum; ++count) {
                        if(static_cast<std::uint32_t>(remaining - count) <= capacity_elsewhere) {
                            actions_.emplace_back(CounterAction{
                                ActionKind::allocate_counter,
                                observation_->card_id(decision.cards[index].card),
                                decision.cards[index].available,
                                count,
                                decision.cards[index],
                                index,
                            });
                        }
                    }
                }
            } else {
                for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                    if(decision.cards[index].available != 0)
                        actions_.emplace_back(CounterAction{
                            ActionKind::allocate_counter,
                            observation_->card_id(decision.cards[index].card),
                            decision.cards[index].available,
                            1,
                            decision.cards[index],
                            index,
                        });
                }
            }
        } else if constexpr(std::is_same_v<T, protocol::SumDecision>) {
            auto& selected = std::get<CardSelection>(selection_);
            for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                if(contains(selected.indices, index))
                    continue;
                auto candidate = selected.indices;
                candidate.push_back(index);
                if(sum_can_complete(decision, candidate))
                    actions_.emplace_back(SumAction{
                        ActionKind::select_sum_card,
                        observation_->card_id(decision.cards[index].card),
                        decision.cards[index].value,
                        decision.cards[index],
                        index,
                    });
            }
            if(sum_complete(decision, selected.indices))
                actions_.emplace_back(SimpleAction{ActionKind::confirm});
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            if(auto* selected = std::get_if<SortSelection>(&selection_)) {
                for(std::uint32_t index = 0; index < decision.cards.size(); ++index) {
                    if(!selected->selected[index])
                        actions_.emplace_back(CardAction{
                            ActionKind::order_card,
                            observation_->card_id(decision.cards[index]),
                            decision.cards[index],
                            index,
                        });
                }
            } else {
                actions_.emplace_back(CardAction{
                    ActionKind::order_card,
                    observation_->card_id(decision.cards[0]),
                    decision.cards[0],
                    0,
                });
            }
            actions_.emplace_back(SimpleAction{ActionKind::cancel});
        } else if constexpr(std::is_same_v<T, protocol::UnselectCardDecision>) {
            add_card_actions(actions_, *observation_, ActionKind::select_card, decision.selectable);
            for(std::uint32_t index = 0; index < decision.unselectable.size(); ++index) {
                actions_.emplace_back(CardAction{
                    ActionKind::unselect_card,
                    observation_->card_id(decision.unselectable[index]),
                    decision.unselectable[index],
                    static_cast<std::uint32_t>(decision.selectable.size()) + index,
                });
            }
            if(decision.finishable)
                actions_.emplace_back(SimpleAction{ActionKind::confirm});
            else if(decision.cancelable)
                actions_.emplace_back(SimpleAction{ActionKind::cancel});
        } else if constexpr(std::is_same_v<T, protocol::AnnounceRaceDecision>) {
            if(auto* selected = std::get_if<BitSelection>(&selection_)) {
                for(const auto race : bits(decision.available & ~selected->mask))
                    actions_.emplace_back(RaceAction{ActionKind::select_race, race});
            } else {
                for(const auto race : bits(decision.available))
                    actions_.emplace_back(RaceAction{ActionKind::select_race, race});
            }
        } else if constexpr(std::is_same_v<T, protocol::AnnounceAttributeDecision>) {
            if(auto* selected = std::get_if<BitSelection>(&selection_)) {
                const auto remaining = decision.available & ~static_cast<std::uint32_t>(selected->mask);
                for(const auto attribute : bits(remaining))
                    actions_.emplace_back(AttributeAction{ActionKind::select_attribute, attribute});
            } else {
                for(const auto attribute : bits(decision.available))
                    actions_.emplace_back(AttributeAction{ActionKind::select_attribute, attribute});
            }
        } else if constexpr(std::is_same_v<T, protocol::AnnounceCardDecision>) {
            for(const auto code : declarable_cards(*engine_, decision))
                actions_.emplace_back(CardCodeAction{ActionKind::announce_card, code});
        } else if constexpr(std::is_same_v<T, protocol::AnnounceNumberDecision>) {
            for(std::uint32_t index = 0; index < decision.options.size(); ++index)
                actions_.emplace_back(NumberAction{ActionKind::announce_number, index, decision.options[index]});
        } else if constexpr(std::is_same_v<T, protocol::RockPaperScissorsDecision>) {
            actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::rock});
            actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::paper});
            actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::scissors});
        }
    }, decision_);
}

}
