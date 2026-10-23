#include "client/planning.h"
#include "client/bytes.h"
#include <functional>
#include <type_traits>

namespace ygo_gym::client {
namespace {
using Match = std::function<bool(const action::Action&)>;
using Kind = action::ActionKind;
Match kind(Kind expected) {
    return [expected](const auto& value) { return action::kind(value) == expected; };
}
Match source(Kind expected, std::uint32_t index) {
    return [expected, index](const auto& value) {
        if(action::kind(value) != expected) return false;
        return std::visit([index](const auto& item) {
            using T = std::decay_t<decltype(item)>;
            if constexpr(std::is_same_v<T, action::CardAction> || std::is_same_v<T, action::EffectAction> ||
                         std::is_same_v<T, action::AttackAction> || std::is_same_v<T, action::TributeAction> ||
                         std::is_same_v<T, action::SumAction> || std::is_same_v<T, action::CounterAction>)
                return item.source_index == index;
            return false;
        }, value);
    };
}
template<typename T, typename V> Match member(V T::*field, V expected) {
    return [field, expected](const auto& value) {
        const auto* item = std::get_if<T>(&value);
        return item && item->*field == expected;
    };
}
std::vector<std::uint32_t> indices(const Packet& response, std::size_t required = 0) {
    const auto encoding = read<std::uint32_t>(response, 0);
    auto count = read<std::uint32_t>(response, 4);
    if(count < required) throw std::invalid_argument("WindBot omitted mandatory materials");
    std::vector<std::uint32_t> result;
    if(encoding == 0) {
        for(std::uint32_t i = 0; i < count; ++i) result.push_back(read<std::uint32_t>(response, 8 + 4 * i));
    } else if(encoding == 2) {
        for(std::uint32_t i = static_cast<std::uint32_t>(required); i < count; ++i) result.push_back(response.at(8 + i));
    } else throw std::invalid_argument("unsupported WindBot selection encoding");
    return result;
}
std::vector<Match> translate(const protocol::Decision& prompt, const Packet& response) {
    return std::visit([&](const auto& decision) -> std::vector<Match> {
        using T = std::decay_t<decltype(decision)>;
        std::vector<Match> result;
        const auto scalar = [&] { return read<std::int32_t>(response, 0); };
        if constexpr(std::is_same_v<T, protocol::IdleDecision> || std::is_same_v<T, protocol::BattleDecision>) {
            const auto value = static_cast<std::uint32_t>(scalar());
            const auto command = value & 0xffff;
            if constexpr(std::is_same_v<T, protocol::IdleDecision>) {
                const std::array kinds{Kind::summon, Kind::special_summon, Kind::reposition, Kind::set_monster,
                    Kind::set_spell_trap, Kind::activate, Kind::battle_phase, Kind::end_phase, Kind::shuffle_hand};
                if(command >= kinds.size()) throw std::invalid_argument("invalid WindBot idle command");
                result.push_back(command < 6 ? source(kinds[command], value >> 16) : kind(kinds[command]));
            } else {
                const std::array kinds{Kind::activate, Kind::attack, Kind::main_phase_2, Kind::end_phase};
                if(command >= kinds.size()) throw std::invalid_argument("invalid WindBot battle command");
                result.push_back(command < 2 ? source(kinds[command], value >> 16) : kind(kinds[command]));
            }
        } else if constexpr(std::is_same_v<T, protocol::CardDecision> || std::is_same_v<T, protocol::TributeDecision> || std::is_same_v<T, protocol::SumDecision>) {
            if(scalar() == -1) return {kind(Kind::cancel)};
            auto selected = [&] {
                if constexpr(std::is_same_v<T, protocol::SumDecision>) return indices(response, decision.required.size());
                return indices(response);
            }();
            Kind target = std::is_same_v<T, protocol::CardDecision> ? Kind::select_card :
                std::is_same_v<T, protocol::TributeDecision> ? Kind::select_tribute : Kind::select_sum_card;
            for(auto index : selected) result.push_back(source(target, index));
            result.push_back(kind(Kind::confirm));
        } else if constexpr(std::is_same_v<T, protocol::UnselectCardDecision>) {
            if(scalar() == -1) return {kind(decision.finishable ? Kind::confirm : Kind::cancel)};
            const auto index = read<std::uint32_t>(response, 4);
            result.push_back(source(index < decision.selectable.size() ? Kind::select_card : Kind::unselect_card, index));
        } else if constexpr(std::is_same_v<T, protocol::ChainDecision>) {
            result.push_back(scalar() == -1 ? kind(Kind::pass) : source(Kind::activate, static_cast<std::uint32_t>(scalar())));
        } else if constexpr(std::is_same_v<T, protocol::YesNoDecision> || std::is_same_v<T, protocol::EffectYesNoDecision>) {
            result.push_back(kind(scalar() ? Kind::yes : Kind::no));
        } else if constexpr(std::is_same_v<T, protocol::OptionDecision>) {
            result.push_back(member(&action::OptionAction::index, static_cast<std::uint32_t>(scalar())));
        } else if constexpr(std::is_same_v<T, protocol::PlaceDecision>) {
            for(std::size_t offset = 0; offset < response.size(); offset += 3) {
                const protocol::ZoneRef zone{response.at(offset), response.at(offset + 1), response.at(offset + 2)};
                result.push_back([zone](const auto& value) {
                    auto item = std::get_if<action::ZoneAction>(&value);
                    return item && item->zone.player == zone.player && item->zone.location == zone.location && item->zone.sequence == zone.sequence;
                });
            }
        } else if constexpr(std::is_same_v<T, protocol::PositionDecision>) {
            result.push_back(member(&action::PositionAction::position, static_cast<std::uint8_t>(scalar())));
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            for(std::size_t index = 0; index < decision.cards.size(); ++index) {
                auto count = read<std::uint16_t>(response, 2 * index);
                result.push_back([index, count](const auto& value) {
                    auto item = std::get_if<action::CounterAction>(&value);
                    return item && item->source_index == index && item->count == count;
                });
            }
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            if(response.at(0) == 255) return {kind(Kind::cancel)};
            for(auto index : response) result.push_back(source(Kind::order_card, index));
        } else if constexpr(std::is_same_v<T, protocol::AnnounceRaceDecision>) {
            auto bits = read<std::uint64_t>(response, 0);
            for(std::uint64_t bit = 1; bit; bit <<= 1) if(bits & bit) result.push_back(member(&action::RaceAction::race, bit));
        } else if constexpr(std::is_same_v<T, protocol::AnnounceAttributeDecision>) {
            auto bits = static_cast<std::uint32_t>(scalar());
            for(std::uint32_t bit = 1; bit; bit <<= 1) if(bits & bit) result.push_back(member(&action::AttributeAction::attribute, bit));
        } else if constexpr(std::is_same_v<T, protocol::AnnounceCardDecision>) {
            result.push_back(member(&action::CardCodeAction::code, static_cast<std::uint32_t>(scalar())));
        } else if constexpr(std::is_same_v<T, protocol::AnnounceNumberDecision>) {
            result.push_back(member(&action::NumberAction::index, static_cast<std::uint32_t>(scalar())));
        } else if constexpr(std::is_same_v<T, protocol::RockPaperScissorsDecision>) {
            result.push_back(member(&action::RpsAction::choice, static_cast<protocol::RpsChoice>(scalar())));
        }
        return result;
    }, prompt);
}
}

std::vector<std::uint32_t> plan(const state::Observation& observation,
                               std::shared_ptr<const EngineState> engine, const Packet& response) {
    const auto& prompt = observation.storage()->client_decision;
    if(!prompt) throw std::invalid_argument("observation has no client decision");
    if(!observation.pending_actions().empty()) throw std::invalid_argument("WindBot planning requires the beginning of a compound selection");
    action::State state(*prompt, std::move(engine), observation.storage());
    std::vector<std::uint32_t> result;
    for(const auto& matches : translate(*prompt, response)) {
        const auto& actions = state.actions();
        auto found = std::find_if(actions.begin(), actions.end(), matches);
        if(found == actions.end()) throw std::invalid_argument("WindBot response does not match a legal semantic action");
        auto index = static_cast<std::uint32_t>(found - actions.begin());
        result.push_back(index);
        if(auto encoded = state.step(index)) {
            const bool sort_cancel = std::holds_alternative<protocol::SortDecision>(*prompt) &&
                !response.empty() && std::all_of(response.begin(), response.end(), [](auto byte) { return byte == 255; });
            if(!std::holds_alternative<protocol::SumDecision>(*prompt) && !sort_cancel && encoded->data != response)
                throw std::invalid_argument("WindBot response contains an invalid count or trailing selection");
            return result;
        }
    }
    throw std::invalid_argument("WindBot response did not complete the current decision");
}
}

std::vector<std::uint32_t> ygo_gym::Engine::plan_client_response(const state::Observation& observation, const std::vector<std::uint8_t>& response) const {
    return client::plan(observation, state_, response);
}
