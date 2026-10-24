import pytest
from ygo_gym import Deck, DeckRules, MatchRules, Puzzle
from ygo_gym.agents import RandomAgent
from ygo_gym.dataset import Dataset
from ygo_gym.dataset.codec import capture
from ygo_gym.evaluation import (
    Competitor, DuelGame, PuzzleGame, Report, evaluate, matches, puzzles, round_robin,
)

from .support import CountingAgent

PUZZLE = "Duel Links/Naim_DuelLinks_1_10.lua"
VANILLA = Deck((69247929, 89631139, 46986414) * 14)
RULES = MatchRules(best_of=3, decks=DeckRules.unrestricted(), max_steps_per_duel=120)


@pytest.fixture
def players():
    return Competitor.product({"random": lambda deck: RandomAgent(), "counting": lambda deck: CountingAgent()},
                              {"vanilla": VANILLA})


def test_competitor_product_names_every_agent_deck_pair(players):
    assert [p.name for p in players] == ["random/vanilla", "counting/vanilla"]
    assert all(p.deck == VANILLA for p in players)
    with pytest.raises(ValueError):
        Competitor("", RandomAgent)


def test_schedules_cover_pairs_seats_and_seeds(players):
    third = Competitor("third", RandomAgent, VANILLA)
    games = round_robin((*players, third), seeds=range(2))
    assert len(games) == 3 * 2 * 2
    assert {tuple(c.name for c in g.competitors) for g in games if g.seed == 0} == {
        (a.name, b.name) for a in (*players, third) for b in (*players, third) if a is not b
    }
    assert len(round_robin(players, seeds=range(2), swap_seats=False)) == 2
    assert len(matches(players, seeds=range(3), rules=RULES)) == 3
    assert len(puzzles([Competitor("solver", RandomAgent)], [PUZZLE], seeds=range(4))) == 4
    with pytest.raises(ValueError, match="unique"):
        round_robin((players[0], players[0]), seeds=(0,))


def test_games_validate_their_competitors(players):
    with pytest.raises(ValueError, match="no deck"):
        PuzzleGame(players[0], Puzzle.builtin(PUZZLE), 0)
    with pytest.raises(ValueError, match="distinct"):
        DuelGame((players[0], players[0]), 0)
    with pytest.raises(ValueError, match="decks"):
        DuelGame((players[0], Competitor("solver", RandomAgent)), 0)


def test_evaluate_writes_a_reloadable_run_and_a_linked_dataset(engine, players, tmp_path):
    games = (
        *round_robin(players, seeds=(1,), max_steps=120),
        *puzzles([Competitor("solver", CountingAgent)], [PUZZLE], seeds=(2,)),
        *matches(players, seeds=(3,), rules=RULES),
    )
    run, dataset = tmp_path / "run", tmp_path / "games.duckdb"
    report = evaluate(games, engine, path=run, dataset=dataset)
    assert report.manifest["complete"] and len(report.manifest["games"]) == len(games)
    loaded = Report.load(run)
    assert loaded.results == report.results
    assert {r.kind for r in report.results} == {"duel", "puzzle", "match"}
    assert set(loaded.summary()) == {
        "solve_rate", "win_rate", "bradley_terry", "match_win_rate", "match_bradley_terry"
    }
    with Dataset.open(dataset) as recorded:
        assert {g["game_id"] for g in recorded.games()} == {r.game_id for r in report.results}
    for result in report.results:
        assert result.game_id is not None
        for seat in result.seats:
            reports = seat.competitor in ("counting/vanilla", "solver")
            assert seat.stats == ({"calls": float(seat.decisions)} if reports else {})
        assert sum(s.decisions for s in result.seats) == result.steps
        with result.replay.play(engine) as again:
            assert again.replay() == result.replay


def test_match_results_follow_seats_and_report_the_series(engine, players):
    report = evaluate(matches(players, seeds=(5,), rules=RULES), engine)
    duels = report.results
    assert [r.duel for r in duels] == list(range(len(duels)))
    assert len({r.match_winner for r in duels}) == 1
    for result in duels:
        assert set(result.competitors) == {p.name for p in players}
        assert result.replay.seed == result.seed


def test_replays_reproduce_evaluated_duels(engine, players):
    result = evaluate(round_robin(players, seeds=(7,), max_steps=60), engine).results[0]
    assert len(result.replay.actions) == result.steps
    with result.replay.play(engine) as duel:
        assert duel.terminated == result.terminated
        assert capture(duel)["engine_rewards"] == list(result.returns) or result.truncated


def test_agents_must_describe_themselves(engine):
    class Anonymous:
        def reset(self, *, player, seed):
            pass

        def act(self, decision):
            return 0

        def end(self, episode):
            pass

    game = DuelGame((Competitor("a", Anonymous, VANILLA), Competitor("b", RandomAgent, VANILLA)), 0)
    with pytest.raises(TypeError, match="describe"):
        evaluate([game], engine)


def test_failed_runs_are_marked_incomplete(engine, tmp_path):
    def broken():
        raise RuntimeError("factory failed")

    game = DuelGame((Competitor("a", broken, VANILLA), Competitor("b", RandomAgent, VANILLA)), 0)
    with pytest.raises(RuntimeError, match="factory failed"):
        evaluate([game], engine, path=tmp_path / "run")
    loaded = Report.load(tmp_path / "run")
    assert not loaded.manifest["complete"] and loaded.results == ()
    with pytest.raises(FileExistsError):
        evaluate([game], engine, path=tmp_path / "run")
