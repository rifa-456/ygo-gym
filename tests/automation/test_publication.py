import pytest

from .repositories import commit, git


@pytest.mark.parametrize("advanced", ["gym", "core", "lua"])
def test_concurrent_changes_are_not_overwritten(repositories, advanced):
    repositories.advance_lua()
    assert repositories.prepare()
    paths = {
        "gym": repositories.root,
        "core": repositories.root / "third_party/ygopro-core",
        "lua": repositories.root / "third_party/ygopro-core/lua/src",
    }
    path = paths[advanced]
    manifest = repositories.manifest()
    base = manifest["lua_update"]["base"] if advanced == "lua" else manifest[f"{advanced}_base"]
    git(path, "checkout", "--detach", base)
    commit(path, "concurrent.txt", "another maintainer's change")
    remote = {"gym": repositories.gym_remote, "core": repositories.core_remote,
              "lua": repositories.lua_remote}[advanced]
    git(path, "push", str(remote), f"HEAD:{'main' if advanced == 'gym' else 'master'}")
    before = repositories.heads()
    lua_before = git(repositories.lua_remote, "rev-parse", "master")
    with pytest.raises(RuntimeError, match="advanced during testing"):
        repositories.publish()
    assert repositories.heads() == before
    assert git(repositories.lua_remote, "rev-parse", "master") == lua_before



@pytest.mark.parametrize("published", ["lua", "core"])
def test_retry_after_partial_three_repository_publication(repositories, published):
    repositories.advance_lua()
    assert repositories.prepare()
    manifest = repositories.manifest()
    core = repositories.root / "third_party/ygopro-core"
    lua = core / "lua/src"
    git(lua, "push", str(repositories.lua_remote), "HEAD:master")
    if published == "core":
        git(core, "push", str(repositories.core_remote), "HEAD:master")
    git(repositories.root, "checkout", "--detach", manifest["gym_base"])
    git(repositories.root, "submodule", "update", "--init", "--recursive")
    assert repositories.prepare()
    repositories.publish()
    assert git(repositories.lua_remote, "rev-parse", "master") == manifest["lua_update"]["head"]
    final = repositories.manifest()
    assert repositories.heads() == (final["core_head"], final["gym_head"])



def test_retry_after_only_core_was_published(repositories):
    commit(repositories.upstream, "engine.cpp", "upstream fix\n")
    assert repositories.prepare()
    manifest = repositories.manifest()
    core = repositories.root / "third_party/ygopro-core"
    git(core, "push", str(repositories.core_remote), "HEAD:master")
    git(repositories.root, "checkout", "--detach", manifest["gym_base"])
    git(repositories.root, "submodule", "update", "--init", "--recursive")
    assert repositories.prepare()
    assert repositories.manifest()["core_head"] == manifest["core_head"]
    repositories.publish()
    assert repositories.heads()[0] == manifest["core_head"]

