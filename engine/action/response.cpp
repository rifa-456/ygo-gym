#include "action/state.h"

#include <type_traits>

namespace ygo_gym::action {

std::optional<protocol::Response> State::apply(const Action& action) {
    return std::visit([this, &action](const auto& decision) -> std::optional<protocol::Response> {
        using T = std::decay_t<decltype(decision)>;
        const auto action_kind = kind(action);
        if constexpr(std::is_same_v<T, protocol::BattleDecision>) {
            if(const auto* effect = std::get_if<EffectAction>(&action))
                return decision.response(protocol::BattleCommand::activate, effect->source_index);
            if(const auto* attack = std::get_if<AttackAction>(&action))
                return decision.response(protocol::BattleCommand::attack, attack->source_index);
            if(action_kind == ActionKind::main_phase_2)
                return decision.response(protocol::BattleCommand::main_phase_2);
            return decision.response(protocol::BattleCommand::end_phase);
        } else if constexpr(std::is_same_v<T, protocol::IdleDecision>) {
            if(const auto* card = std::get_if<CardAction>(&action)) {
                switch(card->kind) {
                case ActionKind::summon:
                    return decision.response(protocol::IdleCommand::summon, card->source_index);
                case ActionKind::special_summon:
                    return decision.response(protocol::IdleCommand::special_summon, card->source_index);
                case ActionKind::reposition:
                    return decision.response(protocol::IdleCommand::reposition, card->source_index);
                case ActionKind::set_monster:
                    return decision.response(protocol::IdleCommand::set_monster, card->source_index);
                default:
                    return decision.response(protocol::IdleCommand::set_spell_trap, card->source_index);
                }
            }
            if(const auto* effect = std::get_if<EffectAction>(&action))
                return decision.response(protocol::IdleCommand::activate, effect->source_index);
            if(action_kind == ActionKind::battle_phase)
                return decision.response(protocol::IdleCommand::battle_phase);
            if(action_kind == ActionKind::end_phase)
                return decision.response(protocol::IdleCommand::end_phase);
            return decision.response(protocol::IdleCommand::shuffle_hand);
        } else if constexpr(std::is_same_v<T, protocol::EffectYesNoDecision>) {
            return decision.response(action_kind == ActionKind::yes);
        } else if constexpr(std::is_same_v<T, protocol::YesNoDecision>) {
            return decision.response(action_kind == ActionKind::yes);
        } else if constexpr(std::is_same_v<T, protocol::OptionDecision>) {
            return decision.response(std::get<OptionAction>(action).index);
        } else if constexpr(std::is_same_v<T, protocol::CardDecision>) {
            if(action_kind == ActionKind::cancel)
                return decision.cancel_response();
            if(action_kind == ActionKind::confirm) {
                if(const auto* selected = std::get_if<CardSelection>(&selection_))
                    return decision.response(selected->indices);
                return decision.response({});
            }
            const auto index = std::get<CardAction>(action).source_index;
            if(auto* selected = std::get_if<CardSelection>(&selection_)) {
                selected->indices.push_back(index);
                return std::nullopt;
            }
            return decision.response({index});
        } else if constexpr(std::is_same_v<T, protocol::ChainDecision>) {
            if(action_kind == ActionKind::pass)
                return decision.pass_response();
            return decision.response(std::get<EffectAction>(action).source_index);
        } else if constexpr(std::is_same_v<T, protocol::PlaceDecision>) {
            const auto zone = std::get<ZoneAction>(action).zone;
            if(auto* selected = std::get_if<ZoneSelection>(&selection_)) {
                selected->zones.push_back(zone);
                if(selected->zones.size() == decision.count)
                    return decision.response(selected->zones);
                return std::nullopt;
            }
            return decision.response({zone});
        } else if constexpr(std::is_same_v<T, protocol::PositionDecision>) {
            return decision.response(std::get<PositionAction>(action).position);
        } else if constexpr(std::is_same_v<T, protocol::TributeDecision>) {
            if(action_kind == ActionKind::cancel)
                return decision.cancel_response();
            if(action_kind == ActionKind::confirm)
                return decision.response(std::get<CardSelection>(selection_).indices);
            const auto index = std::get<TributeAction>(action).source_index;
            if(auto* selected = std::get_if<CardSelection>(&selection_)) {
                selected->indices.push_back(index);
                return std::nullopt;
            }
            return decision.response({index});
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            const auto& counter = std::get<CounterAction>(action);
            if(auto* selected = std::get_if<CounterSelection>(&selection_)) {
                selected->counts[counter.source_index] = counter.count;
                selected->assigned[counter.source_index] = true;
                selected->total = static_cast<std::uint16_t>(selected->total + counter.count);
                if(selected->total == decision.count)
                    return decision.response(selected->counts);
                return std::nullopt;
            }
            std::vector<std::uint16_t> counts(decision.cards.size(), 0);
            counts[counter.source_index] = counter.count;
            return decision.response(counts);
        } else if constexpr(std::is_same_v<T, protocol::SumDecision>) {
            if(action_kind == ActionKind::confirm)
                return decision.response(std::get<CardSelection>(selection_).indices);
            std::get<CardSelection>(selection_).indices.push_back(std::get<SumAction>(action).source_index);
            return std::nullopt;
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            if(action_kind == ActionKind::cancel)
                return decision.cancel_response();
            const auto index = std::get<CardAction>(action).source_index;
            if(auto* selected = std::get_if<SortSelection>(&selection_)) {
                selected->order.push_back(static_cast<std::uint8_t>(index));
                selected->selected[index] = true;
                if(selected->order.size() == decision.cards.size())
                    return decision.response(selected->order);
                return std::nullopt;
            }
            return decision.response({0});
        } else if constexpr(std::is_same_v<T, protocol::UnselectCardDecision>) {
            if(action_kind == ActionKind::confirm || action_kind == ActionKind::cancel)
                return decision.finish_response();
            return decision.response(std::get<CardAction>(action).source_index);
        } else if constexpr(std::is_same_v<T, protocol::AnnounceRaceDecision>) {
            const auto race = std::get<RaceAction>(action).race;
            if(auto* selected = std::get_if<BitSelection>(&selection_)) {
                selected->mask |= race;
                ++selected->count;
                if(selected->count == decision.count)
                    return decision.response(selected->mask);
                return std::nullopt;
            }
            return decision.response(race);
        } else if constexpr(std::is_same_v<T, protocol::AnnounceAttributeDecision>) {
            const auto attribute = std::get<AttributeAction>(action).attribute;
            if(auto* selected = std::get_if<BitSelection>(&selection_)) {
                selected->mask |= attribute;
                ++selected->count;
                if(selected->count == decision.count)
                    return decision.response(static_cast<std::uint32_t>(selected->mask));
                return std::nullopt;
            }
            return decision.response(attribute);
        } else if constexpr(std::is_same_v<T, protocol::AnnounceCardDecision>) {
            return decision.response(std::get<CardCodeAction>(action).code);
        } else if constexpr(std::is_same_v<T, protocol::AnnounceNumberDecision>) {
            return decision.response(std::get<NumberAction>(action).index);
        } else {
            return decision.response(std::get<RpsAction>(action).choice);
        }
    }, decision_);
}

}
