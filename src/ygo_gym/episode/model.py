from dataclasses import dataclass

from ..engine import Outcome


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    """Returns and decision counts for this play() call, indexed by seat.

    An already-ended position reports its current terminal rewards.

    An external step limit truncates the episode without changing the underlying
    duel or task, so a dataset written from its replay is partial. Configure
    Task.max_steps when the limit should be recorded as episode semantics.
    """

    returns: tuple[float, float]
    step_count: int
    player_steps: tuple[int, int]
    terminated: bool
    truncated: bool
    reason: str | None
    outcome: Outcome | None
