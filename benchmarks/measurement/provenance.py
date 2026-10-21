import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

from ygo_gym import _native


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def repository(path: Path) -> dict:
    def git(*args):
        result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        return result.stdout.strip() if result.returncode == 0 else None

    revision = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=normal", "--ignore-submodules=all")
    return {"commit": revision, "dirty": bool(status) if status is not None else None}


def collect(root: Path, build_label: str) -> dict:
    scripts = root / "third_party/CardScripts"
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "build_label": build_label,
        "repositories": {name: repository(path) for name, path in {
            "gym": root,
            "core": root / "third_party/ygopro-core",
            "lua": root / "third_party/ygopro-core/lua/src",
            "cardscripts": scripts,
            "babelcdb": root / "third_party/BabelCDB",
        }.items()},
        "database_sha256": digest(root / "third_party/BabelCDB/cards.cdb"),
        "native_binary_sha256": digest(Path(_native.__file__)),
        "script_sha256": {name: digest(scripts / name) for name in (
            "constant.lua", "utility.lua", "official/c79571449.lua")},
    }


def encoded(root: Path, build_label: str) -> str:
    return json.dumps(collect(root, build_label), sort_keys=True)
