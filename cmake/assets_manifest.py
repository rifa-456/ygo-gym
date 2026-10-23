import hashlib
import json
import subprocess
import sys
import tomllib
from pathlib import Path


def revision(root):
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def digest(paths, root):
    checksum = hashlib.sha256()
    for path in sorted(paths):
        name = path.relative_to(root).as_posix().encode()
        checksum.update(len(name).to_bytes(8, "little"))
        checksum.update(name)
        with path.open("rb") as stream:
            checksum.update(hashlib.file_digest(stream, "sha256").digest())
    return checksum.hexdigest()


def main():
    root, output = map(Path, sys.argv[1:])
    project = tomllib.loads((root / "pyproject.toml").read_text())
    modules = ["ygopro-core", "CardScripts", "BabelCDB", "Puzzles", "WindBot"]
    scripts = root / "third_party/CardScripts"
    database = root / "third_party/BabelCDB/cards.cdb"
    metadata = {
        "package_version": project["project"]["version"],
        "source_revision": revision(root),
        "dependencies": {
            name: revision(root / "third_party" / name) for name in modules
        },
        "database_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
        "scripts_sha256": digest(scripts.rglob("*.lua"), scripts),
    }
    output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
