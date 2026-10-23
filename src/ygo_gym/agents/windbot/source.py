from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from ...assets.location import checkout_root
from .transport import WindBotError


def checkout(root: str | Path | None = None) -> Path:
    root = checkout_root(root)
    if not (root / "third_party/WindBot/Game/GameBehavior.cs").is_file():
        raise FileNotFoundError("WindBot sources are missing; initialize third_party/WindBot")
    if not (root / "integrations/windbot/Host/Host.csproj").is_file():
        raise FileNotFoundError("WindBot host project is missing from the checkout")
    return root


def build(root: str | Path | None = None, *, dotnet: str = "dotnet") -> Path:
    """Build the optional worker; reuse an unchanged build on subsequent calls."""
    root = checkout(root)
    executable = shutil.which(dotnet)
    if executable is None:
        raise WindBotError(
            "Building WindBot requires the .NET 10 SDK; supply dotnet= if it is outside PATH"
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
            f"-p:BaseOutputPath={output / 'bin'}/",
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
