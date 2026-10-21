from time import perf_counter

from benchmarks.reporting.progress import Report
from benchmarks.reporting.pyperf import ReportingRunner


runner = ReportingRunner(program_args=(__file__,))
runner.argparser.add_argument("--display", choices=("rich", "plain"), default="plain")
args = runner.parse_args()


def workload(loops):
    start = perf_counter()
    for _ in range(loops):
        sum(range(10))
    return perf_counter() - start


with Report("Reporting integration", 2, args.display,
            quiet=args.worker or args.quiet, worker_total=args.processes) as report:
    runner.report = report
    for name in ("first", "second"):
        report.start(name)
        runner.bench_time_func(name, workload)
        report.advance()
