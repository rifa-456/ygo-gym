from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


class WindBotError(RuntimeError):
    """WindBot could not initialize, communicate, or select a legal action."""


def checkout(root: str | Path | None = None) -> Path:
    if root is None:
        candidates = (
            Path(__file__).resolve().parents[4],
            Path.cwd(),
            *Path.cwd().parents,
        )
        root = next(
            (
                path
                for path in candidates
                if (path / "integrations/windbot/Host/Host.csproj").is_file()
            ),
            candidates[0],
        )
    root = Path(root).resolve()
    if not (root / "third_party/WindBot/Game/GameBehavior.cs").is_file():
        raise FileNotFoundError(
            "WindBot sources are missing; initialize third_party/WindBot"
        )
    return root


def build(root: str | Path | None = None, *, dotnet: str = "dotnet") -> Path:
    """Build the optional worker; reuse an unchanged build on subsequent calls."""
    root = checkout(root)
    executable = shutil.which(dotnet)
    if executable is None:
        raise WindBotError(
            "Building WindBot requires the .NET 8 SDK; supply dotnet= if it is outside PATH"
        )
    project = root / "integrations/windbot/Host/Host.csproj"
    sources = sorted((root / "integrations/windbot/Host").glob("*"))
    sources += sorted((root / "third_party/WindBot").rglob("*.cs"))
    digest = hashlib.sha256()
    for source in sources:
        if source.is_file() and not {"obj", "bin", ".git"}.intersection(source.parts):
            digest.update(str(source.relative_to(root)).encode())
            digest.update(source.read_bytes())
    stamp = digest.hexdigest()
    output = root / "build/windbot" / stamp[:16]
    assembly = output / "Host.dll"
    marker = output / "source.sha256"
    if assembly.is_file() and marker.is_file() and marker.read_text() == stamp:
        shutil.copy2(root / "integrations/windbot/LICENSE", output / "COPYING")
        shutil.copy2(root / "third_party/WindBot/LICENSE", output / "WindBot-LICENSE")
        return assembly
    result = subprocess.run(
        [
            executable,
            "build",
            str(project),
            "--configuration",
            "Release",
            "--output",
            str(output),
            f"-p:BaseIntermediateOutputPath={output / 'obj'}/",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise WindBotError(
            f"WindBot worker build failed:\n{result.stdout}\n{result.stderr}"
        )
    shutil.copy2(root / "integrations/windbot/LICENSE", output / "COPYING")
    shutil.copy2(root / "third_party/WindBot/LICENSE", output / "WindBot-LICENSE")
    marker.write_text(stamp)
    return assembly


class Worker:
    def __init__(
        self, assembly: Path, *, dotnet: str = "dotnet", timeout: float = 30.0
    ):
        import queue
        import threading

        self.timeout = timeout
        self.process = subprocess.Popen(
            [dotnet, str(assembly)],
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
