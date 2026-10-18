#include "action/candidates/helpers.h"

namespace ygo_gym::action {

void State::add_candidates(const protocol::AnnounceRaceDecision& decision) {
    if(auto* selected = std::get_if<BitSelection>(&selection_)) {
        for(const auto race : bits(decision.available & ~selected->mask))
            actions_.emplace_back(RaceAction{ActionKind::select_race, race});
    } else {
        for(const auto race : bits(decision.available))
            actions_.emplace_back(RaceAction{ActionKind::select_race, race});
    }
}

void State::add_candidates(const protocol::AnnounceAttributeDecision& decision) {
    if(auto* selected = std::get_if<BitSelection>(&selection_)) {
        const auto remaining = decision.available & ~static_cast<std::uint32_t>(selected->mask);
        for(const auto attribute : bits(remaining))
            actions_.emplace_back(AttributeAction{ActionKind::select_attribute, attribute});
    } else {
        for(const auto attribute : bits(decision.available))
            actions_.emplace_back(AttributeAction{ActionKind::select_attribute, attribute});
    }
}

void State::add_candidates(const protocol::AnnounceCardDecision& decision) {
    for(const auto code : declarable_cards(*engine_, decision))
        actions_.emplace_back(CardCodeAction{ActionKind::announce_card, code});
}

void State::add_candidates(const protocol::AnnounceNumberDecision& decision) {
    for(std::uint32_t index = 0; index < decision.options.size(); ++index)
        actions_.emplace_back(NumberAction{ActionKind::announce_number, index, decision.options[index]});
}

void State::add_candidates(const protocol::RockPaperScissorsDecision& decision) {
    actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::rock});
    actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::paper});
    actions_.emplace_back(RpsAction{ActionKind::rock_paper_scissors, protocol::RpsChoice::scissors});
}

}
