import sys

import psutil


def reader(metric: str):
    if metric == "rss":
        try:
            process = psutil.Process()
            process.memory_info()
        except (psutil.Error, OSError) as error:
            raise RuntimeError("Current RSS is unavailable; on Unix, explicitly select --metric peak-rss") from error
        return lambda: process.memory_info().rss
    if metric != "peak-rss":
        raise ValueError(f"unknown memory metric: {metric}")
    try:
        import resource
    except ImportError as error:
        raise RuntimeError("peak-rss requires Unix resource.getrusage; use --metric rss on Windows") from error
    scale = 1 if sys.platform == "darwin" else 1024
    return lambda: resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * scale
