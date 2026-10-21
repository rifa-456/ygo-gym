import hashlib
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
    git(path, "config", "-f", ".gitmodules", f"submodule.{location}.url", url.as_posix())
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
    candidate: object
    publisher: object

    @property
    def output(self) -> Path:
        return self.root.parent / "candidate"

    def prepare(self) -> bool:
        return self.candidate.prepare(self.root, self.output,
                                      str(self.core_remote), str(self.upstream))

    def publish(self) -> None:
        self.publisher.publish(self.root, self.output, "fixture-token",
                               str(self.core_remote), str(self.gym_remote))

    def manifest(self) -> dict:
        return json.loads((self.output / "candidate.json").read_text())

    def heads(self) -> tuple[str, str]:
        return (git(self.core_remote, "rev-parse", "master"),
                git(self.gym_remote, "rev-parse", "main"))


def create_repositories(tmp_path: Path, candidate, publisher) -> Repositories:
    lua = tmp_path / "lua"
    initialize(lua)
    lua_old = commit(lua, "runtime.c", "old Lua")
    lua_new = commit(lua, "runtime.c", "fork Lua")
    upstream = tmp_path / "upstream"
    initialize(upstream)
    commit(upstream, "engine.cpp", "base\n")
    commit(upstream, "state.h", "layout\n")
    submodule(upstream, "lua/src", lua, lua_old)
    fork = tmp_path / "fork"
    subprocess.run(["git", "clone", str(upstream), str(fork)], check=True, capture_output=True)
    git(fork, "config", "user.name", "Test")
    git(fork, "config", "user.email", "test@example.invalid")
    submodule(fork, "lua/src", lua, lua_new)
    commit(fork, "clone/tests/layout.json",
           json.dumps(hashlib.sha256(b"layout\n").hexdigest()))
    commit(fork, "clone/tests/check_layout.py", (
        "import hashlib, json\nfrom pathlib import Path\n"
        "p = Path(__file__).resolve()\n"
        "actual = hashlib.sha256((p.parents[2] / 'state.h').read_text().encode()).hexdigest()\n"
        "assert actual == json.loads(p.with_name('layout.json').read_text())\n"
    ))
    core_remote = tmp_path / "core.git"
    subprocess.run(["git", "clone", "--bare", str(fork), str(core_remote)],
                   check=True, capture_output=True)
    gym = tmp_path / "gym"
    initialize(gym, "main")
    commit(gym, "project.toml", "fixture")
    submodule(gym, "third_party/ygopro-core", core_remote, git(fork, "rev-parse", "HEAD"))
    gym_remote = tmp_path / "gym.git"
    subprocess.run(["git", "clone", "--bare", str(gym), str(gym_remote)],
                   check=True, capture_output=True)
    root = tmp_path / "checkout"
    subprocess.run(["git", "clone", "--recurse-submodules", str(gym_remote), str(root)],
                   check=True, capture_output=True)
    return Repositories(root, upstream, core_remote, gym_remote, lua_new, candidate, publisher)
