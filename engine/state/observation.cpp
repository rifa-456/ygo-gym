#include "observation.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <unordered_map>
#include <utility>

#include "../../third_party/ygopro-core/card.h"
#include "../../third_party/ygopro-core/duel.h"
#include "../../third_party/ygopro-core/effect.h"
#include "../../third_party/ygopro-core/effect_constants.h"
#include "../../third_party/ygopro-core/field.h"
#include "ocgapi_constants.h"

namespace ygo_gym::state {
namespace {

CardLocator locator(const protocol::CardRef& ref) {
    return CardLocator{
        ref.controller,
        ref.location,
        ref.sequence,
        (ref.location & LOCATION_OVERLAY) != 0 && ref.position ? *ref.position : invalid_index,
    };
}

card* resolve_card(::duel* core, const protocol::CardRef& ref) {
    const auto location = ref.location & ~LOCATION_OVERLAY;
    auto* result = core->game_field->get_field_card(ref.controller, location, ref.sequence);
    if((ref.location & LOCATION_OVERLAY) == 0)
        return result;
    if(result == nullptr)
        return nullptr;
    if(ref.position && *ref.position < result->xyz_materials.size())
        return result->xyz_materials[*ref.position];
    for(auto* material : result->xyz_materials) {
        if(material->data.code == ref.code)
            return material;
    }
    return nullptr;
}

bool identity_visible(card& value, std::uint8_t viewer) {
    const bool public_query = (value.current.position & POS_FACEUP) != 0
        || value.is_affected_by_effect(EFFECT_PUBLIC) != nullptr;
    if(public_query)
        return true;
    if(value.current.controler != viewer)
        return false;
    return value.is_affected_by_effect(EFFECT_DARKNESS_HIDE) == nullptr;
}

template<typename F>
void for_each_decision_card(const protocol::Decision& decision, F&& visit) {
    std::visit([&](const auto& value) {
        using T = std::decay_t<decltype(value)>;
        if constexpr(std::is_same_v<T, protocol::BattleDecision>) {
            for(const auto& item : value.activatable) visit(item.card);
            for(const auto& item : value.attackable) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::IdleDecision>) {
            for(const auto& item : value.summonable) visit(item);
            for(const auto& item : value.special_summonable) visit(item);
            for(const auto& item : value.repositionable) visit(item);
            for(const auto& item : value.monster_settable) visit(item);
            for(const auto& item : value.spell_trap_settable) visit(item);
            for(const auto& item : value.activatable) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::EffectYesNoDecision>) {
            visit(value.card);
        } else if constexpr(std::is_same_v<T, protocol::CardDecision>) {
            for(const auto& item : value.cards) visit(item);
        } else if constexpr(std::is_same_v<T, protocol::ChainDecision>) {
            for(const auto& item : value.options) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::TributeDecision>) {
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::CounterDecision>) {
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::SumDecision>) {
            for(const auto& item : value.required) visit(item.card);
            for(const auto& item : value.cards) visit(item.card);
        } else if constexpr(std::is_same_v<T, protocol::SortDecision>) {
            for(const auto& item : value.cards) visit(item);
        } else if constexpr(std::is_same_v<T, protocol::UnselectCardDecision>) {
            for(const auto& item : value.selectable) visit(item);
            for(const auto& item : value.unselectable) visit(item);
        }
    }, decision);
}

class Builder {
public:
    Builder(::duel* core, std::uint8_t viewer, const protocol::Decision* decision)
        : core_(core), viewer_(viewer), decision_(decision), storage_(std::make_shared<ObservationStorage>()) {
        storage_->viewer = viewer;
        storage_->global.turn_player = core_->game_field->infos.turn_player;
        storage_->global.turn_count = core_->game_field->infos.turn_id;
        storage_->global.phase = core_->game_field->infos.phase;
        storage_->global.life_points[0] = core_->game_field->player[0].lp;
        storage_->global.life_points[1] = core_->game_field->player[1].lp;
        if(decision_ != nullptr)
            storage_->global.decision_player = protocol::player(*decision_);
    }

