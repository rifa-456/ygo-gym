#include "state.h"

#include <algorithm>
#include <stdexcept>
#include <type_traits>
#include <utility>

#include "../../third_party/ygopro-core/card.h"
#include "../../third_party/ygopro-core/duel.h"
#include "../../third_party/ygopro-core/effect.h"
#include "../../third_party/ygopro-core/field.h"
#include "ocgapi_constants.h"

namespace ygo_gym::state {
namespace {

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

class Builder {
public:
    explicit Builder(::duel* core) : core_(core), storage_(std::make_shared<StateStorage>()) {
        auto& field = *core_->game_field;
        storage_->global.turn_player = field.infos.turn_player;
        storage_->global.turn_count = field.infos.turn_id;
        storage_->global.phase = field.infos.phase;
        storage_->global.life_points[0] = field.player[0].lp;
        storage_->global.life_points[1] = field.player[1].lp;
        storage_->duel_options = field.core.duel_options;
        for(std::uint8_t player = 0; player < 2; ++player) {
            const auto& info = field.player[player];
            storage_->players[player] = PlayerState{
                info.lp,
                info.start_lp,
                info.start_count,
                info.draw_count,
                info.used_location,
                info.disabled_location,
                info.extra_p_count,
            };
        }
    }

    State build(
        const protocol::Decision* decision,
        const std::vector<action::Action>& pending_actions,
        const ObservationStorage* observation
    ) {
        if(decision != nullptr)
            storage_->global.decision_player = protocol::player(*decision);
        if(observation != nullptr) {
            for(auto* value : observation->core_cards)
                add_card(value);
        }
        add_zones();
        add_unzoned_cards();
        add_relations_and_counters();
        add_chain();
        for(const auto& pending : pending_actions)
            storage_->pending_actions.push_back(remap_action(pending));
        return State{std::move(storage_)};
    }

private:
    std::uint32_t add_card(card* value) {
        if(const auto found = storage_->pointer_index.find(value); found != storage_->pointer_index.end())
            return found->second;

        const auto id = static_cast<std::uint32_t>(storage_->cards.size());
        storage_->pointer_index.emplace(value, id);
        storage_->cards.push_back(CardRecord{
            value->data.code,
            value->owner,
            value->current.controler,
            value->current.location,
            value->current.sequence,
            value->current.position,
        });
        add_components(id, *value);
        return id;
    }

    void add_components(std::uint32_t id, card& value) {
        auto& row = storage_->cards[id];
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

    void add_zone(std::uint8_t player, std::uint32_t location, const card_vector& cards) {
        const auto begin = static_cast<std::uint32_t>(storage_->zone_cards.size());
        for(auto* value : cards) {
            if(value != nullptr)
                storage_->zone_cards.push_back(add_card(value));
        }
        storage_->zones.push_back(ZoneState{
            player,
            location,
            begin,
            static_cast<std::uint32_t>(storage_->zone_cards.size()) - begin,
        });
    }

    void add_materials(card& host) {
        const auto host_id = storage_->pointer_index.at(&host);
        for(std::uint32_t sequence = 0; sequence < host.xyz_materials.size(); ++sequence) {
            auto* material = host.xyz_materials[sequence];
            const auto id = add_card(material);
            auto& row = storage_->cards[id];
            row.location = LOCATION_OVERLAY;
            row.sequence = sequence;
            row.position = 0;
            storage_->relations.push_back(RelationState{RelationKind::material, host_id, id, sequence});
        }
    }

    void add_zones() {
        for(std::uint8_t player = 0; player < 2; ++player) {
            auto& info = core_->game_field->player[player];
            add_zone(player, LOCATION_DECK, info.list_main);
            add_zone(player, LOCATION_HAND, info.list_hand);
            add_zone(player, LOCATION_MZONE, info.list_mzone);
            add_zone(player, LOCATION_SZONE, info.list_szone);
            add_zone(player, LOCATION_GRAVE, info.list_grave);
            add_zone(player, LOCATION_REMOVED, info.list_remove);
            add_zone(player, LOCATION_EXTRA, info.list_extra);
            for(auto* host : info.list_mzone) {
                if(host != nullptr)
                    add_materials(*host);
            }
        }
    }

    void add_unzoned_cards() {
        std::vector<card*> remaining;
        for(auto* value : core_->cards) {
            if(value->data.code != 0 && storage_->pointer_index.find(value) == storage_->pointer_index.end())
                remaining.push_back(value);
        }
        std::sort(remaining.begin(), remaining.end(), [](const card* lhs, const card* rhs) {
            return lhs->cardid < rhs->cardid;
        });
        for(auto* value : remaining)
            add_card(value);
    }

    void add_relations_and_counters() {
        for(auto* value : core_->cards) {
            const auto source_found = storage_->pointer_index.find(value);
            if(source_found == storage_->pointer_index.end())
                continue;
            const auto source = source_found->second;
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
        const auto found = storage_->pointer_index.find(target);
        if(found != storage_->pointer_index.end())
            storage_->relations.push_back(RelationState{kind, source, found->second, sequence});
    }

    void add_chain() {
        const auto& current = core_->game_field->core.current_chain;
        for(std::uint32_t index = 0; index < current.size(); ++index) {
            const auto& link = current[index];
            const auto card_id = storage_->pointer_index.at(link.triggering_effect->get_handler());
            const auto target_begin = static_cast<std::uint32_t>(storage_->chain_targets.size());
            if(link.target_cards) {
                for(auto* target : link.target_cards->container)
                    storage_->chain_targets.push_back(storage_->pointer_index.at(target));
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

    action::Action remap_action(const action::Action& input) const {
        return std::visit([&](const auto& value) -> action::Action {
            using T = std::decay_t<decltype(value)>;
            if constexpr(std::is_same_v<T, action::CardAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_card, core_);
                return copy;
            } else if constexpr(std::is_same_v<T, action::EffectAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_effect.card, core_);
                return copy;
            } else if constexpr(std::is_same_v<T, action::AttackAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_attack.card, core_);
                return copy;
            } else if constexpr(std::is_same_v<T, action::TributeAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_tribute.card, core_);
                return copy;
            } else if constexpr(std::is_same_v<T, action::SumAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_sum.card, core_);
                return copy;
            } else if constexpr(std::is_same_v<T, action::CounterAction>) {
                auto copy = value;
                copy.card = storage_->card_id(copy.core_counter.card, core_);
                return copy;
            } else {
                return value;
            }
        }, input);
    }

