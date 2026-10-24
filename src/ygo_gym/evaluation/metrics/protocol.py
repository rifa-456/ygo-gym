from collections.abc import Sequence
from typing import Protocol

import pyarrow as pa

from ..result import GameResult


class Metric(Protocol):
    name: str

    def compute(self, results: Sequence[GameResult]) -> pa.Table: ...
