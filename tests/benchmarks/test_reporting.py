import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest


pytestmark = pytest.mark.skipif(
    any(importlib.util.find_spec(name) is None for name in ("pyperf", "rich")),
    reason="requires the benchmark dependency group",
)
ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures/runner.py"
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def run_fixture(tmp_path, *options):
    output = tmp_path / "result.json"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    if "rich" in options:
        environment["TERM"] = "xterm-256color"
    command = [sys.executable, str(FIXTURE), "--processes", "2", "--values", "2",
               "--warmups", "0", "--output", str(output), *options]
    result = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                            capture_output=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return result, json.loads(output.read_text(encoding="utf-8"))


def assert_measurements(suite):
    assert len(suite["benchmarks"]) == 2
    for benchmark in suite["benchmarks"]:
        measured = [run for run in benchmark["runs"] if run.get("values")]
        assert len(measured) == 2
        assert sum(len(run["values"]) for run in measured) == 4


def test_calibration_worker_progress_and_diagnostics(tmp_path):
    result, suite = run_fixture(tmp_path, "--min-time", "0.001", "--display", "plain")
    assert_measurements(suite)
    assert "calibrating (" in result.stderr
    assert result.stderr.count("1/2 workers") == 2
    assert result.stderr.count("2/2 workers") == 2
    assert not re.search(r"(?m)^\.+$", result.stdout)
    assert "first:" in result.stdout and "second:" in result.stdout


def test_fixed_loops_preserve_warnings_without_dots(tmp_path):
    result, suite = run_fixture(tmp_path, "--loops", "1", "--display", "plain")
    assert_measurements(suite)
    assert "calibrating" not in result.stderr
    assert "WARNING:" in result.stdout
    assert not re.search(r"(?m)^\.+$", result.stdout)


def test_forced_rich_has_two_rows_and_eta(tmp_path):
    result, suite = run_fixture(tmp_path, "--loops", "1", "--display", "rich")
    assert_measurements(suite)
    display = ANSI.sub("", result.stderr)
    assert "Suite" in display
    assert "2/2 cases" in display
    assert "2/2 workers" in display
    assert "elapsed" in display and "ETA" in display
    assert "WARNING:" in result.stderr
    assert not re.search(r"(?m)^\.+$", ANSI.sub("", result.stdout + result.stderr))


def test_quiet_has_no_progress(tmp_path):
    result, suite = run_fixture(tmp_path, "--loops", "1", "--quiet")
    assert_measurements(suite)
    assert result.stderr == ""
    assert "workers" not in result.stdout
