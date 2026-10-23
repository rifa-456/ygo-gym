import sys

import pytest
from ygo_gym.agents.windbot.runtime import WindBotError, Worker


def program(tmp_path, source):
    path = tmp_path / "worker.py"
    path.write_text(source)
    return path


def test_worker_reports_exit(tmp_path):
    path = program(tmp_path, "raise SystemExit(1)\n")
    worker = Worker(path, dotnet=sys.executable, timeout=2)
    try:
        with pytest.raises(WindBotError, match="exited|failed"):
            worker.request(op="catalog")
    finally:
        worker.close()


def test_worker_timeout_closes_process(tmp_path):
    path = program(tmp_path, "import time\ntime.sleep(30)\n")
    worker = Worker(path, dotnet=sys.executable, timeout=0.1)
    with pytest.raises(WindBotError, match="timed out"):
        worker.request(op="catalog")
    assert worker.process.poll() is not None


def test_worker_reports_remote_exception(tmp_path):
    path = program(
        tmp_path,
        'import sys\nfor line in sys.stdin:\n print(\'{"ok":false,"error":"bad executor"}\',flush=True)\n',
    )
    worker = Worker(path, dotnet=sys.executable, timeout=2)
    try:
        with pytest.raises(WindBotError, match="bad executor"):
            worker.request(op="reset")
    finally:
        worker.close()
