from pathlib import Path

import pyperf

from benchmarks.measurement.provenance import PROJECT_ROOT, encoded
from .cases import add_arguments, positive, selected
from .workloads import Workload


def worker_arguments(command, args) -> None:
    for name in ("scenario", "mode"):
        value = getattr(args, name)
        if value is not None:
            command.extend([f"--{name}", value])
    command.extend(["--scenario-seed", str(args.scenario_seed),
                    "--clone-seed", str(args.clone_seed), "--build-label", args.build_label])
    command.extend(["--operation", args.operation, "--steps", str(args.steps)])


def main() -> None:
    runner = pyperf.Runner(program_args=("-m", "benchmarks.cloning", "timing"),
                           add_cmdline_args=worker_arguments)
    add_arguments(runner.argparser)
    runner.argparser.add_argument("--operation", choices=("latency", "advance", "all"), default="all")
    runner.argparser.add_argument("--steps", type=positive, default=8)
    args = runner.parse_args()
    if args.output and not args.worker:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    runner.metadata["ygo_manifest"] = encoded(PROJECT_ROOT, args.build_label)
    runner.metadata["scenario_seed"] = args.scenario_seed
    for case in selected(args):
        workload = Workload(PROJECT_ROOT, case, args.steps)
        case_metadata = {"rng_mode": case.mode,
                         "clone_seed": case.clone_seed if case.mode == "seeded" else "not applicable"}
        try:
            if args.operation in ("latency", "all"):
                runner.bench_time_func(f"clone/{case.name}", workload.clone_latency,
                                       metadata={**case_metadata, "timed_region": "clone only; close excluded"})
            if args.operation in ("advance", "all"):
                runner.bench_time_func(f"clone_advance/{case.name}/{args.steps}", workload.clone_and_advance,
                                       metadata={**case_metadata, "timed_region": "clone, legal-action selection, steps, close",
                                                 "max_steps_per_branch": args.steps})
        finally:
            workload.close()
