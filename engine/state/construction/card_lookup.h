#pragma once

#include "state/observation.h"

class duel;

namespace ygo_gym::state {
CardLocator locator(const protocol::CardRef& ref);
card* resolve_card(::duel* core, const protocol::CardRef& ref);
bool identity_visible(card& value, std::uint8_t viewer);
}
