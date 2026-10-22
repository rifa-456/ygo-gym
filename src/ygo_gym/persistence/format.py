import hashlib
import json
import struct
import zlib
from dataclasses import dataclass

MAGIC = b"YGOSNAP\x01"
MAX_PAYLOAD = 512 * 1024 * 1024
MAX_HEADER = 64 * 1024


class SnapshotError(ValueError):
    """The snapshot is damaged or uses an unsupported encoding."""


@dataclass(frozen=True, slots=True)
class SnapshotInfo:
    version: int
    compatibility: dict
    payload_bytes: int
    stored_bytes: int
    metadata: dict | None = None


def pack(payload: bytes, compatibility: dict, metadata: dict | None = None) -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise SnapshotError("snapshot exceeds size limit")
    stored = zlib.compress(payload, level=3)
    header = json.dumps(
        {"version": 1, "compatibility": compatibility, "payload_bytes": len(payload), "metadata": metadata},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode()
    if len(header) > MAX_HEADER:
        raise SnapshotError("snapshot metadata exceeds header limit")
    body = MAGIC + struct.pack("<I", len(header)) + header + stored
    return body + hashlib.sha256(body).digest()


def unpack(data: bytes) -> tuple[SnapshotInfo, bytes]:
    if not isinstance(data, bytes):
        raise TypeError("snapshot must be bytes")
    if len(data) < len(MAGIC) + 4 + 32 or len(data) > MAX_PAYLOAD + MAX_HEADER:
        raise SnapshotError("invalid snapshot length")
    if not data.startswith(MAGIC):
        raise SnapshotError("unsupported snapshot format")
    body, checksum = data[:-32], data[-32:]
    if hashlib.sha256(body).digest() != checksum:
        raise SnapshotError("snapshot checksum mismatch")
    size = struct.unpack_from("<I", body, len(MAGIC))[0]
    start = len(MAGIC) + 4
    if size > MAX_HEADER or start + size > len(body):
        raise SnapshotError("invalid snapshot header length")
    try:
        header = json.loads(body[start:start + size])
        if header["version"] != 1 or not isinstance(header["compatibility"], dict):
            raise SnapshotError("unsupported snapshot header")
        expected = header["payload_bytes"]
        if type(expected) is not int or not 0 <= expected <= MAX_PAYLOAD:
            raise SnapshotError("invalid snapshot payload length")
        decoder = zlib.decompressobj()
        payload = decoder.decompress(body[start + size:], expected + 1)
        if len(payload) != expected or not decoder.eof or decoder.unused_data:
            raise SnapshotError("invalid snapshot compressed payload")
    except (KeyError, TypeError, ValueError, zlib.error, UnicodeError) as error:
        if isinstance(error, SnapshotError):
            raise
        raise SnapshotError("invalid snapshot encoding") from error
    return SnapshotInfo(1, header["compatibility"], len(payload), len(data), header.get("metadata")), payload


def inspect_snapshot(data: bytes) -> SnapshotInfo:
    return unpack(data)[0]
