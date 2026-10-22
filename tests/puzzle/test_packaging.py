from ygo_gym.puzzle import collection


def test_packaged_collection_does_not_need_checkout(tmp_path, monkeypatch):
    package = tmp_path / "installed"
    puzzles = package / "assets/puzzles/group"
    puzzles.mkdir(parents=True)
    (puzzles.parent / "COPYING").write_text("license")
    (puzzles / "example.lua").write_text("Debug.ReloadFieldEnd()")
    monkeypatch.setattr(collection, "files", lambda _: package)
    assert collection.list_builtin() == ("group/example.lua",)
    assert (
        collection.builtin_path("group/example.lua").read_text()
        == "Debug.ReloadFieldEnd()"
    )
