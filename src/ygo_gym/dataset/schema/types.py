def struct(fields: dict[str, str]) -> str:
    return "STRUCT(" + ", ".join(f'"{name}" {kind}' for name, kind in fields.items()) + ")"


def integers(*names: str) -> dict[str, str]:
    return dict.fromkeys(names, "BIGINT")


ZONE = struct(integers("player", "location", "sequence"))
LOCATION = struct(integers("controller", "location", "sequence", "position"))
OUTCOME = struct({"winner": "BIGINT", "reason": "BIGINT", "rewards": "DOUBLE[]"})
RESULT = struct({"rewards": "DOUBLE[]", "terminated": "BOOLEAN", "truncated": "BOOLEAN", "reason": "VARCHAR"})
