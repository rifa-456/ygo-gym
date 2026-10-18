#include "binding_types.h"

namespace ygo_gym::event {

void bind_batch(py::module_& module) {
    auto batch = py::class_<Batch>(module, "EventBatch");
    batch
        .def("__len__", &Batch::size)
        .def_property_readonly("cards", &Batch::cards)
        .def("__getitem__", [](const Batch& value, py::ssize_t index) {
            const auto events = value.events();
            return event_object(events.at(normalize_index(index, events.size())));
        });
    public_type(batch);
}

}
