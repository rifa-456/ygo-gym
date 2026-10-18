#include "binding_types.h"

namespace ygo_gym::event {

void bind_enums(py::module_& module) {
    py::enum_<SummonKind>(module, "SummonKind")
        .value("NORMAL", SummonKind::normal)
        .value("SPECIAL", SummonKind::special)
        .value("FLIP", SummonKind::flip);
    py::enum_<SummonStage>(module, "SummonStage")
        .value("ATTEMPT", SummonStage::attempt)
        .value("COMPLETE", SummonStage::complete);
    py::enum_<ChainStage>(module, "ChainStage")
        .value("ACTIVATING", ChainStage::activating)
        .value("ADDED", ChainStage::added)
        .value("RESOLVING", ChainStage::resolving)
        .value("RESOLVED", ChainStage::resolved)
        .value("NEGATED", ChainStage::negated)
        .value("DISABLED", ChainStage::disabled)
        .value("ENDED", ChainStage::ended);
    py::enum_<LifePointKind>(module, "LifePointKind")
        .value("DAMAGE", LifePointKind::damage)
        .value("RECOVER", LifePointKind::recover)
        .value("PAY", LifePointKind::pay)
        .value("SET", LifePointKind::set);
    py::enum_<RelationEventKind>(module, "RelationEventKind")
        .value("EQUIP", RelationEventKind::equip)
        .value("UNEQUIP", RelationEventKind::unequip)
        .value("TARGET", RelationEventKind::target)
        .value("CANCEL_TARGET", RelationEventKind::cancel_target);
    py::enum_<RandomKind>(module, "RandomKind")
        .value("COIN", RandomKind::coin)
        .value("DICE", RandomKind::dice);
    py::enum_<DamageStepStage>(module, "DamageStepStage")
        .value("START", DamageStepStage::start)
        .value("END", DamageStepStage::end);
}

}
