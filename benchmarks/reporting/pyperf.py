from contextlib import redirect_stdout
from io import StringIO

import pyperf
from pyperf._manager import Manager


class ReportingManager(Manager):
    def __init__(self, runner):
        super().__init__(runner)
        runner.report.begin_workers(calibrating=bool(self.calibrate_loops or self.calibrate_warmups))

    def display_run(self, bench, run):
        self.runner.report.worker_finished(bool(run.values), self.nprocess, self.need_nprocess)
        if self.args.verbose:
            super().display_run(bench, run)

    def calibration_done(self):
        super().calibration_done()
        self.runner.report.begin_workers(calibrating=False)


class ReportingRunner(pyperf.Runner):
    report = None

    def _display_result(self, benchmark, checks=True):
        if self.args.worker or self.report is None:
            return super()._display_result(benchmark, checks=checks)
        output = StringIO()
        try:
            with redirect_stdout(output):
                super()._display_result(benchmark, checks=checks)
        finally:
            self.report.output(output.getvalue())

    def _manager(self):
        if self.report is None:
            return super()._manager()
        benchmark = ReportingManager(self).create_bench()
        self._display_result(benchmark)
        return benchmark
