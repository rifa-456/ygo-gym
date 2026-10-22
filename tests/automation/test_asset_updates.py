import subprocess

import pytest

from .repositories import commit, git


@pytest.mark.parametrize("path", ["third_party/CardScripts", "third_party/BabelCDB", "third_party/Puzzles"])
def test_asset_only_update_can_publish_without_core_changes(repositories, path):
    original_core = repositories.heads()[0]
    revision = repositories.advance_asset(path)
    assert repositories.prepare()
    candidate = repositories.manifest()
    assert candidate["core_head"] == original_core
    assert candidate["lua_update"] is None
    repositories.publish()
    assert repositories.heads()[0] == original_core
    assert git(repositories.gym_remote, "rev-parse", f"main:{path}") == revision
    assert not repositories.prepare()


def test_core_lua_and_assets_are_pinned_in_one_tested_candidate(repositories):
    commit(repositories.upstream, "engine.cpp", "upstream fix\n")
    repositories.advance_lua()
    revisions = {path: repositories.advance_asset(path) for path in repositories.asset_sources}
    before = repositories.heads()
    assert repositories.prepare()
    assert repositories.heads() == before
    consumer = repositories.root.parent / "consumer"
    subprocess.run(["git", "clone", "--recurse-submodules", str(repositories.gym_remote), str(consumer)],
                   check=True, capture_output=True)
    for path in revisions:
        repositories.advance_asset(path, "newer revision after candidate was prepared")
    repositories.candidate.checkout(consumer, repositories.output)
    for path, revision in revisions.items():
        assert git(consumer / path, "rev-parse", "HEAD") == revision
    repositories.publish()
    for path, revision in revisions.items():
        assert git(repositories.gym_remote, "rev-parse", f"main:{path}") == revision
    changed = set(git(repositories.root, "diff", "--name-only", "HEAD^", "HEAD").splitlines())
    assert changed == {"third_party/ygopro-core", *revisions}


def test_failed_asset_fetch_does_not_publish(repositories):
    before = repositories.heads()
    repositories.asset_remotes["third_party/BabelCDB"] = str(repositories.root.parent / "missing.git")
    with pytest.raises(RuntimeError, match="git fetch"):
        repositories.prepare()
    assert repositories.heads() == before
