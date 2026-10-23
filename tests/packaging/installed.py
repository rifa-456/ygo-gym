import json
import shutil
from pathlib import Path

import ygo_gym
from ygo_gym import Deck, Engine, Puzzle, play
from ygo_gym.agents import RandomAgent
from ygo_gym.agents.windbot import WindBotAgent, available_decks
from ygo_gym.assets.location import source_checkout
from ygo_gym.dataset.codec import capture


def main():
    assert shutil.which("dotnet") is None
    assert source_checkout() is None
    engine = Engine()
    package = Path(ygo_gym.__file__).parent
    assert engine.card_database.is_relative_to(package)
    assert all(path.is_relative_to(package) for path in engine.script_roots)
    deck = Deck((69247929,) * 40)
    with engine.create_duel(deck, deck, seed=42) as source:
        assert source.actions
        with source.clone(preserve_rng=True) as branch:
            assert capture(source) == capture(branch)
        with engine.deserialize(source.serialize()) as restored:
            assert capture(source) == capture(restored)
    names = Puzzle.list_builtin()
    assert len(names) > 400
    with Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua").start(engine, seed=1) as puzzle:
        assert puzzle.duel.state().player(1).life_points == 100
    variants = available_decks(dotnet="must-not-be-used")
    assert any(entry.id == "OldSchool" and entry.available for entry in variants)
    try:
        WindBotAgent(engine, deck="unknown-executor", dotnet="must-not-be-used")
    except ValueError:
        pass
    else:
        raise AssertionError("unknown executor was accepted")
    with WindBotAgent(engine, deck="OldSchool", dotnet="must-not-be-used") as bot:
        assert len(bot.worker.process.args) == 1
        assert bot.root is None
        with engine.create_duel(bot.deck, bot.deck, seed=17) as duel:
            result = play(duel, agents=(bot, RandomAgent()), max_steps=1000, seed=1)
            assert result.terminated and not result.truncated
    print(json.dumps({"installed_package": str(package), "puzzles": len(names),
                      "executors": len(variants), "windbot_steps": result.step_count}))


if __name__ == "__main__":
    main()
