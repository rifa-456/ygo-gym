#pragma once

#include "reader.h"

namespace ygo_gym::protocol {

BattleDecision read_battle(Reader& reader);
IdleDecision read_idle(Reader& reader);
ChainDecision read_chain(Reader& reader);
CardDecision read_card_selection(Reader& reader);
PlaceDecision read_place(Reader& reader, bool disable_field);
TributeDecision read_tribute(Reader& reader);
CounterDecision read_counter(Reader& reader);
SumDecision read_sum(Reader& reader);
SortDecision read_sort(Reader& reader, bool chain);
UnselectCardDecision read_unselect(Reader& reader);

}
