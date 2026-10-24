from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa

from .metrics import BradleyTerry, Metric, SolveRate, WinRate
from .result import GameResult
from .run import read_run

DEFAULT_METRICS: Mapping[str, tuple[Metric, ...]] = {
    "puzzle": (SolveRate(),),
    "duel": (WinRate(), BradleyTerry()),
    "match": (WinRate(), WinRate(unit="match"), BradleyTerry(unit="match")),
}


@dataclass(frozen=True, slots=True)
class Report:
    """Results of an evaluation run and the manifest that makes it reproducible."""

    manifest: Mapping
    results: tuple[GameResult, ...]

    @classmethod
    def load(cls, path: str | Path) -> Report:
        manifest, results = read_run(path)
        return cls(manifest, results)

    def summary(self, metrics: Sequence[Metric] | None = None) -> dict[str, pa.Table]:
        """Tables by metric name; by default, the metrics for the kinds of games played."""
        if metrics is None:
            kinds = {result.kind for result in self.results}
            chosen = {m.name: m for kind in DEFAULT_METRICS if kind in kinds for m in DEFAULT_METRICS[kind]}
            metrics = tuple(chosen.values())
        return {metric.name: metric.compute(self.results) for metric in metrics}
