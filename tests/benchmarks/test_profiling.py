import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from ygo_gym import _native


pytestmark = pytest.mark.skipif(
    any(importlib.util.find_spec(name) is None for name in ("pyperf", "rich", "psutil")),
    reason="requires the benchmark dependency group",
)
ROOT = Path(__file__).resolve().parents[2]
DIAGNOSTICS = getattr(getattr(_native, "_profiling", None), "diagnostics_enabled", False)


def invoke(output, *options):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run([sys.executable, "-m", "benchmarks.cloning", "profile",
                           "--iterations", "2", "--warmups", "1", "--quiet",
                           "--output", str(output), *options], cwd=ROOT, env=environment,
                          capture_output=True, text=True, timeout=60)


def test_single_process_profile(tmp_path):
    output = tmp_path / "profile.json"
    result = invoke(output)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == result.stderr == ""
    data = json.loads(output.read_text())
    assert data["completed_iterations"] == 2
    assert data["diagnostics"] is None
    assert data["elapsed_seconds"] > 0
    assert data["case"]["scenario"] == "simple"
    assert data["measurement"]["setup_included"] is False
    assert data["measurement"]["warmups_included"] is False
    assert data["measurement"]["workload"] == "clone + close"


def test_existing_output_is_preserved(tmp_path):
    output = tmp_path / "profile.json"
    output.write_text("keep this")
    result = invoke(output)
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert output.read_text() == "keep this"


@pytest.mark.skipif(not DIAGNOSTICS, reason="requires the diagnostic native build")
@pytest.mark.parametrize("scenario", ("simple", "developed", "suspended"))
@pytest.mark.parametrize("mode", ("exact", "seeded", "fresh"))
def test_phase_accounting_excludes_warmup_and_setup(tmp_path, scenario, mode):
    output = tmp_path / "profile.json"
    result = invoke(output, "--diagnostics", "--scenario", scenario, "--mode", mode)
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(output.read_text())
    counts = data["diagnostics"]["counters"]
    times = data["diagnostics"]["phase_nanoseconds"]
    assert counts["clone_attempts"] == counts["clone_successes"] == 2
    assert counts["core_cards"] >= 160
    assert counts["lua_blocks_copied"] > 0
    assert counts["lua_bytes_copied"] > 0
    assert counts["lua_translation_lookups"] > 0
    assert times["host_clone"] >= times["core_clone"] > 0
    assert times["core_clone"] >= times["lua_clone"] >= times["lua_copy_blocks"] > 0
    assert times["host_state_copy"] > 0
    assert times["host_close"] >= times["core_destroy"] > 0
    assert (times["core_reseed"] > 0) == (mode != "exact")


@pytest.mark.skipif(not DIAGNOSTICS, reason="requires the diagnostic native build")
def test_diagnostic_session_guards_and_reset():
    profiler = _native._profiling
    with pytest.raises(RuntimeError, match="no active"):
        profiler.end()
    profiler.begin()
    try:
        with pytest.raises(RuntimeError, match="already active"):
            profiler.begin()
    finally:
        data = profiler.end()
    assert all(value == 0 for value in data["counters"].values())


@pytest.mark.skipif(DIAGNOSTICS, reason="requires the normal native build")
def test_disabled_diagnostics_fails_clearly(tmp_path):
    output = tmp_path / "profile.json"
    result = invoke(output, "--diagnostics")
    assert result.returncode != 0
    assert "YGO_CLONE_DIAGNOSTICS=ON" in result.stderr
    assert not output.exists()
