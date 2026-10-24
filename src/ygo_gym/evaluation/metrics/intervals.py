import math
from statistics import NormalDist


def check_confidence(confidence: float) -> None:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")


def wilson(successes: float, trials: int, confidence: float) -> tuple[float, float]:
    """Wilson score interval; draws may contribute half successes."""
    if trials == 0:
        return 0.0, 1.0
    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    rate = successes / trials
    centre = rate + z * z / (2 * trials)
    margin = z * math.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials * trials))
    scale = 1 + z * z / trials
    return max(0.0, (centre - margin) / scale), min(1.0, (centre + margin) / scale)


def percentile_interval(values: list[float], confidence: float) -> tuple[float, float]:
    ordered = sorted(values)
    tail = (1 - confidence) / 2
    low = ordered[max(0, math.floor(tail * (len(ordered) - 1)))]
    high = ordered[min(len(ordered) - 1, math.ceil((1 - tail) * (len(ordered) - 1)))]
    return low, high
