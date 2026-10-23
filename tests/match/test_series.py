import pytest

from ygo_gym import (
    ActionKind,
    Deck,
    DeckRules,
    DuelConfig,
    Match,
    MatchRules,
    play_match,
)
from ygo_gym.agents import RandomAgent
from ygo_gym.match import DrawPolicy


class ScriptedAgent(RandomAgent):
    def __init__(self):
        super().__init__()
        self.episodes = []
        self.sides = []
        self.choices = []
        self.starts = []

    def reset(self, *, player, seed):
        super().reset(player=player, seed=seed)
        self.starts.append(int(player))

    def act(self, decision):
        for kind in (
            ActionKind.ACTIVATE,
            ActionKind.SUMMON,
            ActionKind.BATTLE_PHASE,
            ActionKind.ATTACK,
            ActionKind.SELECT_CARD,
            ActionKind.CONFIRM,
            ActionKind.YES,
            ActionKind.SELECT_ZONE,
            ActionKind.END_PHASE,
            ActionKind.PASS,
        ):
            for i, action in enumerate(decision.actions):
                if action.kind == kind:
                    return i
        return 0

    def end(self, episode):
        self.episodes.append(episode)

    def side_deck(self, decision):
        self.sides.append(decision)
        return decision.deck

    def choose_first(self, decision):
        self.choices.append(decision)
        return decision.player

    def match_end(self, result):
        self.final = result


def config(**changes):
    return MatchRules(
        decks=DeckRules.unrestricted(),
        first_player=0,
        duel=DuelConfig(opening_hand=(1, 1)),
        max_steps_per_duel=1000,
        **changes,
    )


def test_real_duels_side_decking_callbacks_and_reproducibility(engine):
    decks = (Deck((69247929,) * 8), Deck((69247929,) * 8))
    summaries = []
    for _ in range(2):
        agents = ScriptedAgent(), ScriptedAgent()
        with Match(engine, decks, rules=config(), seed=12) as match:
            result = play_match(match, agents=agents, seed=4)
            assert result.terminated and not result.truncated
            assert result.winner in (0, 1)
            assert len(result.duels) in (2, 3)
            assert len(agents[0].sides) == len(result.duels) - 1
            assert len(agents[1].sides) == len(result.duels) - 1
            assert agents[0].final == agents[1].final == result
            assert len(agents[0].episodes) == len(result.duels)
            summaries.append(result)
    assert summaries[0] == summaries[1]


def test_draw_policy_counts_draws_like_edopro(match_engine):
    decks = (Deck((100000003,) * 10), Deck((100000003,) * 10))
    with Match(match_engine, decks, rules=config(best_of=3), seed=0) as match:
        result = play_match(match, agents=(ScriptedAgent(), ScriptedAgent()))
        assert result.scores == (0, 0)
        assert result.draws == 3 and result.winner is None
        assert len(result.duels) == 3


def test_replay_draws_respects_explicit_duel_cap(match_engine):
    decks = (Deck((100000003,) * 10), Deck((100000003,) * 10))
    with Match(
        match_engine,
        decks,
        rules=config(
            best_of=1,
            draw_policy=DrawPolicy.REPLAY,
            max_duels=4,
        ),
    ) as match:
        result = play_match(match, agents=(ScriptedAgent(), ScriptedAgent()))
        assert result.draws == 4 and len(result.duels) == 4
        assert result.reason == "duel_limit"


def test_match_kill_ends_series_from_a_real_card_effect(match_engine):
    decks = (Deck((100000004,) * 10), Deck((69247929,) * 10))
    rules = MatchRules(
        first_player=0,
        decks=DeckRules.unrestricted(),
        duel=DuelConfig(
            flags=2 | int(DuelConfig().flags),
            life_points=(100, 100),
            opening_hand=(1, 0),
        ),
        max_steps_per_duel=100,
    )
    with Match(match_engine, decks, rules=rules) as match:
        result = play_match(match, agents=(ScriptedAgent(), ScriptedAgent()))
        assert result.reason == "match_kill"
        assert result.winner == 0 and len(result.duels) == 1
        assert result.duels[0].match_kill == 100000004


def test_budget_exhaustion_truncates_without_fabricating_a_draw(engine):
    decks = (Deck((69247929,) * 10), Deck((69247929,) * 10))
    rules = MatchRules(
        first_player=1, decks=DeckRules.unrestricted(), max_steps_per_duel=1
    )
    with Match(engine, decks, rules=rules) as match:
        result = play_match(match, agents=(ScriptedAgent(), ScriptedAgent()))
        assert result.truncated and not result.terminated
        assert result.winner is None and result.draws == 0
        assert result.duels[-1].episode.truncated
        assert not match.duel.terminated


def test_callback_errors_do_not_become_losses(engine):
    class Broken(ScriptedAgent):
        def act(self, decision):
            raise RuntimeError("broken policy")

    with Match(engine, (Deck((69247929,) * 10),) * 2, rules=config()) as match:
        with pytest.raises(RuntimeError, match="broken policy"):
            play_match(match, agents=(Broken(), ScriptedAgent()))
        assert not match.ended and match.scores == (0, 0)


def test_match_end_notifies_both_agents_when_one_callback_fails(engine):
    class BrokenEnd(ScriptedAgent):
        def match_end(self, result):
            raise ValueError("bad match callback")

    other = ScriptedAgent()
    with Match(
        engine,
        (Deck((69247929,) * 10),) * 2,
        rules=MatchRules(
            first_player=0, max_steps_per_duel=1, decks=DeckRules.unrestricted()
        ),
    ) as match:
        with pytest.raises(ExceptionGroup, match="match end callbacks"):
            play_match(match, agents=(BrokenEnd(), other))
        assert other.final == match.result


def test_natural_results_can_be_collected_through_low_level_match_steps(engine):
    from ygo_gym import MatchPhase

    decks = (Deck((69247929,) * 2), Deck((69247929,) * 10))
    with Match(engine, decks, rules=config(best_of=1), seed=3) as match:
        agents = ScriptedAgent(), ScriptedAgent()
        for _ in range(300):
            if match.ended:
                break
            player = match.current_player
            if player is None:
                match.complete_duel()
                continue
            from ygo_gym.agents import AgentInput

            observation = match.observe(player)
            action = agents[player].act(
                AgentInput(observation, match.actions, (observation,))
            )
            match.step(action)
        assert match.phase == MatchPhase.FINISHED
        assert match.result.scores in ((1, 0), (0, 1))
        assert match.duels[0].episode is None
