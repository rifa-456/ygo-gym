import shutil
import sqlite3
from pathlib import Path

import pytest

from ygo_gym import Engine


@pytest.fixture(scope="module")
def match_engine(pytestconfig, tmp_path_factory):
    root = pytestconfig.rootpath
    database = tmp_path_factory.mktemp("match-cards") / "cards.cdb"
    shutil.copy2(root / "third_party/BabelCDB/cards.cdb", database)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            "INSERT OR REPLACE INTO datas "
            "(id, ot, alias, setcode, type, atk, def, level, race, attribute, category) "
            "VALUES (?, 0, 0, 0, ?, ?, 0, 4, 1, 1, 0)",
            [(100000003, 2, 0), (100000004, 17, 2000)],
        )
    scripts = root / "third_party/CardScripts"
    return Engine(
        database, (Path(__file__).parent / "scripts", scripts, scripts / "official")
    )