    Observation build(const event::Transition& events) {
        add_zone_counts();
        add_visible_cards();
        if(decision_ != nullptr && protocol::player(*decision_) == viewer_)
            add_decision_cards();
        add_chain();
        add_relations_and_counters();
        storage_->events = event::project(events, viewer_, *storage_);
        return Observation{std::move(storage_)};
    }

private:
    void add_zone_counts() {
        constexpr std::uint32_t locations[] = {
            LOCATION_DECK, LOCATION_HAND, LOCATION_MZONE, LOCATION_SZONE,
            LOCATION_GRAVE, LOCATION_REMOVED, LOCATION_EXTRA,
        };
        for(std::uint8_t player = 0; player < 2; ++player) {
            for(const auto location : locations) {
                storage_->zone_counts.push_back(ZoneCount{
                    player,
                    location,
                    OCG_DuelQueryCount(core_, player, location),
                });
            }
        }
    }

    void add_visible_cards() {
        for(std::uint8_t player = 0; player < 2; ++player) {
            const auto& info = core_->game_field->player[player];
            for(auto* value : info.list_hand)
                add_card(value, identity_visible(*value, viewer_));
            for(auto* value : info.list_mzone) {
                if(value != nullptr) {
                    const auto host = add_card(value, identity_visible(*value, viewer_));
                    add_materials(*value, host);
                }
            }
            for(auto* value : info.list_szone) {
                if(value != nullptr)
                    add_card(value, identity_visible(*value, viewer_));
            }
            for(auto* value : info.list_grave)
                add_card(value, identity_visible(*value, viewer_));
            for(auto* value : info.list_remove)
                add_card(value, identity_visible(*value, viewer_));
            for(auto* value : info.list_extra) {
                const bool visible = identity_visible(*value, viewer_);
                if(value->owner == viewer_ || visible)
                    add_card(value, visible);
            }
        }
    }

    void add_decision_cards() {
        for_each_decision_card(*decision_, [&](const protocol::CardRef& ref) {
            auto* value = resolve_card(core_, ref);
            if(value == nullptr)
                throw std::runtime_error("ocgcore decision references a card that cannot be resolved");
            const auto id = add_card(value, decision_reveals_identity(ref));
            storage_->card_index.insert_or_assign(locator(ref), id);
        });
    }

    bool decision_reveals_identity(const protocol::CardRef& ref) const {
        // EDOPro masks these selection packet codes when the card is controlled by the other player.
        return std::visit([&](const auto& value) {
            using T = std::decay_t<decltype(value)>;
            if constexpr(std::is_same_v<T, protocol::CardDecision>
                || std::is_same_v<T, protocol::TributeDecision>
                || std::is_same_v<T, protocol::UnselectCardDecision>) {
                return ref.controller == value.player;
            }
            return true;
        }, *decision_);
    }

    std::uint32_t add_card(card* value, bool reveal) {
        if(const auto found = by_pointer_.find(value); found != by_pointer_.end()) {
            if(reveal && storage_->cards[found->second].code == unknown_card)
                reveal_card(found->second, *value);
            return found->second;
        }

        const auto id = static_cast<std::uint32_t>(storage_->cards.size());
        by_pointer_.emplace(value, id);
        storage_->cards.push_back(CardRecord{
            reveal ? value->data.code : unknown_card,
            value->owner,
            value->current.controler,
            value->current.location,
            value->current.sequence,
            value->current.position,
        });
        storage_->core_cards.push_back(value);
        storage_->card_index.emplace(CardLocator{
            value->current.controler,
            value->current.location,
            value->current.sequence,
            invalid_index,
        }, id);
        if(reveal)
            add_components(id, *value);
        return id;
    }

