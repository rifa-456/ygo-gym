import json
import subprocess
from dataclasses import dataclass
from pathlib import Path



def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def initialize(path: Path, branch: str = "master") -> None:
    path.mkdir()
    git(path, "init", "-b", branch)
    git(path, "config", "user.name", "Test")
    git(path, "config", "user.email", "test@example.invalid")


def commit(path: Path, filename: str, text: str) -> str:
    target = path / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    git(path, "add", "--", filename)
    git(path, "commit", "-m", "fixture change")
    return git(path, "rev-parse", "HEAD")


def submodule(path: Path, location: str, url: Path, revision: str) -> None:
    git(path, "config", "-f", ".gitmodules", f"submodule.{location}.path", location)
    git(path, "config", "-f", ".gitmodules", f"submodule.{location}.url", url.as_uri())
    git(path, "update-index", "--add", "--cacheinfo", f"160000,{revision},{location}")
    git(path, "add", ".gitmodules")
    git(path, "commit", "-m", "fixture dependency")


@dataclass
class Repositories:
    root: Path
    upstream: Path
    core_remote: Path
    gym_remote: Path
    lua_new: str
    lua_upstream: Path
    lua_remote: Path
    asset_sources: dict[str, Path]
    asset_remotes: dict[str, str]
    candidate: object
    publisher: object

    @property
    def output(self) -> Path:
        return self.root.parent / "candidate"

    def prepare(self) -> bool:
        return self.candidate.prepare(self.root, self.output,
                                      self.core_remote.as_uri(), self.upstream.as_uri(), self.lua_remote.as_uri(),
                                      self.asset_remotes)

    def publish(self) -> None:
        self.publisher.publish(self.root, self.output, "fixture-token",
                               self.core_remote.as_uri(), self.gym_remote.as_uri(), self.lua_remote.as_uri(),
                               self.asset_remotes)

    def manifest(self) -> dict:
        return json.loads((self.output / "candidate.json").read_text())

    def heads(self) -> tuple[str, str]:
        return (git(self.core_remote, "rev-parse", "master"),
                git(self.gym_remote, "rev-parse", "main"))

    def advance_lua(self, filename: str = "runtime.c", content: str = "updated Lua") -> str:
        revision = commit(self.lua_upstream, filename, content)
        git(self.upstream, "update-index", "--cacheinfo", f"160000,{revision},lua/src")
        git(self.upstream, "commit", "-m", "bump upstream Lua")
        return revision

    def advance_asset(self, path: str, content: str = "updated asset") -> str:
        source = self.asset_sources[path]
        revision = commit(source, "asset.txt", content)
        git(source, "push", self.asset_remotes[path], "HEAD:master")
        return revision


def create_repositories(tmp_path: Path, candidate, publisher) -> Repositories:
    lua = tmp_path / "lua"
    initialize(lua)
    lua_old = commit(lua, "runtime.c", "old Lua")
    lua_fork = tmp_path / "lua-fork"
    subprocess.run(["git", "clone", str(lua), str(lua_fork)], check=True, capture_output=True)
    git(lua_fork, "config", "user.name", "Test")
    git(lua_fork, "config", "user.email", "test@example.invalid")
    lua_new = commit(lua_fork, "clone.c", "fork cloning support")
    lua_remote = tmp_path / "lua.git"
    subprocess.run(["git", "clone", "--bare", str(lua_fork), str(lua_remote)],
                   check=True, capture_output=True)
    upstream = tmp_path / "upstream"
    initialize(upstream)
    commit(upstream, "engine.cpp", "base\n")
    commit(upstream, "state.h", "layout\n")
    submodule(upstream, "lua/src", lua, lua_old)
    fork = tmp_path / "fork"
    subprocess.run(["git", "clone", str(upstream), str(fork)], check=True, capture_output=True)
    git(fork, "config", "user.name", "Test")
    git(fork, "config", "user.email", "test@example.invalid")
    submodule(fork, "lua/src", lua_remote, lua_new)
    commit(fork, "clone/clone.cpp", "fork cloning support")
    core_remote = tmp_path / "core.git"
    subprocess.run(["git", "clone", "--bare", str(fork), str(core_remote)],
                   check=True, capture_output=True)
    gym = tmp_path / "gym"
    initialize(gym, "main")
    commit(gym, "project.toml", "fixture")
    submodule(gym, "third_party/ygopro-core", core_remote, git(fork, "rev-parse", "HEAD"))
    asset_sources, asset_remotes = {}, {}
    for name in ["CardScripts", "BabelCDB", "Puzzles", "WindBot"]:
        source, remote = tmp_path / name, tmp_path / f"{name}.git"
        initialize(source)
        revision = commit(source, "asset.txt", "original asset")
        subprocess.run(["git", "clone", "--bare", str(source), str(remote)],
                       check=True, capture_output=True)
        path = f"third_party/{name}"
        submodule(gym, path, remote, revision)
        asset_sources[path], asset_remotes[path] = source, remote.as_uri()
    gym_remote = tmp_path / "gym.git"
    subprocess.run(["git", "clone", "--bare", str(gym), str(gym_remote)],
                   check=True, capture_output=True)
    root = tmp_path / "checkout"
    subprocess.run(["git", "clone", "--recurse-submodules", str(gym_remote), str(root)],
                   check=True, capture_output=True)
    return Repositories(root, upstream, core_remote, gym_remote, lua_new,
                        lua, lua_remote, asset_sources, asset_remotes, candidate, publisher)
