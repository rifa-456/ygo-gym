import math

import pytest
from ygo_gym.evaluation import BradleyTerry, Elo, SolveRate, WinRate
from ygo_gym.evaluation.metrics.intervals import wilson

from .support import attempt, duel


def test_wilson_matches_the_reference_interval():
    low, high = wilson(8, 10, 0.95)
    assert low == pytest.approx(0.4902, abs=1e-4)
    assert high == pytest.approx(0.9433, abs=1e-4)
    assert wilson(0, 0, 0.95) == (0.0, 1.0)


def test_solve_rate_counts_attempts_per_competitor():
    rows = SolveRate().compute([attempt("a", True), attempt("a", False), attempt("b", True)]).to_pylist()
    assert [(r["competitor"], r["attempts"], r["solved"], r["rate"]) for r in rows] == [
        ("a", 2, 1, 0.5), ("b", 1, 1, 1.0)
    ]


def test_win_rate_is_symmetric_and_draws_count_half():
    results = [duel("a", "b", "a"), duel("b", "a", "a"), duel("a", "b", None)]
    rows = {(r["competitor"], r["opponent"]): r for r in WinRate().compute(results).to_pylist()}
    assert (rows["a", "b"]["wins"], rows["a", "b"]["draws"], rows["a", "b"]["losses"]) == (2, 1, 0)
    assert rows["a", "b"]["rate"] == pytest.approx(2.5 / 3)
    assert rows["b", "a"]["rate"] == pytest.approx(0.5 / 3)


def test_win_rate_by_seat_separates_first_and_second_turns():
    results = [duel("a", "b", "a"), duel("b", "a", "b")]
    rows = {(r["competitor"], r["seat"]): r["rate"] for r in WinRate(by_seat=True).compute(results).to_pylist()}
    assert rows == {("a", 0): 1.0, ("a", 1): 0.0, ("b", 0): 1.0, ("b", 1): 0.0}
    with pytest.raises(ValueError):
        WinRate(unit="match", by_seat=True)


def test_match_unit_scores_each_match_once():
    results = [
        duel("a", "b", "a", index=0, kind="match", match_winner="a", duel=0),
        duel("b", "a", "b", index=0, kind="match", match_winner="a", duel=1),
        duel("a", "b", "a", index=0, kind="match", match_winner="a", duel=2),
    ]
    rows = {r["competitor"]: r for r in WinRate(unit="match").compute(results).to_pylist()}
    assert rows["a"]["played"] == 1 and rows["a"]["wins"] == 1


def test_bradley_terry_orders_by_strength_and_stays_finite_for_unbeaten():
    results = [duel("a", "b", "a")] * 8 + [duel("b", "c", "b")] * 8 + [duel("a", "c", "a")] * 8
    rows = BradleyTerry(resamples=50).compute(results).to_pylist()
    assert [r["competitor"] for r in rows] == ["a", "b", "c"]
    assert sum(r["rating"] for r in rows) == pytest.approx(0, abs=1e-6)
    for r in rows:
        assert r["low"] <= r["rating"] <= r["high"]


def test_bradley_terry_recovers_a_known_strength_ratio():
    results = [duel("a", "b", "a")] * 750 + [duel("a", "b", "b")] * 250
    rows = {r["competitor"]: r["rating"] for r in BradleyTerry(resamples=0, prior=1e-6).compute(results).to_pylist()}
    assert rows["a"] - rows["b"] == pytest.approx(400 * math.log10(3), abs=0.5)


def test_elo_follows_play_order():
    rows = {r["competitor"]: r["rating"] for r in Elo(resamples=0).compute([duel("a", "b", "a")]).to_pylist()}
    assert rows == {"a": 8.0, "b": -8.0}


def test_metrics_reject_invalid_options():
    for build in (lambda: SolveRate(confidence=1.5), lambda: BradleyTerry(unit="set"),
                  lambda: BradleyTerry(prior=0), lambda: Elo(resamples=-1)):
        with pytest.raises(ValueError):
            build()
