from pathlib import Path

from ygo_gym import Deck, Duel, Engine
from ygo_gym.action import ActionKind as Kind
from ygo_gym.protocol import IdleDecision, CardDecision
from ygo_gym.state import Location


KINDS = (Kind.CONFIRM, Kind.SELECT_CARD, Kind.SELECT_ZONE, Kind.PASS, Kind.NO,
         Kind.SUMMON, Kind.END_PHASE, Kind.YES)


def choose(duel: Duel, kinds=KINDS) -> int:
    for kind in kinds:
        for index, action in enumerate(duel.actions):
            if action.kind == kind:
                return index
    raise RuntimeError(f"unsupported benchmark decision: {duel.decision}")


def create(root: Path, name: str, seed: int = 123) -> tuple[Engine, Duel]:
    if name not in ("simple", "developed", "suspended"):
        raise ValueError(f"unknown benchmark scenario: {name}")
    assets = root / "third_party"
    scripts = assets / "CardScripts"
    engine = Engine(assets / "BabelCDB/cards.cdb", (scripts, scripts / "official"))
    ordinary = Deck(main=(69247929,) * 40)
    first = Deck(main=(79571449,) * 40) if name == "suspended" else ordinary
    duel = engine.create_duel(first, ordinary, seed=seed)
    try:
        if name == "developed":
            for _ in range(160):
                state = duel.state()
                occupied = sum(len(state.zone(p, Location.MONSTER_ZONE)) for p in (0, 1))
                if occupied >= 4 and isinstance(duel.decision, IdleDecision):
                    return engine, duel
                duel.step(choose(duel, (Kind.SUMMON, Kind.SELECT_ZONE, Kind.PASS,
                                        Kind.NO, Kind.END_PHASE, Kind.YES)))
            raise RuntimeError("could not construct developed board")
        if name == "suspended":
            duel.step(choose(duel, (Kind.ACTIVATE,)))
            for _ in range(32):
                if isinstance(duel.decision, CardDecision):
                    duel.step(choose(duel, (Kind.SELECT_CARD,)))
                    return engine, duel
                duel.step(choose(duel))
            raise RuntimeError("Graceful Charity did not reach partial selection")
        return engine, duel
    except BaseException:
        duel.close()
        raise
