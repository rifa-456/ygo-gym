#include "protocol/bindings/types.h"

namespace ygo_gym::protocol {

void bind_references(py::module_& module) {
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
}

}
