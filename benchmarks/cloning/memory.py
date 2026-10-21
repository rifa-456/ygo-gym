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
from benchmarks.reporting.progress import Report, add_argument
from benchmarks.reporting.summaries import memory as show_summary
from .cases import add_arguments, command_arguments, positive, selected
from .scenarios import create


def measure(case, count: int, metric: str) -> dict:
    engine, source = create(PROJECT_ROOT, case.scenario, case.scenario_seed)
    try:
        read = reader(metric)
        gc.collect()
        baseline = read()
        with ExitStack() as stack:
            for _ in range(count):
                stack.enter_context(source.clone(**case.clone_options))
            retained = read()
        gc.collect()
        released = read()
        return {
            "scenario": case.scenario, "mode": case.mode, "source_seed": case.scenario_seed,
            "clone_seed": case.clone_seed if case.mode == "seeded" else None,
            "live_clones": count, "metric": metric, "baseline_bytes": baseline,
            "retained_bytes": retained, "growth_bytes": retained - baseline,
            "after_close_bytes": released,
        }
    finally:
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Retained-clone memory in isolated processes")
    add_arguments(parser)
    add_argument(parser)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--counts", type=positive, nargs="+", default=[1, 8, 32, 128])
    parser.add_argument("--repetitions", type=positive, default=3)
    parser.add_argument("--metric", choices=("rss", "peak-rss"), default="rss")
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/cloning-memory.json"))
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    cases = selected(args)
    if args.worker:
        if len(cases) != 1 or len(args.counts) != 1:
            parser.error("worker requires one case and one clone count")
        print(json.dumps(measure(cases[0], args.counts[0], args.metric)))
        return
    if args.output.exists():
        parser.error(f"output already exists: {args.output}")
    manifest = collect(PROJECT_ROOT, args.build_label)
    records = []
    total = len(cases) * len(args.counts) * args.repetitions
    with Report("Clone memory", total, args.display, args.quiet) as report:
        for case in cases:
            for count in args.counts:
                for repetition in range(1, args.repetitions + 1):
                    report.start(f"{case.name}: {count} clones, run {repetition}/{args.repetitions}")
                    command = [sys.executable, "-m", "benchmarks.cloning", "memory", "--worker",
                               *command_arguments(case, args.build_label), "--counts", str(count),
                               "--metric", args.metric, "--display", "plain"]
                    completed = subprocess.run(command, capture_output=True, text=True,
                                               encoding="utf-8", errors="replace")
                    if completed.returncode:
                        raise RuntimeError(f"Memory worker failed:\n{completed.stderr}")
                    record = json.loads(completed.stdout)
                    record["repetition"] = repetition
                    records.append(record)
                    report.advance()
        result = {
            "schema_version": 2, "created_at": datetime.now(timezone.utc).isoformat(),
            "manifest": manifest,
            "measurement": {"isolation": "one fresh process per case, count and repetition",
                            "metric": args.metric,
                            "interpretation": "retained process-memory growth; includes allocator effects"},
            "runs": records,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    show_summary(report, records, args.metric)
    report.saved(args.output)
