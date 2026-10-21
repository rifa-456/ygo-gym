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



def test_header_change_proceeds_to_testing(repositories):
    before = repositories.heads()
    commit(repositories.upstream, "state.h", "new layout\n")
    assert repositories.prepare()
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

