from collections import defaultdict
from statistics import mean, median, stdev


def timing(report, benchmarks) -> None:
    rows = []
    for benchmark in benchmarks:
        values = benchmark.get_values()
        runs = sum(bool(run.values) for run in benchmark.get_runs())
        deviation = f"{stdev(values) * 1000:.3f} ms" if len(values) > 1 else "n/a"
        rows.append((benchmark.get_name(), f"{mean(values) * 1000:.3f} ms", deviation, len(values), runs))
    if rows:
        report.summary("Clone timing results", ("Benchmark", "Mean", "Stddev", "Values", "Runs"), rows)


def memory(report, records, metric: str) -> None:
    groups = defaultdict(list)
    for record in records:
        groups[(record["scenario"], record["mode"], record["live_clones"])].append(record["growth_bytes"])
    rows = [(scenario, mode, count, f"{median(values) / 1024**2:.3f}", len(values))
            for (scenario, mode, count), values in groups.items()]
    label = "current RSS" if metric == "rss" else "peak RSS"
    report.summary(f"Retained-clone memory ({label})",
                   ("Scenario", "RNG", "Clones", "Median growth (MiB)", "Runs"), rows)
