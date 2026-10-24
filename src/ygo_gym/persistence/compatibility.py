import platform
import struct
import sys
from dataclasses import dataclass

from .format import SnapshotError, inspect_snapshot


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    compatible: bool
    differences: tuple[str, ...]


class SnapshotCompatibilityError(SnapshotError):
    def __init__(self, report: CompatibilityReport):
        self.report = report
        super().__init__("incompatible engine snapshot: " + ", ".join(report.differences))


def fingerprint(engine, provenance=None) -> dict:
    if provenance is None:
        from ..provenance import Provenance

        provenance = Provenance.capture(engine)
    values = provenance.as_record()
    return {
        "native_sha256": values["native_sha256"],
        "database_sha256": values["database_sha256"],
        "scripts_sha256": values["scripts_sha256"],
        "platform": sys.platform,
        "machine": platform.machine(),
        "byteorder": sys.byteorder,
        "pointer_bytes": struct.calcsize("P"),
    }


def check_snapshot(engine, data: bytes, *, provenance=None) -> CompatibilityReport:
    saved = inspect_snapshot(data).compatibility
    current = fingerprint(engine, provenance)
    differences = tuple(sorted(key for key in saved.keys() | current.keys() if saved.get(key) != current.get(key)))
    return CompatibilityReport(not differences, differences)
