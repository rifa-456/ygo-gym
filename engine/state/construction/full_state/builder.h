#pragma once

#include "state/state.h"
#include "ygopro-core/duel.h"

namespace ygo_gym::state {

class StateBuilder {
public:
    explicit StateBuilder(::duel* core);
    State build(
        const protocol::Decision* decision,
        const std::vector<action::Action>& pending_actions,
        const ObservationStorage* observation
    );

private:
    std::uint32_t add_card(card* value);
    void add_components(std::uint32_t id, card& value);
    void add_zone(std::uint8_t player, std::uint32_t location, const card_vector& cards);
    void add_materials(card& host);
    void add_zones();
    void add_unzoned_cards();
    void add_relations_and_counters();
    void add_relation(RelationKind kind, std::uint32_t source, card* target, std::uint32_t sequence);
    void add_chain();
    action::Action remap_action(const action::Action& input) const;

    ::duel* core_;
    std::shared_ptr<StateStorage> storage_;
};

}
