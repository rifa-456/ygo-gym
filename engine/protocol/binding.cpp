#include "binding.h"

#include <pybind11/stl.h>

#include "decision.h"

namespace py = pybind11;

namespace ygo_gym::protocol {
namespace {

template<typename T>
void set_public_module(py::class_<T>& type) {
    type.attr("__module__") = "ygo_gym.protocol";
}

}

void bind_protocol(py::module_& module) {
    py::enum_<DecisionKind>(module, "DecisionKind")
        .value("BATTLE_COMMAND", DecisionKind::battle_command)
        .value("IDLE_COMMAND", DecisionKind::idle_command)
        .value("EFFECT_YES_NO", DecisionKind::effect_yes_no)
        .value("YES_NO", DecisionKind::yes_no)
        .value("OPTION", DecisionKind::option)
        .value("CARD", DecisionKind::card)
        .value("CHAIN", DecisionKind::chain)
        .value("PLACE", DecisionKind::place)
        .value("POSITION", DecisionKind::position)
        .value("TRIBUTE", DecisionKind::tribute)
        .value("SORT_CHAIN", DecisionKind::sort_chain)
        .value("COUNTER", DecisionKind::counter)
        .value("SUM", DecisionKind::sum)
        .value("DISABLE_FIELD", DecisionKind::disable_field)
        .value("SORT_CARD", DecisionKind::sort_card)
        .value("UNSELECT_CARD", DecisionKind::unselect_card)
        .value("ROCK_PAPER_SCISSORS", DecisionKind::rock_paper_scissors)
        .value("ANNOUNCE_RACE", DecisionKind::announce_race)
        .value("ANNOUNCE_ATTRIBUTE", DecisionKind::announce_attribute)
        .value("ANNOUNCE_CARD", DecisionKind::announce_card)
        .value("ANNOUNCE_NUMBER", DecisionKind::announce_number);

    py::enum_<IdleCommand>(module, "IdleCommand")
        .value("SUMMON", IdleCommand::summon)
        .value("SPECIAL_SUMMON", IdleCommand::special_summon)
        .value("REPOSITION", IdleCommand::reposition)
        .value("SET_MONSTER", IdleCommand::set_monster)
        .value("SET_SPELL_TRAP", IdleCommand::set_spell_trap)
        .value("ACTIVATE", IdleCommand::activate)
        .value("BATTLE_PHASE", IdleCommand::battle_phase)
        .value("END_PHASE", IdleCommand::end_phase)
        .value("SHUFFLE_HAND", IdleCommand::shuffle_hand);

    py::enum_<BattleCommand>(module, "BattleCommand")
        .value("ACTIVATE", BattleCommand::activate)
        .value("ATTACK", BattleCommand::attack)
        .value("MAIN_PHASE_2", BattleCommand::main_phase_2)
        .value("END_PHASE", BattleCommand::end_phase);

    py::enum_<RpsChoice>(module, "RpsChoice")
        .value("ROCK", RpsChoice::rock)
        .value("PAPER", RpsChoice::paper)
        .value("SCISSORS", RpsChoice::scissors);

    auto response = py::class_<Response>(module, "CoreResponse");
    response
        .def_property_readonly("kind", [](const Response& value) { return value.kind; })
        .def_property_readonly("bytes", [](const Response& value) {
            return py::bytes(reinterpret_cast<const char*>(value.data.data()), value.data.size());
        });
    set_public_module(response);

    auto card_ref = py::class_<CardRef>(module, "CardRef");
    card_ref
        .def_readonly("code", &CardRef::code)
        .def_readonly("controller", &CardRef::controller)
        .def_readonly("location", &CardRef::location)
        .def_readonly("sequence", &CardRef::sequence)
        .def_readonly("position", &CardRef::position);
    set_public_module(card_ref);

    auto effect_ref = py::class_<EffectRef>(module, "EffectRef");
    effect_ref
        .def_readonly("card", &EffectRef::card)
        .def_readonly("description", &EffectRef::description)
        .def_readonly("client_mode", &EffectRef::client_mode);
    set_public_module(effect_ref);

    auto attack_ref = py::class_<AttackRef>(module, "AttackRef");
    attack_ref
        .def_readonly("card", &AttackRef::card)
        .def_readonly("direct", &AttackRef::direct);
    set_public_module(attack_ref);

    auto tribute_ref = py::class_<TributeRef>(module, "TributeRef");
    tribute_ref
        .def_readonly("card", &TributeRef::card)
        .def_readonly("value", &TributeRef::value);
    set_public_module(tribute_ref);

    auto counter_ref = py::class_<CounterRef>(module, "CounterRef");
    counter_ref
        .def_readonly("card", &CounterRef::card)
        .def_readonly("available", &CounterRef::available);
    set_public_module(counter_ref);

    auto sum_ref = py::class_<SumRef>(module, "SumRef");
    sum_ref
        .def_readonly("card", &SumRef::card)
        .def_readonly("value", &SumRef::value);
    set_public_module(sum_ref);

    auto zone_ref = py::class_<ZoneRef>(module, "ZoneRef");
    zone_ref
        .def(py::init<std::uint8_t, std::uint8_t, std::uint8_t>(), py::arg("player"), py::arg("location"), py::arg("sequence"))
        .def_readonly("player", &ZoneRef::player)
        .def_readonly("location", &ZoneRef::location)
        .def_readonly("sequence", &ZoneRef::sequence);
    set_public_module(zone_ref);

    auto battle = py::class_<BattleDecision>(module, "BattleDecision");
    battle
        .def_property_readonly("kind", [](const BattleDecision&) { return DecisionKind::battle_command; })
        .def_readonly("player", &BattleDecision::player)
        .def_readonly("activatable", &BattleDecision::activatable)
        .def_readonly("attackable", &BattleDecision::attackable)
        .def_readonly("can_main_phase_2", &BattleDecision::can_main_phase_2)
        .def_readonly("can_end_phase", &BattleDecision::can_end_phase)
        .def("response", &BattleDecision::response, py::arg("command"), py::arg("index") = 0);
    set_public_module(battle);

    auto idle = py::class_<IdleDecision>(module, "IdleDecision");
    idle
        .def_property_readonly("kind", [](const IdleDecision&) { return DecisionKind::idle_command; })
        .def_readonly("player", &IdleDecision::player)
        .def_readonly("summonable", &IdleDecision::summonable)
        .def_readonly("special_summonable", &IdleDecision::special_summonable)
        .def_readonly("repositionable", &IdleDecision::repositionable)
        .def_readonly("monster_settable", &IdleDecision::monster_settable)
        .def_readonly("spell_trap_settable", &IdleDecision::spell_trap_settable)
        .def_readonly("activatable", &IdleDecision::activatable)
        .def_readonly("can_battle_phase", &IdleDecision::can_battle_phase)
        .def_readonly("can_end_phase", &IdleDecision::can_end_phase)
        .def_readonly("can_shuffle_hand", &IdleDecision::can_shuffle_hand)
        .def("response", &IdleDecision::response, py::arg("command"), py::arg("index") = 0);
    set_public_module(idle);

    auto effect_yes_no = py::class_<EffectYesNoDecision>(module, "EffectYesNoDecision");
    effect_yes_no
        .def_property_readonly("kind", [](const EffectYesNoDecision&) { return DecisionKind::effect_yes_no; })
        .def_readonly("player", &EffectYesNoDecision::player)
        .def_readonly("card", &EffectYesNoDecision::card)
        .def_readonly("description", &EffectYesNoDecision::description)
        .def("response", &EffectYesNoDecision::response, py::arg("yes"));
    set_public_module(effect_yes_no);

    auto yes_no = py::class_<YesNoDecision>(module, "YesNoDecision");
    yes_no
        .def_property_readonly("kind", [](const YesNoDecision&) { return DecisionKind::yes_no; })
        .def_readonly("player", &YesNoDecision::player)
        .def_readonly("description", &YesNoDecision::description)
        .def("response", &YesNoDecision::response, py::arg("yes"));
    set_public_module(yes_no);

    auto option = py::class_<OptionDecision>(module, "OptionDecision");
    option
        .def_property_readonly("kind", [](const OptionDecision&) { return DecisionKind::option; })
        .def_readonly("player", &OptionDecision::player)
        .def_readonly("options", &OptionDecision::options)
        .def("response", &OptionDecision::response, py::arg("index"));
    set_public_module(option);

    auto card = py::class_<CardDecision>(module, "CardDecision");
    card
        .def_property_readonly("kind", [](const CardDecision&) { return DecisionKind::card; })
        .def_readonly("player", &CardDecision::player)
        .def_readonly("cancelable", &CardDecision::cancelable)
        .def_readonly("min", &CardDecision::min)
        .def_readonly("max", &CardDecision::max)
        .def_readonly("cards", &CardDecision::cards)
        .def("response", &CardDecision::response, py::arg("indices"))
        .def("cancel_response", &CardDecision::cancel_response);
    set_public_module(card);

    auto chain = py::class_<ChainDecision>(module, "ChainDecision");
    chain
        .def_property_readonly("kind", [](const ChainDecision&) { return DecisionKind::chain; })
        .def_readonly("player", &ChainDecision::player)
        .def_readonly("special_count", &ChainDecision::special_count)
        .def_readonly("forced", &ChainDecision::forced)
        .def_readonly("hint_timing", &ChainDecision::hint_timing)
        .def_readonly("opponent_hint_timing", &ChainDecision::opponent_hint_timing)
        .def_readonly("options", &ChainDecision::options)
        .def("response", &ChainDecision::response, py::arg("index"))
        .def("pass_response", &ChainDecision::pass_response);
    set_public_module(chain);

    auto place = py::class_<PlaceDecision>(module, "PlaceDecision");
    place
        .def_property_readonly("kind", [](const PlaceDecision& value) {
            return value.disable_field ? DecisionKind::disable_field : DecisionKind::place;
        })
        .def_readonly("player", &PlaceDecision::player)
        .def_readonly("count", &PlaceDecision::count)
        .def_readonly("unavailable", &PlaceDecision::unavailable)
        .def_readonly("disable_field", &PlaceDecision::disable_field)
        .def("response", &PlaceDecision::response, py::arg("zones"));
    set_public_module(place);

    auto position = py::class_<PositionDecision>(module, "PositionDecision");
    position
        .def_property_readonly("kind", [](const PositionDecision&) { return DecisionKind::position; })
        .def_readonly("player", &PositionDecision::player)
        .def_readonly("card_code", &PositionDecision::card_code)
        .def_readonly("positions", &PositionDecision::positions)
        .def("response", &PositionDecision::response, py::arg("position"));
    set_public_module(position);

    auto tribute = py::class_<TributeDecision>(module, "TributeDecision");
    tribute
        .def_property_readonly("kind", [](const TributeDecision&) { return DecisionKind::tribute; })
        .def_readonly("player", &TributeDecision::player)
        .def_readonly("cancelable", &TributeDecision::cancelable)
        .def_readonly("min", &TributeDecision::min)
        .def_readonly("max", &TributeDecision::max)
        .def_readonly("cards", &TributeDecision::cards)
        .def("response", &TributeDecision::response, py::arg("indices"))
        .def("cancel_response", &TributeDecision::cancel_response);
    set_public_module(tribute);

    auto counter = py::class_<CounterDecision>(module, "CounterDecision");
    counter
        .def_property_readonly("kind", [](const CounterDecision&) { return DecisionKind::counter; })
        .def_readonly("player", &CounterDecision::player)
        .def_readonly("counter_type", &CounterDecision::counter_type)
        .def_readonly("count", &CounterDecision::count)
        .def_readonly("cards", &CounterDecision::cards)
        .def("response", &CounterDecision::response, py::arg("counts"));
    set_public_module(counter);

    auto sum = py::class_<SumDecision>(module, "SumDecision");
    sum
        .def_property_readonly("kind", [](const SumDecision&) { return DecisionKind::sum; })
        .def_readonly("player", &SumDecision::player)
        .def_readonly("mode", &SumDecision::mode)
        .def_readonly("target", &SumDecision::target)
        .def_readonly("min", &SumDecision::min)
        .def_readonly("max", &SumDecision::max)
        .def_readonly("required", &SumDecision::required)
        .def_readonly("cards", &SumDecision::cards)
        .def("response", &SumDecision::response, py::arg("indices"));
    set_public_module(sum);

    auto sort = py::class_<SortDecision>(module, "SortDecision");
    sort
        .def_property_readonly("kind", [](const SortDecision& value) {
            return value.chain ? DecisionKind::sort_chain : DecisionKind::sort_card;
        })
        .def_readonly("player", &SortDecision::player)
        .def_readonly("chain", &SortDecision::chain)
        .def_readonly("cards", &SortDecision::cards)
        .def("response", &SortDecision::response, py::arg("order"))
        .def("cancel_response", &SortDecision::cancel_response);
    set_public_module(sort);

    auto unselect = py::class_<UnselectCardDecision>(module, "UnselectCardDecision");
    unselect
        .def_property_readonly("kind", [](const UnselectCardDecision&) { return DecisionKind::unselect_card; })
        .def_readonly("player", &UnselectCardDecision::player)
        .def_readonly("finishable", &UnselectCardDecision::finishable)
        .def_readonly("cancelable", &UnselectCardDecision::cancelable)
        .def_readonly("min", &UnselectCardDecision::min)
        .def_readonly("max", &UnselectCardDecision::max)
        .def_readonly("selectable", &UnselectCardDecision::selectable)
        .def_readonly("unselectable", &UnselectCardDecision::unselectable)
        .def("response", &UnselectCardDecision::response, py::arg("index"))
        .def("finish_response", &UnselectCardDecision::finish_response);
    set_public_module(unselect);

    auto race = py::class_<AnnounceRaceDecision>(module, "AnnounceRaceDecision");
    race
        .def_property_readonly("kind", [](const AnnounceRaceDecision&) { return DecisionKind::announce_race; })
        .def_readonly("player", &AnnounceRaceDecision::player)
        .def_readonly("count", &AnnounceRaceDecision::count)
        .def_readonly("available", &AnnounceRaceDecision::available)
        .def("response", &AnnounceRaceDecision::response, py::arg("races"));
    set_public_module(race);

    auto attribute = py::class_<AnnounceAttributeDecision>(module, "AnnounceAttributeDecision");
    attribute
        .def_property_readonly("kind", [](const AnnounceAttributeDecision&) { return DecisionKind::announce_attribute; })
        .def_readonly("player", &AnnounceAttributeDecision::player)
        .def_readonly("count", &AnnounceAttributeDecision::count)
        .def_readonly("available", &AnnounceAttributeDecision::available)
        .def("response", &AnnounceAttributeDecision::response, py::arg("attributes"));
    set_public_module(attribute);

    auto announce_card = py::class_<AnnounceCardDecision>(module, "AnnounceCardDecision");
    announce_card
        .def_property_readonly("kind", [](const AnnounceCardDecision&) { return DecisionKind::announce_card; })
        .def_readonly("player", &AnnounceCardDecision::player)
        .def_readonly("opcodes", &AnnounceCardDecision::opcodes)
        .def("response", &AnnounceCardDecision::response, py::arg("code"));
    set_public_module(announce_card);

    auto number = py::class_<AnnounceNumberDecision>(module, "AnnounceNumberDecision");
    number
        .def_property_readonly("kind", [](const AnnounceNumberDecision&) { return DecisionKind::announce_number; })
        .def_readonly("player", &AnnounceNumberDecision::player)
        .def_readonly("options", &AnnounceNumberDecision::options)
        .def("response", &AnnounceNumberDecision::response, py::arg("index"));
    set_public_module(number);

    auto rps = py::class_<RockPaperScissorsDecision>(module, "RockPaperScissorsDecision");
    rps
        .def_property_readonly("kind", [](const RockPaperScissorsDecision&) { return DecisionKind::rock_paper_scissors; })
        .def_readonly("player", &RockPaperScissorsDecision::player)
        .def("response", &RockPaperScissorsDecision::response, py::arg("choice"));
    set_public_module(rps);
}

}
