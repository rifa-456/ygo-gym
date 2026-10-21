from .progress import Report


PARENTS = {
    "host_state_copy": "host_clone", "core_clone": "host_clone", "core_reseed": "host_clone",
    "core_setup": "core_clone", "core_allocate": "core_clone", "core_objects": "core_clone",
    "core_field": "core_clone", "core_metadata": "core_clone", "lua_clone": "core_clone",
    "lua_collect": "lua_clone", "lua_copy_blocks": "lua_clone", "lua_fix_pointers": "lua_clone",
    "core_destroy": "host_close",
}


def show(result, display: str, quiet: bool) -> None:
    report = Report("Clone profile", 0, display, quiet)
    count = result["completed_iterations"]
    elapsed = result["elapsed_seconds"]
    report.summary("Profiling workload", ("Scenario", "RNG", "Iterations", "Wall time", "Workload"), [
        (result["case"]["scenario"], result["case"]["mode"], count, f"{elapsed:.3f} s",
         result["measurement"]["workload"]),
    ])
    diagnostics = result["diagnostics"]
    if diagnostics is not None:
        times = diagnostics["phase_nanoseconds"]
        rows = []
        for name, total in times.items():
            parent = PARENTS.get(name)
            denominator = times.get(parent, 0)
            share = f"{total / denominator:.1%}" if denominator else "n/a"
            per_clone = f"{total / count / 1e6:.4f}" if count else "n/a"
            rows.append((name, f"{total / 1e6:.3f}", per_clone, parent or "separate total", share))
        report.summary("Native phase times (inclusive; nested rows overlap)",
                       ("Phase", "Total ms", "ms/iteration", "Parent", "% parent"), rows)
        rows = [(name, f"{total:,}", f"{total / count:,.1f}" if count else "n/a")
                for name, total in diagnostics["counters"].items()]
        report.summary("Work counters", ("Counter", "Total", "Per iteration"), rows)
    report.saved(result["output"])