    void reveal_card(std::uint32_t id, card& value) {
        storage_->cards[id].code = value.data.code;
        add_components(id, value);
    }

    void add_components(std::uint32_t id, card& value) {
        auto& row = storage_->cards[id];
        if(row.properties_index != invalid_index)
            return;

        const auto type = value.get_type();
        row.properties_index = static_cast<std::uint32_t>(storage_->properties.size());
        storage_->properties.push_back(CardProperties{
            value.get_code(), type, value.get_attribute(), value.get_race(),
        });
        if((type & TYPE_MONSTER) != 0) {
            row.monster_index = static_cast<std::uint32_t>(storage_->monsters.size());
            storage_->monsters.push_back(MonsterState{
                value.get_level(), value.get_rank(), value.get_attack(), value.get_defense(),
                value.get_base_attack(), value.get_base_defense(),
            });
        }
        if((type & TYPE_PENDULUM) != 0) {
            row.pendulum_index = static_cast<std::uint32_t>(storage_->pendulums.size());
            storage_->pendulums.push_back(PendulumState{value.get_lscale(), value.get_rscale()});
        }
        if((type & TYPE_LINK) != 0) {
            row.link_index = static_cast<std::uint32_t>(storage_->links.size());
            storage_->links.push_back(LinkState{value.get_link(), value.get_link_marker()});
        }
    }

    void add_materials(card& host, std::uint32_t host_id) {
        for(std::uint32_t sequence = 0; sequence < host.xyz_materials.size(); ++sequence) {
            auto* material = host.xyz_materials[sequence];
            const auto id = add_card(material, true);
            auto& row = storage_->cards[id];
            row.location = LOCATION_OVERLAY;
            row.sequence = sequence;
            row.position = 0;
            storage_->card_index.emplace(CardLocator{
                host.current.controler,
                static_cast<std::uint32_t>(host.current.location | LOCATION_OVERLAY),
                host.current.sequence,
                sequence,
            }, id);
            storage_->relations.push_back(RelationState{RelationKind::material, host_id, id, sequence});
        }
    }

    void add_chain() {
        const auto& current = core_->game_field->core.current_chain;
        for(std::uint32_t index = 0; index < current.size(); ++index) {
            const auto& link = current[index];
            auto* handler = link.triggering_effect->get_handler();
            const auto card_id = add_card(handler, true);
            const auto target_begin = static_cast<std::uint32_t>(storage_->chain_targets.size());
            if(link.target_cards) {
                for(auto* target : link.target_cards->container)
                    storage_->chain_targets.push_back(add_card(target, identity_visible(*target, viewer_)));
            }
            storage_->chain.push_back(ChainState{
                index,
                card_id,
                link.triggering_player,
                link.triggering_controler,
                link.triggering_location,
                link.triggering_sequence,
                link.triggering_effect->description,
                target_begin,
                static_cast<std::uint32_t>(storage_->chain_targets.size()) - target_begin,
            });
        }
    }

    void add_relations_and_counters() {
        for(const auto& [value, source] : by_pointer_) {
            for(const auto& counter : value->counters) {
                const auto count = static_cast<std::uint16_t>(counter.second[0] + counter.second[1]);
                storage_->counters.push_back(CounterState{source, counter.first, count});
            }
            if(value->equiping_target != nullptr)
                add_relation(RelationKind::equip, source, value->equiping_target, 0);
            std::uint32_t sequence = 0;
            for(auto* target : value->effect_target_cards)
                add_relation(RelationKind::target, source, target, sequence++);
            if(value->current.reason_card != nullptr)
                add_relation(RelationKind::reason, source, value->current.reason_card, 0);
        }
    }

    void add_relation(RelationKind kind, std::uint32_t source, card* target, std::uint32_t sequence) {
        const auto found = by_pointer_.find(target);
        if(found != by_pointer_.end())
            storage_->relations.push_back(RelationState{kind, source, found->second, sequence});
    }

