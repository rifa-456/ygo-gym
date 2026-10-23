import pytest

from ygo_gym import (
    ActionKind,
    CardSetup,
    DuelSetup,
    Location,
    PlayerSetup,
    Position,
    Puzzle,
    WinThisTurn,
)
from ygo_gym.dataset.codec import capture as snapshot

NAME = "Duel Links/Naim_DuelLinks_1_10.lua"


def test_builtin_retains_source_and_engine_rules(engine, pytestconfig):
    puzzle = Puzzle.builtin(NAME)
    original = pytestconfig.rootpath / "third_party/Puzzles" / NAME
    assert puzzle.source.encode() == original.read_bytes()
    assert puzzle.source in puzzle.to_lua()
    with puzzle.start(engine, seed=1) as episode:
        duel = episode.duel
        assert duel.state().player(0).life_points == 4000
        assert duel.state().player(1).life_points == 100
        assert len(duel.state().relations) > 0
        with duel.clone(preserve_rng=True) as branch:
            assert snapshot(duel) == snapshot(branch)
        for _ in range(12):
            if episode.ended:
                break
            index = next(
                i
                for kind in (ActionKind.END_PHASE, ActionKind.PASS)
                for i, a in enumerate(episode.actions)
                if a.kind == kind
            )
            episode.step(index)
        assert episode.terminated and int(episode.duel.outcome.winner) == 1


def test_python_puzzle_can_win_through_real_battle(engine):
    setup = DuelSetup(
        players=(PlayerSetup(), PlayerSetup(life_points=100)),
        cards=(
            CardSetup(89631139, 0, 0, Location.MONSTER_ZONE, 0, Position.FACEUP_ATTACK),
        ),
    )
    puzzle = Puzzle("direct-attack", setup=setup, objective=WinThisTurn())
    with puzzle.start(engine, seed=1) as episode:
        for _ in range(20):
            if episode.ended:
                break
            choices = [
                i
                for kind in (
                    ActionKind.BATTLE_PHASE,
                    ActionKind.ATTACK,
                    ActionKind.SELECT_CARD,
                    ActionKind.CONFIRM,
                    ActionKind.YES,
                    ActionKind.PASS,
                )
                for i, a in enumerate(episode.actions)
                if a.kind == kind
            ]
            assert choices, episode.actions
            episode.step(choices[0])
        assert int(episode.duel.outcome.winner) == 0


def test_collection_listing_and_missing_files():
    assert NAME in Puzzle.list_builtin()
    assert "Puzzle Creator.lua" not in Puzzle.list_builtin()
    for name in ("../COPYING", "/tmp/puzzle.lua", "a\\b.lua"):
        with pytest.raises(ValueError):
            Puzzle.builtin(name)
    with pytest.raises(FileNotFoundError):
        Puzzle.builtin("missing.lua")


def test_script_errors_are_reported(engine, tmp_path):
    script = tmp_path / "broken.lua"
    script.write_text('error("broken puzzle")')
    with pytest.raises(RuntimeError, match="broken puzzle"):
        Puzzle.from_lua(script).start(engine, seed=0)
