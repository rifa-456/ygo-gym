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
def test_upstream_lua_update_requires_review(repositories, change):
    before = repositories.heads()
    if change == "pin":
        git(repositories.upstream, "update-index", "--cacheinfo",
            f"160000,{repositories.lua_new},lua/src")
    else:
        git(repositories.upstream, "config", "-f", ".gitmodules", "submodule.lua/src.url", "changed-url")
        git(repositories.upstream, "add", ".gitmodules")
    git(repositories.upstream, "commit", "-m", "update upstream Lua")
    with pytest.raises(RuntimeError, match="Upstream changed Lua"):
        repositories.prepare()
    assert repositories.heads() == before


def test_layout_change_is_not_automatically_approved(repositories):
    before = repositories.heads()
    commit(repositories.upstream, "state.h", "new layout\n")
    with pytest.raises(subprocess.CalledProcessError):
        repositories.prepare()
    assert repositories.heads() == before


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


@pytest.mark.parametrize("advanced", ["gym", "core"])
def test_concurrent_changes_are_not_overwritten(repositories, advanced):
    commit(repositories.upstream, "engine.cpp", "upstream fix\n")
    assert repositories.prepare()
    path = repositories.root if advanced == "gym" else repositories.root / "third_party/ygopro-core"
    manifest = repositories.manifest()
    git(path, "checkout", "--detach", manifest[f"{advanced}_base"])
    commit(path, "concurrent.txt", "another maintainer's change")
    remote = repositories.gym_remote if advanced == "gym" else repositories.core_remote
    git(path, "push", str(remote), f"HEAD:{'main' if advanced == 'gym' else 'master'}")
    before = repositories.heads()
    with pytest.raises(RuntimeError, match="advanced during testing"):
        repositories.publish()
    assert repositories.heads() == before


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
