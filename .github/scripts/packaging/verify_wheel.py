import argparse
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Exercise an installed wheel outside the checkout")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    wheels = list(args.directory.resolve().glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("expected exactly one wheel for this platform")
    wheel = wheels[0]
    root = Path(__file__).resolve().parents[3]
    with zipfile.ZipFile(wheel) as archive:
        sizes = {"download_bytes": wheel.stat().st_size,
                 "unpacked_bytes": sum(info.file_size for info in archive.infolist())}
        assert "ygo_gym/assets/manifest.json" in archive.namelist()
        assert any(name.endswith("/DotNet-LICENSE.TXT") for name in archive.namelist())
    print(json.dumps({"wheel": wheel.name, **sizes}), flush=True)
    with tempfile.TemporaryDirectory(prefix="ygo-installed-") as temporary:
        work = Path(temporary)
        environment = work / "environment"
        subprocess.run(["uv", "venv", str(environment), "--python", "3.14"], check=True)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], check=True)
        script = work / "installed.py"
        shutil.copy2(root / "tests/packaging/installed.py", script)
        empty_path = work / "empty-path"
        empty_path.mkdir()
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.update(PATH=str(empty_path), DOTNET_ROOT=str(empty_path), DOTNET_MULTILEVEL_LOOKUP="0")
        subprocess.run([str(python), "-I", str(script)], cwd=work, env=env, check=True)


if __name__ == "__main__":
    main()
