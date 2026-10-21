import json
import os
from pathlib import Path

from git import Repository
import assets
import lua

CORE_PATH = "third_party/ygopro-core"
CORE_URL = "https://github.com/rifa-456/ygopro-core.git"
UPSTREAM_URL = "https://github.com/edo9300/ygopro-core.git"
GYM_URL = "https://github.com/rifa-456/ygo-gym.git"


def prepare(root: Path, output: Path, core_url: str = CORE_URL,
            upstream_url: str = UPSTREAM_URL, lua_url: str = lua.LUA_URL,
            asset_urls: dict[str, str] | None = None) -> bool:
    gym, core = Repository(root), Repository(root / CORE_PATH)
    if gym.command("status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("Prepare requires a clean checkout")
    gym_base = gym.head()
    gym.command("submodule", "update", "--init", "--recursive", "--", CORE_PATH)
    if core.command("rev-parse", "--is-shallow-repository") == "true":
        core.command("fetch", "--unshallow", "--no-recurse-submodules", core_url, "master")
    core_base = core.fetch(core_url, "master")
    pinned_core = gym.command("rev-parse", f"HEAD:{CORE_PATH}")
    if not core.ancestor(pinned_core, core_base):
        raise RuntimeError("Core fork does not descend from YGO Gym's current pin; manual review required")
    core.command("checkout", "--detach", core_base)
    upstream = core.fetch(upstream_url, "master")
    original_lua = core.lua(core_base)
    lua_update = lua.prepare(core, core_base, upstream, lua_url)
    if not core.ancestor(upstream, core_base):
        core.identity()
        incoming = lua.adapt_upstream(core, upstream, lua_update) if lua_update else upstream
        core.command("checkout", "--detach", core_base)
        core.command("merge", "--no-ff", "--no-edit", incoming)
    expected_lua = (lua_update["head"], lua_update["url"]) if lua_update else original_lua
    if core.lua("HEAD") != expected_lua:
        raise RuntimeError("Core does not pin the prepared Lua fork")
    core_head = core.head()
    asset_updates = assets.prepare(root, gym, asset_urls if asset_urls is not None else assets.URLS)
    if pinned_core == core_head and all(row["base"] == row["head"] for row in asset_updates):
        return False
    gym.identity()
    gym.command("add", "--", CORE_PATH, *assets.URLS)
    gym.command("commit", "-m", "build(deps): update tested engine and card assets")
    output.mkdir(parents=True, exist_ok=True)
    core.command("bundle", "create", str(output / "core.bundle"), "HEAD")
    gym.command("bundle", "create", str(output / "gym.bundle"), "HEAD")
    if lua_update:
        Repository(core.path / "lua/src").command("bundle", "create", str(output / "lua.bundle"), "HEAD")
    manifest = {
        "gym_base": gym_base, "gym_head": gym.head(),
        "core_base": core_base, "core_head": core_head,
        "upstream": upstream, "lua": list(expected_lua), "lua_update": lua_update,
        "assets": asset_updates,
    }
    (output / "candidate.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Prepared core {core_head} and YGO Gym {gym.head()}")
    return True


def checkout(root: Path, output: Path) -> dict:
    manifest = json.loads((output / "candidate.json").read_text())
    gym, core = Repository(root), Repository(root / CORE_PATH)
    gym.import_bundle(output / "gym.bundle", manifest["gym_head"])
    core.import_bundle(output / "core.bundle", manifest["core_head"])
    if update := manifest["lua_update"]:
        Repository(core.path / "lua/src").import_bundle(output / "lua.bundle", update["head"])
    if gym.command("rev-parse", f"HEAD:{CORE_PATH}") != core.head():
        raise RuntimeError("Candidate YGO Gym does not pin the candidate core")
    assets.verify_pins(gym, manifest["assets"])
    gym.command("submodule", "sync", "--recursive")
    gym.command("submodule", "update", "--init", "--recursive")
    for row in manifest["assets"]:
        if Repository(root / row["path"]).head() != row["head"]:
            raise RuntimeError(f"Checked out wrong asset revision: {row['path']}")
    return manifest


def set_changed(changed: bool) -> None:
    value = "true" if changed else "false"
    print(f"changed={value}")
    if path := os.environ.get("GITHUB_OUTPUT"):
        with open(path, "a") as stream:
            stream.write(f"changed={value}\n")
