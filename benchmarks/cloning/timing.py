from pathlib import Path

from benchmarks.measurement.provenance import PROJECT_ROOT, encoded
from benchmarks.reporting.progress import Report, add_argument
from benchmarks.reporting.pyperf import ReportingRunner
from benchmarks.reporting.summaries import timing as show_summary
from .cases import add_arguments, positive, selected
from .workloads import Workload


def worker_arguments(command, args) -> None:
    for name in ("scenario", "mode", "scenario_seed", "clone_seed", "build_label", "operation", "steps"):
        value = getattr(args, name)
        if value is not None:
            command.extend(("--" + name.replace("_", "-"), str(value)))
    command.extend(("--display", "plain"))


def main() -> None:
    runner = ReportingRunner(program_args=("-m", "benchmarks.cloning", "timing"),
                           add_cmdline_args=worker_arguments)
    add_arguments(runner.argparser)
    add_argument(runner.argparser)
    runner.argparser.add_argument("--operation", choices=("latency", "advance", "all"), default="all")
    runner.argparser.add_argument("--steps", type=positive, default=8)
    args = runner.parse_args()
    if args.output and not args.worker:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    runner.metadata["ygo_manifest"] = encoded(PROJECT_ROOT, args.build_label)
    runner.metadata["scenario_seed"] = args.scenario_seed
    cases = selected(args)
    results = []
    total = len(cases) * (2 if args.operation == "all" else 1)
    with Report("Clone timing", total, args.display, quiet=args.worker or args.quiet,
                worker_total=args.processes) as report:
        runner.report = report
        for case in cases:
            workload = Workload(PROJECT_ROOT, case, args.steps)
            metadata = {"rng_mode": case.mode,
                        "clone_seed": case.clone_seed if case.mode == "seeded" else "not applicable"}
            try:
                operations = []
                if args.operation in ("latency", "all"):
                    operations.append(("clone", workload.clone_latency))
                if args.operation in ("advance", "all"):
                    operations.append((f"clone+advance({args.steps})", workload.clone_and_advance))
                for operation, function in operations:
                    name = f"{case.name}/{operation}"
                    report.start(name)
                    benchmark = runner.bench_time_func(name, function, metadata=metadata)
                    if benchmark is not None:
                        results.append(benchmark)
                    report.advance()
            finally:
                workload.close()
    if not args.worker:
        show_summary(report, results)
        if args.output or args.append:
            report.saved(args.output or args.append)
