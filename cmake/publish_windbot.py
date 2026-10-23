import json
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    dotnet, source, destination, rid = sys.argv[1:]
    root = Path(source)
    output = Path(destination)
    subprocess.run(
        [
            dotnet, "publish", str(root / "integrations/windbot/Host/Host.csproj"),
            "--configuration", "Release", "--runtime", rid,
            "--self-contained", "true", "--output", str(output),
            "-p:PublishTrimmed=false", "-p:PublishAot=false", "-p:PublishSingleFile=false",
            f"-p:BaseIntermediateOutputPath={output.parent / 'windbot-obj'}/",
            f"-p:BaseOutputPath={output.parent / 'windbot-bin'}/",
        ],
        cwd=root, check=True,
    )
    sdk = subprocess.check_output([dotnet, "--version"], cwd=root, text=True).strip()
    runtime = json.loads((output / "Host.runtimeconfig.json").read_text())
    assets = json.loads((output.parent / "windbot-obj/project.assets.json").read_text())
    framework = next(
        item for item in runtime["runtimeOptions"]["includedFrameworks"]
        if item["name"] == "Microsoft.NETCore.App"
    )
    package = f"microsoft.netcore.app.runtime.{rid}/{framework['version']}"
    package_root = next(
        Path(folder) / package for folder in assets["packageFolders"]
        if (Path(folder) / package).is_dir()
    )
    for name in ("LICENSE.TXT", "THIRD-PARTY-NOTICES.TXT"):
        notice = next(path for path in package_root.iterdir() if path.name.upper() == name)
        shutil.copy2(notice, output / ("DotNet-" + name))
    metadata = {
        "runtime_identifier": rid,
        "sdk_version": sdk,
        "frameworks": runtime["runtimeOptions"]["includedFrameworks"],
    }
    (output / "build.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
