from dataclasses import dataclass

from .codec import capture
from .initialization import Provenance, create_duel


@dataclass(frozen=True, slots=True)
class ReplayReport:
    game_id: str
    compatible: bool
    checked_steps: int
    provenance_matches: bool
    path: str | None = None
    expected: object = None
    actual: object = None
    error: str | None = None


def difference(expected, actual, path: str):
    if type(expected) is not type(actual):
        return path, expected, actual
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return path + ".keys", sorted(expected), sorted(actual)
        for key in expected:
            if found := difference(expected[key], actual[key], path + "." + key):
                return found
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return path + ".length", len(expected), len(actual)
        for index, (left, right) in enumerate(zip(expected, actual, strict=True)):
            if found := difference(left, right, f"{path}[{index}]"):
                return found
    elif expected != actual:
        return path, expected, actual
    return None


def validate_replay(dataset, engine, game_id: str, *, provenance: Provenance | None = None) -> ReplayReport:
    """Validate this recorded path, not equivalence of every possible future branch."""
    game = dataset.game(game_id)
    current = provenance or Provenance.capture(engine)
    matches = game["provenance"] == current.as_record()
    count = 0
    path = "initial"

    def failure(found):
        return ReplayReport(game_id, False, count, matches, *found)

    try:
        with create_duel(engine, game["setup"]) as duel:
            frame = capture(duel)
            if found := difference(game["initial"], frame, path):
                return failure(found)
            for row in dataset.steps(game_id):
                path = f"steps[{count}]"
                if row["step_index"] != count:
                    return failure((path + ".step_index", count, row["step_index"]))
                if found := difference(row["before"], frame, path + ".before"):
                    return failure(found)
                if row["acting_player"] != frame["current_player"]:
                    return failure((path + ".acting_player", frame["current_player"], row["acting_player"]))
                index = row["action_index"]
                if not 0 <= index < len(frame["actions"]):
                    return failure((path + ".action_index", "valid legal-action index", index))
                if found := difference(row["action"], frame["actions"][index], path + ".action"):
                    return failure(found)
                duel.step(index)
                frame = capture(duel)
                if found := difference(row["after"], frame, path + ".after"):
                    return failure(found)
                count += 1
            if count != game["step_count"]:
                return failure(("game.step_count", game["step_count"], count))
            if found := difference(game["outcome"], frame["outcome"], "game.outcome"):
                return failure(found)
    except Exception as error:
        return ReplayReport(game_id, False, count, matches, path, error=f"{type(error).__name__}: {error}")
    return ReplayReport(game_id, True, count, matches)
