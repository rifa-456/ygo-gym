#include "state/construction/card_lookup.h"
#include "ygopro-core/card.h"
#include "ygopro-core/duel.h"
#include "ygopro-core/field.h"
#include "ygopro-core/effect_constants.h"

namespace ygo_gym::state {

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

}
