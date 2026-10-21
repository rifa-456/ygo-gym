import json
import os
import subprocess
import sys
from pathlib import Path

from git import Repository

CORE_PATH = "third_party/ygopro-core"
CORE_URL = "https://github.com/rifa-456/ygopro-core.git"
UPSTREAM_URL = "https://github.com/edo9300/ygopro-core.git"
GYM_URL = "https://github.com/rifa-456/ygo-gym.git"


def prepare(root: Path, output: Path, core_url: str = CORE_URL,
            upstream_url: str = UPSTREAM_URL) -> bool:
    gym, core = Repository(root), Repository(root / CORE_PATH)
    if gym.command("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("Prepare requires a clean checkout")
    gym_base = gym.head()
    gym.command("submodule", "update", "--init", "--recursive", "--", CORE_PATH)
    if core.command("rev-parse", "--is-shallow-repository") == "true":
        core.command("fetch", "--unshallow", core_url, "master")
    core_base = core.fetch(core_url, "master")
    pinned_core = gym.command("rev-parse", f"HEAD:{CORE_PATH}")
    if not core.ancestor(pinned_core, core_base):
        raise RuntimeError("Core fork does not descend from YGO Gym's current pin; manual review required")
    core.command("checkout", "--detach", core_base)
    upstream = core.fetch(upstream_url, "master")
    lua = core.lua(core_base)
    if not core.ancestor(upstream, core_base):
        bases = core.command("merge-base", "--all", core_base, upstream).splitlines()
        if len(bases) != 1:
            raise RuntimeError("Ambiguous upstream merge base; manual review required")
        if core.lua(bases[0]) != core.lua(upstream):
            raise RuntimeError("Upstream changed Lua; manual compatibility review required")
        core.identity()
        core.command("merge", "--no-ff", "--no-edit", upstream)
    if core.lua("HEAD") != lua:
        raise RuntimeError("Merge changed our Lua dependency; manual review required")
    core_head = core.head()
    if pinned_core == core_head:
        return False
    subprocess.run([sys.executable, str(core.path / "clone/tests/check_layout.py")], check=True)
    gym.identity()
    gym.command("add", "--", CORE_PATH)
    gym.command("commit", "-m", "build(engine): update tested upstream core")
    output.mkdir(parents=True, exist_ok=True)
    core.command("bundle", "create", str(output / "core.bundle"), "HEAD")
    gym.command("bundle", "create", str(output / "gym.bundle"), "HEAD")
    manifest = {
        "gym_base": gym_base, "gym_head": gym.head(),
        "core_base": core_base, "core_head": core_head,
        "upstream": upstream, "lua": list(lua),
    }
    (output / "candidate.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared core {core_head} and YGO Gym {gym.head()}")
    return True


def checkout(root: Path, output: Path) -> dict:
    manifest = json.loads((output / "candidate.json").read_text())
    gym, core = Repository(root), Repository(root / CORE_PATH)
    gym.import_bundle(output / "gym.bundle", manifest["gym_head"])
    core.import_bundle(output / "core.bundle", manifest["core_head"])
    if gym.command("rev-parse", f"HEAD:{CORE_PATH}") != core.head():
        raise RuntimeError("Candidate YGO Gym does not pin the candidate core")
    gym.command("submodule", "sync", "--recursive")
    gym.command("submodule", "update", "--init", "--recursive")
    return manifest


def set_changed(changed: bool) -> None:
    value = "true" if changed else "false"
    print(f"changed={value}")
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as stream:
            stream.write(f"changed={value}\n")
