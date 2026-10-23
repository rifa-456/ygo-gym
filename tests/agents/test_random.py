from tests.episode.support import quiet_setup
from ygo_gym.agents import RandomAgent
from ygo_gym.episode import play


class TracedRandom(RandomAgent):
    def reset(self, *, player, seed):
        super().reset(player=player, seed=seed)
        self.choices = []

    def act(self, decision):
        result = super().act(decision)
        assert 0 <= result < len(decision.actions)
        self.choices.append(result)
        return result


def test_random_self_play_is_repeatable_without_global_rng_changes(engine):
    import random

    before = random.getstate()
    agents = TracedRandom(), TracedRandom()
    runs = []
    for _ in range(2):
        with engine.create_duel(setup=quiet_setup(), seed=12) as duel:
            result = play(duel, agents=agents, max_steps=15, seed=55)
            runs.append((result, [tuple(agent.choices) for agent in agents]))
    assert runs[0] == runs[1]
    assert random.getstate() == before
