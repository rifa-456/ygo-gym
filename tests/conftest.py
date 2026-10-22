import shutil
import sqlite3
from pathlib import Path

import pytest
from ygo_gym import Deck, Engine

VANILLA = 69247929
SCRIPTED_EFFECT = 100000001


@pytest.fixture(scope="session")
def deck() -> Deck:
    return Deck(main=(VANILLA,) * 40)


@pytest.fixture(scope="session")
def engine(pytestconfig: pytest.Config, tmp_path_factory: pytest.TempPathFactory) -> Engine:
    root = pytestconfig.rootpath
    database = tmp_path_factory.mktemp("cards") / "cards.cdb"
    shutil.copy2(root / "third_party/BabelCDB/cards.cdb", database)
    with sqlite3.connect(database) as connection:
        connection.executemany(
            'INSERT OR REPLACE INTO datas '
            '(id, ot, alias, setcode, type, atk, def, level, race, attribute, category) '
            'VALUES (?, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0)', [(SCRIPTED_EFFECT,), (100000002,)],
        )
    scripts = root / "third_party/CardScripts"
    return Engine(database, (Path(__file__).parent / "duel" / "scripts", scripts, scripts / "official"))
