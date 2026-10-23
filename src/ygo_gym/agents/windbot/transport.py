from __future__ import annotations

import json
import subprocess
from pathlib import Path


class WindBotError(RuntimeError):
    """WindBot could not initialize, communicate, or select a legal action."""


class Worker:
    def __init__(
        self, assembly: Path | tuple[str, ...], *, dotnet: str = "dotnet", timeout: float = 30.0
    ):
        import queue
        import threading

        self.timeout = timeout
        self.process = subprocess.Popen(
            list(assembly) if isinstance(assembly, tuple) else [dotnet, str(assembly)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.output = queue.Queue()
        self.errors: list[str] = []

        def read_output():
            for line in self.process.stdout:
                self.output.put(line)
            self.output.put(None)

        def read_errors():
            for line in self.process.stderr:
                self.errors.append(line.rstrip())
                del self.errors[:-30]

        threading.Thread(target=read_output, daemon=True).start()
        threading.Thread(target=read_errors, daemon=True).start()

    def request(self, **request):
        import queue

        try:
            self.process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
            self.process.stdin.flush()
            line = self.output.get(timeout=self.timeout)
        except (BrokenPipeError, OSError, queue.Empty) as error:
            self.close()
            raise WindBotError(
                f"WindBot worker failed or timed out: {'; '.join(self.errors)}"
            ) from error
        if line is None:
            raise WindBotError(f"WindBot worker exited: {'; '.join(self.errors)}")
        try:
            response = json.loads(line)
        except json.JSONDecodeError as error:
            raise WindBotError(
                f"WindBot worker returned invalid JSON: {line[:200]}"
            ) from error
        if not response["ok"]:
            raise WindBotError(response["error"])
        return response["result"]

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()
