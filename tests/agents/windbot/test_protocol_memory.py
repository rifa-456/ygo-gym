from types import SimpleNamespace

import pytest
from ygo_gym.agents.windbot.agent import WindBotAgent
from ygo_gym.agents.windbot.runtime import WindBotError


class Worker:
    def __init__(self):
        self.calls = []

    def request(self, **request):
        self.calls.append(request)
        return {"responses": [], "closed": False, "surrendered": False}


def session():
    bot = object.__new__(WindBotAgent)
    bot._player = 0
    bot._session = None
    bot._last_batch = -1
    bot.worker = Worker()
    return bot


def observation(index, *, initial=False, session_id=42):
    return SimpleNamespace(
        viewer=0, _client_batch=(session_id, index, initial, [b"\x01\x28\x00"])
    )


def test_duplicate_compound_updates_are_delivered_once():
    bot = session()
    initial = observation(0, initial=True)
    bot._feed((initial, initial))
    bot._feed((initial, observation(1)))
    assert len(bot.worker.calls) == 2
    assert all(len(call["packets"]) == 1 for call in bot.worker.calls)


def test_missing_history_is_an_error():
    bot = session()
    with pytest.raises(WindBotError, match="initial observation"):
        bot._feed((observation(4),))
    bot._feed((observation(0, initial=True),))
    with pytest.raises(WindBotError, match="missed client updates"):
        bot._feed((observation(2),))


def test_rewound_or_other_duel_is_an_error():
    bot = session()
    bot._feed((observation(0, initial=True), observation(1)))
    with pytest.raises(WindBotError, match="rewound"):
        bot._feed((observation(0, initial=True),))
    with pytest.raises(WindBotError, match="different"):
        bot._feed((observation(0, initial=True, session_id=99),))
