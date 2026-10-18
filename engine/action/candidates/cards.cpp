#include "action/candidates/helpers.h"

namespace ygo_gym::action {

void State::add_candidates(const protocol::CardDecision& decision) {
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
}

void State::add_candidates(const protocol::TributeDecision& decision) {
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
}

void State::add_candidates(const protocol::SortDecision& decision) {
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
}

void State::add_candidates(const protocol::UnselectCardDecision& decision) {
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
}

}
