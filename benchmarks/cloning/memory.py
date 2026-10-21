import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import subprocess
import sys

from benchmarks.measurement.process_memory import reader
from benchmarks.measurement.provenance import PROJECT_ROOT, collect
from .cases import add_arguments, command_arguments, positive, selected
from .scenarios import create


def measure(case, count: int, metric: str) -> dict:
    engine, source = create(PROJECT_ROOT, case.scenario, case.scenario_seed)
    with source:
        memory_bytes = reader(metric)
        gc.collect()
        baseline = memory_bytes()
        with ExitStack() as stack:
            for _ in range(count):
                stack.enter_context(source.clone(**case.clone_options))
            retained = memory_bytes()
        gc.collect()
        released = memory_bytes()
        return {"scenario": case.scenario, "mode": case.mode,
                "scenario_seed": case.scenario_seed,
                "clone_seed": case.clone_seed if case.mode == "seeded" else None,
                "live_clones": count, "metric": metric,
                "baseline_bytes": baseline, "retained_bytes": retained,
                "growth_bytes": retained - baseline, "after_close_bytes": released}


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure retained-clone process memory in isolated runs")
    add_arguments(parser)
    parser.add_argument("--counts", nargs="+", type=positive, default=[1, 8, 32, 128])
    parser.add_argument("--repetitions", type=positive, default=3)
    parser.add_argument("--metric", choices=("rss", "peak-rss"), default="rss")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/cloning-memory.json"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    cases = selected(args)
    counts = sorted(set(args.counts))
    if args.worker:
        if len(cases) != 1 or len(counts) != 1:
            parser.error("a memory worker requires exactly one scenario, mode, and count")
        print(json.dumps(measure(cases[0], counts[0], args.metric)))
        return
    if args.output.exists():
        parser.error(f"output already exists: {args.output}; choose another filename")
    manifest = collect(PROJECT_ROOT, args.build_label)
    records = []
    for case in cases:
        for count in counts:
            for repetition in range(args.repetitions):
                command = [sys.executable, "-m", "benchmarks.cloning", "memory", "--worker",
                           *command_arguments(case, args.build_label), "--counts", str(count),
                           "--metric", args.metric]
                result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True,
                                        encoding="utf-8", errors="replace")
                if result.returncode:
                    raise RuntimeError(f"{case.name}/{count} failed:\n{result.stderr}")
                record = json.loads(result.stdout)
                record["repetition"] = repetition
                records.append(record)
            print(f"{case.name}: {count} retained clones, {args.repetitions} independent runs")
    result = {"schema_version": 2, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "manifest": manifest, "measurement": {
                  "isolation": "fresh process per scenario, mode, clone count, and repetition",
                  "metric": args.metric,
                  "interpretation": "process-level memory includes allocator effects; peak-rss cannot decrease",
              }, "runs": records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(args.output)
