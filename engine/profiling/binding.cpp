#include "binding.h"
#include "ygopro-core/ocgapi.h"
#include <stdexcept>

namespace py = pybind11;

namespace ygo_gym::profiling {
namespace {
constexpr const char* phases[] = {
    "host_clone", "host_state_copy", "host_close", "core_clone", "core_setup",
    "core_allocate", "core_objects", "core_field", "core_metadata", "core_reseed",
    "core_destroy", "lua_clone", "lua_collect", "lua_copy_blocks", "lua_fix_pointers",
};
constexpr const char* counters[] = {
    "clone_attempts", "clone_successes", "core_cards", "core_effects", "core_groups",
    "core_mapped_lookups", "lua_blocks_copied", "lua_bytes_copied", "lua_gc_objects",
    "lua_translation_lookups", "lua_external_lookups",
};
static_assert(sizeof(phases) / sizeof(*phases) == OCG_PROFILE_PHASE_COUNT);
static_assert(sizeof(counters) / sizeof(*counters) == OCG_PROFILE_COUNTER_COUNT);

py::dict finish() {
    OCG_CloneProfileRecord record{};
    if(!OCG_CloneProfileEnd(&record))
        throw std::runtime_error("no active clone diagnostic session on this thread");
    py::dict times, counts, result;
    for(int i = 0; i < OCG_PROFILE_PHASE_COUNT; ++i)
        times[phases[i]] = record.nanoseconds[i];
    for(int i = 0; i < OCG_PROFILE_COUNTER_COUNT; ++i)
        counts[counters[i]] = record.counters[i];
    result["phase_nanoseconds"] = times;
    result["counters"] = counts;
    return result;
}
}

void bind(py::module_& module) {
    auto profiling = module.def_submodule("_profiling");
    profiling.attr("diagnostics_enabled") = OCG_CloneProfileEnabled() != 0;
#if defined(YGO_PROFILE_SYMBOLS)
    profiling.attr("symbols_enabled") = true;
#else
    profiling.attr("symbols_enabled") = false;
#endif
    profiling.def("begin", [] {
        if(!OCG_CloneProfileEnabled())
            throw std::runtime_error("clone diagnostics require a build with YGO_CLONE_DIAGNOSTICS=ON");
        if(!OCG_CloneProfileBegin())
            throw std::runtime_error("a clone diagnostic session is already active on this thread");
    });
    profiling.def("end", &finish);
}
}
