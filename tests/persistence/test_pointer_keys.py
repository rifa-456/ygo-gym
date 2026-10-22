import shutil
import sqlite3
from pathlib import Path

from ygo_gym import Deck, Engine
from ygo_gym.action import ActionKind as K
from ygo_gym.dataset.codec import capture
from ygo_gym.dataset.initialization import Provenance

from ..duel.comparison import choose


def test_pointer_keys_survive_vm_relocation(engine, deck, tmp_path):
    database = tmp_path / "cards.cdb"
    shutil.copy2(engine.card_database, database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO datas (id,ot,alias,setcode,type,atk,def,level,race,attribute,category) "
            "VALUES (100000003,0,0,0,2,0,0,0,0,0,0)"
        )
    local = Engine(database, (Path(__file__).parent / "scripts", *engine.script_roots))
    provenance = Provenance.capture(local)
    with local.create_duel(Deck(main=(100000003,) * 40), deck, seed=1) as source:
        source.step(choose(source, K.ACTIVATE))
        for _ in range(12):
            if any(a.kind == K.YES for a in source.actions):
                break
            source.step(choose(source, K.PASS, K.SELECT_ZONE))
        else:
            raise AssertionError("script did not yield")
        with local.deserialize(source.serialize(provenance=provenance), provenance=provenance) as loaded:
            for _ in range(8):
                index = choose(source, K.YES, K.PASS, K.END_PHASE, K.SELECT_ZONE)
                source.step(index)
                loaded.step(index)
                assert capture(source) == capture(loaded)
