import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter

from ygo_gym import _native

from benchmarks.measurement.provenance import PROJECT_ROOT, collect
from benchmarks.reporting.profiling import PARENTS, show
from benchmarks.reporting.progress import add_argument
from .cases import add_arguments, positive, selected
from .scenarios import choose, create


def nonnegative(value: str) -> int:
    result = int(value)
    if result < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return result


def iteration(source, options, steps: int) -> None:
    with source.clone(**options) as branch:
        for _ in range(steps):
            if branch.terminated:
                break
            branch.step(choose(branch))


def run(case, iterations: int, warmups: int, steps: int, diagnostics: bool,
        wait: bool, quiet: bool, native_profile) -> dict:
    engine, source = create(PROJECT_ROOT, case.scenario, case.scenario_seed)
    completed = 0
    interrupted = False
    data = None
    try:
        for _ in range(warmups):
            iteration(source, case.clone_options, steps)
        if not quiet:
            print(f"PID {os.getpid()}: {case.name}; {iterations} iterations; warmup complete", flush=True)
        if wait:
            input("Attach the native profiler, start collection, then press Enter: ")
        if diagnostics:
            native_profile.begin()
        start = perf_counter()
        try:
            for _ in range(iterations):
                iteration(source, case.clone_options, steps)
                completed += 1
        except KeyboardInterrupt:
            interrupted = True
        finally:
            elapsed = perf_counter() - start
            if diagnostics:
                data = native_profile.end()
        return {"completed_iterations": completed, "interrupted": interrupted,
                "elapsed_seconds": elapsed, "diagnostics": data}
    finally:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-process native clone profiling")
    add_arguments(parser)
    add_argument(parser)
    parser.set_defaults(scenario="simple", mode="exact")
    parser.add_argument("--operation", choices=("clone", "advance"), default="clone")
    parser.add_argument("--iterations", type=positive, default=1000)
    parser.add_argument("--warmups", type=nonnegative, default=10)
    parser.add_argument("--steps", type=positive, default=8)
    parser.add_argument("--diagnostics", action="store_true")
    parser.add_argument("--wait-for-profiler", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/profiles/clone.json"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    native_profile = getattr(_native, "_profiling", None)
    enabled = native_profile is not None and native_profile.diagnostics_enabled
    symbols = native_profile is not None and native_profile.symbols_enabled
    if args.diagnostics and not enabled:
        parser.error("diagnostics require rebuilding with YGO_CLONE_DIAGNOSTICS=ON")
    case = selected(args)[0]
    manifest = collect(PROJECT_ROOT, args.build_label)
    result = run(case, args.iterations, args.warmups, args.steps if args.operation == "advance" else 0,
                 args.diagnostics, args.wait_for_profiler, args.quiet, native_profile)
    result.update({
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(), "case": asdict(case), "operation": args.operation,
        "requested_iterations": args.iterations, "warmups": args.warmups,
        "steps": args.steps if args.operation == "advance" else 0, "manifest": manifest,
        "build": {"symbols_enabled": symbols, "diagnostics_enabled": enabled},
        "measurement": {"workload": "clone + advance + close" if args.operation == "advance" else "clone + close",
                        "warmups_included": False, "setup_included": False,
                        "instrumented": args.diagnostics, "phase_timers": "inclusive",
                        "phase_parents": PARENTS,
                        "counter_scope": "thread-local; successful Lua block copies and selected pointer lookups",
                        "counter_definitions": {
                            "lua_blocks_copied": "successful tracked VM block copies; not total native allocation calls",
                            "lua_bytes_copied": "tracked VM payload bytes; excludes allocator and mapping-table overhead",
                            "lua_translation_lookups": "nonnull calls to the Lua address translator",
                            "core_mapped_lookups": "nonnull calls to the core object-map translator",
                        },
                        "intended_use": "profiling diagnosis; use the timing command for performance comparisons"},
        "output": str(args.output),
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    show(result, args.display, args.quiet)
    if result["interrupted"]:
        raise SystemExit(130)