    ::duel* core_;
    std::shared_ptr<StateStorage> storage_;
};

}

std::uint32_t StateStorage::card_id(const protocol::CardRef& ref, OCG_Duel duel) const {
    auto* value = resolve_card(static_cast<::duel*>(duel), ref);
    if(value == nullptr)
        throw std::runtime_error("ocgcore card reference cannot be resolved in full state");
    const auto found = pointer_index.find(value);
    if(found == pointer_index.end())
        throw std::runtime_error("resolved ocgcore card is absent from full state");
    return found->second;
}

StateCardView::StateCardView(std::shared_ptr<const StateStorage> storage, std::uint32_t id)
    : storage_(std::move(storage)), id_(id) {}
std::uint32_t StateCardView::id() const noexcept { return id_; }
const CardRecord& StateCardView::card() const noexcept { return storage_->cards[id_]; }
const CardProperties& StateCardView::properties() const noexcept {
    return storage_->properties[card().properties_index];
}
const MonsterState* StateCardView::monster() const noexcept {
    return card().monster_index == invalid_index ? nullptr : &storage_->monsters[card().monster_index];
}
const PendulumState* StateCardView::pendulum() const noexcept {
    return card().pendulum_index == invalid_index ? nullptr : &storage_->pendulums[card().pendulum_index];
}
const LinkState* StateCardView::link() const noexcept {
    return card().link_index == invalid_index ? nullptr : &storage_->links[card().link_index];
}

StateCardCollection::StateCardCollection(std::shared_ptr<const StateStorage> storage) : storage_(std::move(storage)) {}
std::size_t StateCardCollection::size() const noexcept { return storage_->cards.size(); }
StateCardView StateCardCollection::at(std::size_t index) const {
    if(index >= size())
        throw std::out_of_range("state card index is out of range");
    return StateCardView{storage_, static_cast<std::uint32_t>(index)};
}

State::State(std::shared_ptr<StateStorage> storage) : storage_(std::move(storage)) {}
const GlobalState& State::global() const noexcept { return storage_->global; }
std::uint64_t State::duel_options() const noexcept { return storage_->duel_options; }
const PlayerState& State::player(std::size_t index) const {
    if(index > 1)
        throw std::out_of_range("player index is out of range");
    return storage_->players[index];
}
StateCardCollection State::cards() const { return StateCardCollection{storage_}; }
const std::vector<ZoneState>& State::zones() const noexcept { return storage_->zones; }
const std::vector<std::uint32_t>& State::zone_cards() const noexcept { return storage_->zone_cards; }
const std::vector<CounterState>& State::counters() const noexcept { return storage_->counters; }
const std::vector<RelationState>& State::relations() const noexcept { return storage_->relations; }
const std::vector<ChainState>& State::chain() const noexcept { return storage_->chain; }
const std::vector<std::uint32_t>& State::chain_targets() const noexcept { return storage_->chain_targets; }
const std::vector<action::Action>& State::pending_actions() const noexcept { return storage_->pending_actions; }
const event::Batch& State::events() const noexcept { return storage_->events; }
std::shared_ptr<StateStorage> State::storage() const noexcept { return storage_; }

State build_state(
    OCG_Duel duel,
    const protocol::Decision* decision,
    const std::vector<action::Action>& pending_actions,
    const ObservationStorage* observation,
    const event::Transition& events
) {
    auto state = Builder{static_cast<::duel*>(duel)}.build(decision, pending_actions, observation);
    state.storage()->events = event::full(events, *state.storage());
    return state;
}

}
