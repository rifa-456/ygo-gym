import json
import os
import subprocess
import sys
from dataclasses import replace

import pytest
from ygo_gym import Deck
from ygo_gym.action import ActionKind as K
from ygo_gym.dataset.codec import capture
from ygo_gym.dataset.initialization import Provenance
from ygo_gym.persistence import (
    SnapshotCompatibilityError,
    SnapshotError,
    check_snapshot,
)
from ygo_gym.task import Task, TaskDuel

from ..duel.comparison import choose


def scripted(engine, deck):
    source = engine.create_duel(Deck(main=(100000001,) * 40), deck, seed=123)
    source.step(choose(source, K.ACTIVATE))
    for _ in range(12):
        if any(action.kind == K.SELECT_CARD for action in source.actions):
            source.step(choose(source, K.SELECT_CARD))
            return source
        source.step(choose(source, K.PASS, K.NO, K.SELECT_ZONE))
    source.close()
    pytest.fail("script did not reach a partial card selection")


@pytest.mark.parametrize("suspended", [False, True])
def test_roundtrip(engine, deck, suspended):
    provenance = Provenance.capture(engine)
    with (scripted(engine, deck) if suspended else engine.create_duel(deck, deck, seed=123)) as source:
        with engine.deserialize(source.serialize(provenance=provenance), provenance=provenance) as loaded:
            assert capture(source) == capture(loaded)
            for _ in range(16):
                index = choose(source, K.SELECT_CARD, K.CONFIRM, K.YES, K.PASS, K.SELECT_ZONE, K.END_PHASE)
                source.step(index)
                loaded.step(index)
                assert capture(source) == capture(loaded)
            before = capture(loaded)
            source.close()
            with loaded.clone(preserve_rng=True) as branch:
                assert capture(branch) == before
            checkpoint = loaded.checkpoint()
            loaded.step(0)
            loaded.restore(checkpoint, preserve_rng=True)
            assert capture(loaded) == before


def test_fresh_process(engine, deck, tmp_path):
    provenance = Provenance.capture(engine)
    with scripted(engine, deck) as source:
        data = source.serialize(provenance=provenance)
        frames, actions = [capture(source)], []
        for _ in range(12):
            index = choose(source, K.SELECT_CARD, K.CONFIRM, K.YES, K.PASS, K.SELECT_ZONE, K.END_PHASE)
            actions.append(index)
            source.step(index)
            frames.append(capture(source))
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "database": str(engine.card_database), "scripts": [str(p) for p in engine.script_roots],
        "actions": actions, "frames": frames,
    }))
    script = """
import json,sys
from pathlib import Path
from ygo_gym import Engine
from ygo_gym.dataset.codec import capture
config=json.loads(Path(sys.argv[1]).read_text())
engine=Engine(config['database'],tuple(config['scripts']))
with engine.deserialize(sys.stdin.buffer.read()) as duel:
    assert capture(duel)==config['frames'][0]
    for index,expected in zip(config['actions'],config['frames'][1:],strict=True):
        duel.step(index)
        assert capture(duel)==expected
"""
    subprocess.run([sys.executable, "-c", script, str(config)], input=data, check=True, timeout=60, env=os.environ.copy())


def test_invalid_snapshots(engine, deck):
    provenance = Provenance.capture(engine)
    with engine.create_duel(deck, deck, seed=1) as source:
        data = source.serialize(provenance=provenance)
    for broken in (b"", data[:20], data[:-1], data + b"x", data[:-60] + b"a" + data[-59:]):
        with pytest.raises(SnapshotError):
            engine.deserialize(broken, provenance=provenance)
    different = replace(provenance, native_sha256="other-build")
    assert check_snapshot(engine, data, provenance=different).differences == ("native_sha256",)
    with pytest.raises(SnapshotCompatibilityError):
        engine.deserialize(data, provenance=different)


def accumulating(transition, context):
    context.memory["count"] = context.memory.get("count", 0) + 1
    context.memory["typed"] = (b"bytes", [1, None])
    return (context.memory["count"], -context.memory["count"])


def test_task_state(engine, deck):
    provenance = Provenance.capture(engine)
    task = Task(reward=accumulating, max_steps=10)
    with engine.create_duel(deck, deck, seed=123) as duel:
        source = TaskDuel(duel, task)
        source.step(0)
        data = source.serialize(provenance=provenance)
        with TaskDuel.deserialize(engine, data, task, provenance=provenance) as loaded:
            assert loaded._session.state_dict() == source._session.state_dict()
            source.step(0)
            loaded.step(0)
            assert loaded.result == source.result
        with pytest.raises(SnapshotError, match="Task"):
            TaskDuel.deserialize(engine, data, Task(), provenance=provenance)
