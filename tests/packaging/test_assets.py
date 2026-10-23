import pytest

from ygo_gym import Engine
from ygo_gym.assets import location
from ygo_gym.agents.windbot import runtime


def test_default_engine_uses_live_checkout_from_any_directory(pytestconfig, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    default = Engine()
    explicit = Engine.from_checkout(pytestconfig.rootpath)
    assert default.card_databases == explicit.card_databases
    assert default.script_roots == explicit.script_roots
    assert default.card_database.is_relative_to(pytestconfig.rootpath)


@pytest.mark.parametrize("options", [{"card_database": "cards.cdb"}, {"script_roots": ()}])
def test_custom_assets_require_both_paths(options):
    with pytest.raises(ValueError, match="provide both"):
        Engine(**options)


def test_installed_asset_locations_ignore_working_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(location, "source_checkout", lambda: None)
    monkeypatch.setattr(location, "files", lambda _: tmp_path)
    database, scripts = location.engine_defaults()
    assert database == tmp_path / "assets/database/cards.cdb"
    assert scripts == (tmp_path / "assets/scripts", tmp_path / "assets/scripts/official")
    with pytest.raises(FileNotFoundError, match="supply root"):
        location.checkout_root()


def test_bundled_worker_is_launched_directly(tmp_path, monkeypatch):
    executable = tmp_path / "runtime/Host"
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.setattr(runtime, "source_checkout", lambda: None)
    monkeypatch.setattr(runtime, "directory", lambda *_: tmp_path)
    monkeypatch.setattr(runtime.sys, "platform", "linux")
    selected = runtime.resolve(dotnet="does-not-exist")
    assert selected.command == (str(executable),)
    assert selected.assets == tmp_path
    assert selected.root is None


def test_missing_bundled_worker_has_no_source_build_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "source_checkout", lambda: None)
    monkeypatch.setattr(runtime, "directory", lambda *_: tmp_path)
    with pytest.raises(runtime.WindBotError, match="bundled WindBot worker is missing"):
        runtime.resolve()
