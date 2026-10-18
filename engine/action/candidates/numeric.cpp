#include "action/candidates/helpers.h"

namespace ygo_gym::action {

void State::add_candidates(const protocol::CounterDecision& decision) {
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
}

void State::add_candidates(const protocol::SumDecision& decision) {
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
}

}