    ::duel* core_;
    std::uint8_t viewer_;
    const protocol::Decision* decision_;
    std::shared_ptr<ObservationStorage> storage_;
    std::unordered_map<const card*, std::uint32_t> by_pointer_;
};

}

std::size_t CardLocatorHash::operator()(const CardLocator& value) const noexcept {
    std::size_t hash = value.controller;
    hash = hash * 1315423911u + value.location;
    hash = hash * 1315423911u + value.sequence;
    hash = hash * 1315423911u + value.overlay_sequence;
    return hash;
}

std::uint32_t ObservationStorage::card_id(const protocol::CardRef& card) const {
    const auto found = card_index.find(locator(card));
    if(found == card_index.end())
        throw std::runtime_error("semantic action references a card absent from the observation");
    return found->second;
}

CardView::CardView(std::shared_ptr<const ObservationStorage> storage, std::uint32_t id)
    : storage_(std::move(storage)), id_(id) {}

const CardRecord& CardView::record() const noexcept { return storage_->cards[id_]; }
std::uint32_t CardView::id() const noexcept { return id_; }
std::uint32_t CardView::code() const noexcept { return record().code; }
std::uint8_t CardView::owner() const noexcept { return record().owner; }
std::uint8_t CardView::controller() const noexcept { return record().controller; }
std::uint32_t CardView::location() const noexcept { return record().location; }
std::uint32_t CardView::sequence() const noexcept { return record().sequence; }
std::uint32_t CardView::position() const noexcept { return record().position; }

const CardProperties* CardView::properties() const noexcept {
    return record().properties_index == invalid_index ? nullptr : &storage_->properties[record().properties_index];
}
const MonsterState* CardView::monster() const noexcept {
    return record().monster_index == invalid_index ? nullptr : &storage_->monsters[record().monster_index];
}
const PendulumState* CardView::pendulum() const noexcept {
    return record().pendulum_index == invalid_index ? nullptr : &storage_->pendulums[record().pendulum_index];
}
const LinkState* CardView::link() const noexcept {
    return record().link_index == invalid_index ? nullptr : &storage_->links[record().link_index];
}

CardCollection::CardCollection(std::shared_ptr<const ObservationStorage> storage) : storage_(std::move(storage)) {}
std::size_t CardCollection::size() const noexcept { return storage_->cards.size(); }
CardView CardCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("card index is out of range");
    return CardView{storage_, static_cast<std::uint32_t>(index)};
}

Observation::Observation(std::shared_ptr<ObservationStorage> storage) : storage_(std::move(storage)) {}
std::uint8_t Observation::viewer() const noexcept { return storage_->viewer; }
const GlobalState& Observation::global() const noexcept { return storage_->global; }
CardCollection Observation::cards() const { return CardCollection{storage_}; }
const std::vector<ZoneCount>& Observation::zone_counts() const noexcept { return storage_->zone_counts; }
const std::vector<CounterState>& Observation::counters() const noexcept { return storage_->counters; }
const std::vector<RelationState>& Observation::relations() const noexcept { return storage_->relations; }
const std::vector<ChainState>& Observation::chain() const noexcept { return storage_->chain; }
const std::vector<std::uint32_t>& Observation::chain_targets() const noexcept { return storage_->chain_targets; }
const std::vector<action::Action>& Observation::pending_actions() const noexcept { return storage_->pending_actions; }
const event::Batch& Observation::events() const noexcept { return storage_->events; }
std::shared_ptr<ObservationStorage> Observation::storage() const noexcept { return storage_; }

Observation build_observation(OCG_Duel duel, std::uint8_t viewer, const protocol::Decision* decision, const event::Transition& events) {
    if(viewer > 1)
        throw std::invalid_argument("viewer must be player 0 or 1");
    return Builder{static_cast<::duel*>(duel), viewer, decision}.build(events);
}

}
