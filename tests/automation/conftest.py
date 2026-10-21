import importlib

import pytest

from .repositories import create_repositories


@pytest.fixture
def repositories(tmp_path, monkeypatch, pytestconfig):
    monkeypatch.setenv("GIT_ALLOW_PROTOCOL", "file")
    scripts = pytestconfig.rootpath / ".github/scripts/dependency_updates"
    monkeypatch.syspath_prepend(str(scripts))
    return create_repositories(
        tmp_path, importlib.import_module("candidate"), importlib.import_module("publish"),
    )
