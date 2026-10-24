from contextlib import contextmanager

from ..competitor import Competitor
from ..seat import Seat


@contextmanager
def seated(competitors: tuple[Competitor, ...]):
    """Fresh sessions for one game, closed afterwards even when play fails."""
    seats = []
    try:
        for competitor in competitors:
            seats.append(Seat(competitor))
        yield tuple(seats)
    finally:
        for seat in seats:
            seat.close()


def winner_name(seats, winner) -> str | None:
    return None if winner is None else seats[int(winner)].competitor.name
