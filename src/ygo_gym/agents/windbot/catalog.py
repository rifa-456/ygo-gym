from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ...deck import Deck
from .runtime import Worker, build, checkout


@dataclass(frozen=True, slots=True)
class WindBotDeck:
    id: str
    name: str
    file: Path
    level: str
    difficulty: int | None
    master_rules: tuple[int, ...]

    @property
    def available(self) -> bool:
        return self.file.is_file()

    def load(self) -> Deck:
        zones = {"main": [], "extra": [], "side": []}
        zone = "main"
        for line in self.file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line == "#main":
                zone = "main"
            elif line == "#extra":
                zone = "extra"
            elif line == "!side":
                zone = "side"
            elif line and not line.startswith(("#", "!")):
                zones[zone].append(int(line))
        return Deck(**zones)


def available_decks(
    root: str | Path | None = None, *, dotnet: str = "dotnet"
) -> tuple[WindBotDeck, ...]:
    root = checkout(root)
    worker = Worker(build(root, dotnet=dotnet), dotnet=dotnet)
    try:
        entries = worker.request(op="catalog")
    finally:
        worker.close()
    metadata = {
        row["deck"]: row
        for row in json.loads(
            (root / "third_party/WindBot/bots.json").read_text(encoding="utf-8-sig")
        )
    }
    results = []
    for row in entries:
        details = metadata.get(row["id"], {})
        results.append(
            WindBotDeck(
                row["id"],
                details.get("name", row["id"]),
                root / "third_party/WindBot/Decks" / f"{row['file']}.ydk",
                row["level"],
                details.get("difficulty"),
                tuple(details.get("masterRules", ())),
            )
        )
    return tuple(results)
