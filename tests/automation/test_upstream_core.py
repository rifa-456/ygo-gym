import subprocess

import pytest

from .repositories import commit, git


def test_no_changes_do_not_create_a_candidate(repositories):
    before = repositories.heads()
    assert not repositories.prepare()
    assert not repositories.output.exists()
    assert repositories.heads() == before


def test_prepare_checkout_publish_and_noop(repositories):
    before = repositories.heads()
    commit(repositories.upstream, "engine.cpp", "upstream fix\n")
    assert repositories.prepare()
    assert repositories.heads() == before
    manifest = repositories.manifest()
    repositories.candidate.checkout(repositories.root, repositories.output)
    core = repositories.root / "third_party/ygopro-core"
    assert git(core, "rev-parse", "HEAD:lua/src") == repositories.lua_new
    assert (core / "engine.cpp").read_text() == "upstream fix\n"
    repositories.publish()
    assert repositories.heads() == (manifest["core_head"], manifest["gym_head"])
    assert not repositories.prepare()


@pytest.mark.parametrize("change", ["pin", "url"])
def test_clean_lua_merge_preserves_fork_and_publishes_dependencies_first(repositories, change):
    before = repositories.heads()
    lua_before = git(repositories.lua_remote, "rev-parse", "master")
    if change == "pin":
        revision = repositories.advance_lua()
    else:
        mirror = repositories.root.parent / "lua-mirror"
        subprocess.run(["git", "clone", "--bare", str(repositories.lua_upstream), str(mirror)],
                       check=True, capture_output=True)
        git(repositories.upstream, "config", "-f", ".gitmodules", "submodule.lua/src.url", mirror.as_posix())
        git(repositories.upstream, "add", ".gitmodules")
        git(repositories.upstream, "commit", "-m", "update upstream Lua URL")
        revision = git(repositories.lua_upstream, "rev-parse", "master")
    assert repositories.prepare()
    assert repositories.heads() == before
    assert git(repositories.lua_remote, "rev-parse", "master") == lua_before
    manifest = repositories.manifest()
    assert manifest["lua_update"]["upstream"] == revision
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


def test_header_change_proceeds_to_testing(repositories):
    before = repositories.heads()
    commit(repositories.upstream, "state.h", "new layout\n")
    assert repositories.prepare()
    assert repositories.heads() == before


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


def test_merge_conflict_does_not_publish(repositories):
    core = repositories.root / "third_party/ygopro-core"
    git(core, "config", "user.name", "Test")
    git(core, "config", "user.email", "test@example.invalid")
    commit(core, "engine.cpp", "fork fix\n")
    git(core, "push", str(repositories.core_remote), "HEAD:master")
    git(core, "checkout", "--detach", git(repositories.root, "rev-parse", "HEAD:third_party/ygopro-core"))
    before = repositories.heads()
    commit(repositories.upstream, "engine.cpp", "conflicting fix\n")
    with pytest.raises(RuntimeError, match="git merge"):
        repositories.prepare()
    assert repositories.heads() == before


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
