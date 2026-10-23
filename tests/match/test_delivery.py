from ygo_gym import UNKNOWN_CARD, Player
from ygo_gym.event import SetEvent
from ygo_gym.match import play
from ygo_gym.state import Location

from .support import CollectingAgent, quiet_setup


def test_both_seats_receive_every_update_once_and_only_their_own_information(engine):
    agents = CollectingAgent(), CollectingAgent()
    with engine.create_duel(setup=quiet_setup(), seed=2) as duel:
        result = play(duel, agents=agents, max_steps=10, seed=3)
        assert result.truncated and not result.terminated
        assert result.outcome is None
        assert not duel.closed and not duel.terminated
        assert sum(result.player_steps) == result.step_count == 10
        for seat, agent in enumerate(agents):
            updates = agent.updates()
            assert len(updates) == result.step_count + 1
            assert len({id(update) for update in updates}) == len(updates)
            assert agent.final.result is result
            assert int(agent.final.player) == seat
            from ygo_gym.dataset.codec.actions import action as encode_action

            assert [
                [encode_action(action) for action in decision.actions]
                for decision in agent.decisions
            ] == agent.action_values
            for decision in agent.decisions:
                assert decision.observation is decision.updates[-1]
                assert int(decision.observation.viewer) == seat
                assert decision.actions
                for action in decision.actions:
                    card = getattr(action, "card", None)
                    if card is not None:
                        assert 0 <= card < len(decision.observation.cards)
            for update in updates:
                for card in update.cards:
                    if int(card.controller) != seat and card.location in (
                        Location.HAND,
                        Location.MONSTER_ZONE,
                    ):
                        assert card.code == UNKNOWN_CARD
                for card in update.events.cards:
                    if card.current_card is not None:
                        assert 0 <= card.current_card < len(update.cards)
            own_sets, hidden_sets = 0, 0
            for update in updates:
                for event in update.events:
                    if isinstance(event, SetEvent):
                        code = update.events.cards[event.card].code
                        own_sets += code != UNKNOWN_CARD
                        hidden_sets += code == UNKNOWN_CARD
            assert own_sets == hidden_sets == 1
        assert agents[0].resets[0][0] == Player.PLAYER_0
        assert agents[1].resets[0][0] == Player.PLAYER_1
        assert agents[0].resets[0][1] != agents[1].resets[0][1]
        assert any(
            len(decision.updates) > 1
            for agent in agents
            for decision in agent.decisions
        )


def test_terminal_updates_reach_a_player_that_never_acted(engine):
    from ygo_gym import ActionKind, Puzzle

    def end_turn(decision):
        return next(
            i
            for kind in (ActionKind.END_PHASE, ActionKind.PASS)
            for i, action in enumerate(decision.actions)
            if action.kind == kind
        )

    agents = CollectingAgent(end_turn), CollectingAgent()
    with Puzzle.builtin("Duel Links/Naim_DuelLinks_1_10.lua").start(
        engine, seed=4
    ) as episode:
        result = play(episode, agents=agents)
        assert result.terminated and not result.truncated
        assert result.returns == (-1.0, 1.0)
        assert not agents[1].decisions
        assert agents[0].final.reward == -1.0
        assert agents[1].final.reward == 1.0
        assert len(agents[1].final.updates) == result.step_count + 1
        for agent in agents:
            assert len(agent.updates()) == result.step_count + 1


def test_compound_selection_delivers_empty_events_and_local_pending_state(engine, deck):
    from ygo_gym import ActionKind, Deck

    def select(decision):
        count = len(decision.observation.pending_actions)
        kinds = (ActionKind.CONFIRM,) if count >= 2 else (ActionKind.SELECT_CARD,)
        kinds += (
            ActionKind.ACTIVATE,
            ActionKind.SELECT_ZONE,
            ActionKind.PASS,
            ActionKind.YES,
        )
        return next(
            (
                i
                for kind in kinds
                for i, a in enumerate(decision.actions)
                if a.kind == kind
            ),
            0,
        )

    agents = CollectingAgent(select), CollectingAgent()
    with engine.create_duel(Deck(main=(100000001,) * 40), deck, seed=123) as duel:
        result = play(duel, agents=agents, max_steps=14)
        selections = [d for d in agents[0].decisions if d.observation.pending_actions]
        assert selections
        assert any(len(d.observation.events) == 0 for d in selections)
        assert all(not update.pending_actions for update in agents[1].updates())
        assert all(len(a.updates()) == result.step_count + 1 for a in agents)


def test_transient_reveal_remains_available_after_card_disappears_into_deck(engine):
    from pathlib import Path

    from ygo_gym import Puzzle
    from ygo_gym.event import RevealEvent

    agents = CollectingAgent(), CollectingAgent()
    script = Path(__file__).parent / "scripts/reveal_and_hide.lua"
    with Puzzle.from_lua(script).start(engine, seed=10) as episode:
        play(episode, agents=agents, max_steps=1)
    for agent in agents:
        initial = agent.updates()[0]
        reveals = [event for event in initial.events if isinstance(event, RevealEvent)]
        assert len(reveals) == 1
        card = initial.events.cards[reveals[0].card]
        assert card.code == 69247929
        assert card.current_card is None
        assert not initial.cards
