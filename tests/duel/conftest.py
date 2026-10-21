from collections.abc import Iterator
from pathlib import Path
import shutil
import sqlite3

import pytest
from ygo_gym import Deck, Duel, Engine


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
        connection.execute(
            'INSERT OR REPLACE INTO datas '
            '(id, ot, alias, setcode, type, atk, def, level, race, attribute, category) '
            'VALUES (?, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0)', (SCRIPTED_EFFECT,),
        )
    scripts = root / "third_party/CardScripts"
    return Engine(database, (Path(__file__).parent / "scripts", scripts, scripts / "official"))


@pytest.fixture
def duel(engine: Engine, deck: Deck) -> Iterator[Duel]:
    with engine.create_duel(deck, deck, seed=123) as value:
        yield value
