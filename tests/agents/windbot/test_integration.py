import os
import shutil

import pytest
from ygo_gym import Engine
from ygo_gym.agents import RandomAgent
from ygo_gym.agents.windbot import WindBotAgent, available_decks
from ygo_gym.match import play

pytestmark = pytest.mark.skipif(
    os.environ.get("YGO_TEST_WINDBOT") != "1",
    reason="set YGO_TEST_WINDBOT=1 to run the optional .NET integration",
)


@pytest.fixture(scope="module")
def runtime(pytestconfig):
    dotnet = os.environ.get("YGO_DOTNET", "dotnet")
    if not shutil.which(dotnet):
        pytest.fail("WindBot integration tests require the .NET 10 SDK")
    return pytestconfig.rootpath, dotnet


def test_discovery_and_missing_names(runtime):
    root, dotnet = runtime
    variants = available_decks(root, dotnet=dotnet)
    assert any(row.id == "BE2025" and row.available for row in variants)
    assert any(row.id == "Lucky" and not row.available for row in variants)
    with pytest.raises(ValueError, match="Unknown WindBot"):
        WindBotAgent(
            Engine.from_checkout(root), deck="does-not-exist", root=root, dotnet=dotnet
        )


@pytest.mark.parametrize("variant", ["OldSchool", "Burn", "BE2025"])
def test_real_duel(runtime, variant):
    root, dotnet = runtime
    engine = Engine.from_checkout(root)
    with WindBotAgent(engine, deck=variant, root=root, dotnet=dotnet) as bot:
        assert bot.deck == bot.variant.load()
        with engine.create_duel(bot.deck, bot.deck, seed=17) as duel:
            result = play(duel, agents=(bot, RandomAgent()), max_steps=1000, seed=1)
            assert result.step_count > 5
            assert result.terminated or result.truncated


def test_both_seats_and_repeatability(runtime):
    root, dotnet = runtime
    traces = []
    for _ in range(2):
        engine = Engine.from_checkout(root)
        with WindBotAgent(engine, deck="OldSchool", root=root, dotnet=dotnet) as first:
            with WindBotAgent(
                engine, deck="OldSchool", root=root, dotnet=dotnet
            ) as second:
                with engine.create_duel(first.deck, second.deck, seed=123) as duel:
                    result = play(duel, agents=(first, second), max_steps=100, seed=7)
                    traces.append((result, duel.message_buffer))
    assert traces[0] == traces[1]


def test_winner_ends_client_stream(runtime):
    root, dotnet = runtime
    engine = Engine.from_checkout(root)
    with WindBotAgent(engine, deck="OldSchool", root=root, dotnet=dotnet) as bot:
        with engine.create_duel(bot.deck, bot.deck, seed=456) as duel:
            result = play(duel, agents=(bot, RandomAgent()), max_steps=1000, seed=23)
            assert result.terminated
            packets = duel.observe(0)._client_batch[3]
            assert packets[-1][:2] == bytes((1, 5))


def test_match_callbacks_keep_deck_and_choose_starting_player(runtime):
    from types import SimpleNamespace

    root, dotnet = runtime
    engine = Engine.from_checkout(root)
    with WindBotAgent(engine, deck="OldSchool", root=root, dotnet=dotnet) as bot:
        start = SimpleNamespace(player=0, seed=42, deck=bot.deck)
        bot.match_reset(start)
        choice = bot.choose_first(SimpleNamespace(player=0))
        assert choice in (0, 1)
        assert bot.side_deck(SimpleNamespace(deck=bot.deck)) == bot.deck
        bot.match_end(None)


def test_real_best_of_three_match(runtime):
    from ygo_gym import DuelConfig, Match, MatchRules, play_match

    root, dotnet = runtime
    engine = Engine.from_checkout(root)
    with WindBotAgent(engine, deck="OldSchool", root=root, dotnet=dotnet) as bot:
        rules = MatchRules(
            best_of=3,
            side_decking=True,
            initial_chooser=0,
            duel=DuelConfig(life_points=(4000, 6000), opening_hand=(3, 4)),
            max_steps_per_duel=1000,
        )
        with Match(engine, (bot.deck, bot.deck), rules=rules, seed=17) as match:
            result = play_match(match, agents=(bot, RandomAgent()), seed=23)
            assert result.terminated and not result.truncated
            assert 2 <= len(result.duels) <= 3
            assert all(duel.episode.terminated for duel in result.duels)
            assert match._decks[0] == bot.deck


def test_windbot_competes_in_an_evaluation(runtime):
    from ygo_gym.evaluation import Competitor, evaluate, round_robin

    root, dotnet = runtime
    engine = Engine.from_checkout(root)
    variant = next(row for row in available_decks(root, dotnet=dotnet) if row.id == "OldSchool")
    deck = variant.load()
    competitors = (
        Competitor("windbot", lambda: WindBotAgent(engine, deck="OldSchool", root=root, dotnet=dotnet), deck),
        Competitor("random", RandomAgent, deck),
    )
    report = evaluate(round_robin(competitors, seeds=(1,), max_steps=1000), engine)
    assert len(report.results) == 2
    for result in report.results:
        windbot = next(seat for seat in result.seats if seat.competitor == "windbot")
        assert windbot.agent.name == "windbot" and windbot.agent.config == {"executor": "OldSchool"}
        assert windbot.decisions > 0
