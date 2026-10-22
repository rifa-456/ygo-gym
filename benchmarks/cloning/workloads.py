from time import perf_counter

from .cases import Case
from .scenarios import choose, create


class Workload:
    def __init__(self, root, case: Case, steps: int):
        self.root = root
        self.case = case
        self.steps = steps
        self.engine = None
        self._source = None
        self._checkpoint = None
        self.options = case.clone_options

    @property
    def source(self):
        if self._source is None:
            self.engine, self._source = create(self.root, self.case.scenario, self.case.scenario_seed)
        return self._source

    @property
    def checkpoint(self):
        if self._checkpoint is None:
            self._checkpoint = self.source.checkpoint()
        return self._checkpoint

    def close(self) -> None:
        self._checkpoint = None
        if self._source is not None:
            self._source.close()
            self._source = None
            self.engine = None

    def clone_latency(self, loops: int) -> float:
        source = self.source
        elapsed = 0.0
        for _ in range(loops):
            start = perf_counter()
            branch = source.clone(**self.options)
            elapsed += perf_counter() - start
            branch.close()
        return elapsed

    def clone_and_advance(self, loops: int) -> float:
        source = self.source
        elapsed = 0.0
        for _ in range(loops):
            start = perf_counter()
            with source.clone(**self.options) as branch:
                for _ in range(self.steps):
                    if branch.terminated:
                        break
                    branch.step(choose(branch))
            elapsed += perf_counter() - start
        return elapsed

    def restore_latency(self, loops: int) -> float:
        source, checkpoint = self.source, self.checkpoint
        elapsed = 0.0
        for _ in range(loops):
            start = perf_counter()
            source.restore(checkpoint, **self.options)
            elapsed += perf_counter() - start
        return elapsed

    def restore_and_advance(self, loops: int) -> float:
        source, checkpoint = self.source, self.checkpoint
        start = perf_counter()
        for _ in range(loops):
            source.restore(checkpoint, **self.options)
            for _ in range(self.steps):
                if source.terminated:
                    break
                source.step(choose(source))
        return perf_counter() - start
