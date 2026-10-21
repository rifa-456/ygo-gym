import subprocess

import pytest

from .repositories import commit, git


@pytest.mark.parametrize("change", ["pin", "url"])
def test_clean_lua_merge_preserves_fork_and_publishes_dependencies_first(repositories, change):
    before = repositories.heads()
    lua_before = git(repositories.lua_remote, "rev-parse", "master")
    core = repositories.root / "third_party/ygopro-core"
    fork_url = git(core, "config", "--blob", "HEAD:.gitmodules", "--get", "submodule.lua/src.url")
    assert fork_url == repositories.lua_remote.as_uri()
    if change == "pin":
        revision = repositories.advance_lua()
    else:
        mirror = repositories.root.parent / "lua-mirror"
        subprocess.run(["git", "clone", "--bare", str(repositories.lua_upstream), str(mirror)],
                       check=True, capture_output=True)
        git(repositories.upstream, "config", "-f", ".gitmodules", "submodule.lua/src.url", mirror.as_uri())
        git(repositories.upstream, "add", ".gitmodules")
        git(repositories.upstream, "commit", "-m", "update upstream Lua URL")
        revision = git(repositories.lua_upstream, "rev-parse", "master")
    assert repositories.prepare()
    assert repositories.heads() == before
    assert git(repositories.lua_remote, "rev-parse", "master") == lua_before
    manifest = repositories.manifest()
    assert manifest["lua_update"]["upstream"] == revision
    assert manifest["lua_update"]["url"] == fork_url
    assert git(core, "config", "--blob", "HEAD:.gitmodules", "--get", "submodule.lua/src.url") == fork_url
    consumer = repositories.root.parent / "consumer"
    subprocess.run(["git", "clone", "--recurse-submodules", str(repositories.gym_remote), str(consumer)],
                   check=True, capture_output=True)
    repositories.candidate.checkout(consumer, repositories.output)
    lua = consumer / "third_party/ygopro-core/lua/src"
    assert (lua / "clone.c").read_text() == "fork cloning support"
    assert git(lua, "merge-base", "--is-ancestor", revision, "HEAD") == ""
    if change == "pin":
        assert (lua / "runtime.c").read_text() == "updated Lua"
    repositories.publish()
    assert git(repositories.lua_remote, "rev-parse", "master") == manifest["lua_update"]["head"]
    assert repositories.heads() == (manifest["core_head"], manifest["gym_head"])
    assert not repositories.prepare()



def test_lua_conflict_does_not_publish(repositories):
    lua = repositories.root / "third_party/ygopro-core/lua/src"
    git(lua, "config", "user.name", "Test")
    git(lua, "config", "user.email", "test@example.invalid")
    commit(lua, "runtime.c", "fork runtime change")
    git(lua, "push", str(repositories.lua_remote), "HEAD:master")
    git(lua, "checkout", "--detach", repositories.lua_new)
    before = repositories.heads()
    lua_before = git(repositories.lua_remote, "rev-parse", "master")
    repositories.advance_lua()
    with pytest.raises(RuntimeError, match="git merge"):
        repositories.prepare()
    assert repositories.heads() == before
    assert git(repositories.lua_remote, "rev-parse", "master") == lua_before



def test_lua_does_not_track_independent_upstream_releases(repositories):
    commit(repositories.lua_upstream, "runtime.c", "unrequested Lua release")
    commit(repositories.upstream, "engine.cpp", "ordinary core fix\n")
    assert repositories.prepare()
    assert repositories.manifest()["lua_update"] is None
    assert repositories.manifest()["lua"][0] == repositories.lua_new

