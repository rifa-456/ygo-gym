#pragma once

#include "state/observation.h"
#include "ygopro-core/duel.h"

namespace ygo_gym::state {

class ObservationBuilder {
public:
    explicit ObservationBuilder(::duel* core, std::uint8_t viewer, const protocol::Decision* decision);
    Observation build(const event::Transition& events);

private:
    void add_zone_counts();
    void add_visible_cards();
    void add_decision_cards();
    bool decision_reveals_identity(const protocol::CardRef& ref) const;
    std::uint32_t add_card(card* value, bool reveal);
    void reveal_card(std::uint32_t id, card& value);
    void add_components(std::uint32_t id, card& value);
    void add_materials(card& host, std::uint32_t host_id);
    void add_chain();
    void add_relations_and_counters();
    void add_relation(RelationKind kind, std::uint32_t source, card* target, std::uint32_t sequence);

    ::duel* core_;
    std::uint8_t viewer_;
    const protocol::Decision* decision_;
    std::shared_ptr<ObservationStorage> storage_;
    std::unordered_map<const card*, std::uint32_t> by_pointer_;
};

}
