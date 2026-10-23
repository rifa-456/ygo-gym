from pathlib import Path


def read_banlist(path, name=None):
    """Read one EDOPro lflist.conf section, including whitelist sections."""
    sections = []
    current = None
    for raw in Path(path).read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            current = (line[1:].strip(), {}, [False])
            sections.append(current)
        elif line == "$whitelist":
            if current is None:
                raise ValueError("whitelist directive outside a banlist section")
            current[2][0] = True
        elif current is not None:
            parts = line.split()
            if len(parts) < 2:
                raise ValueError(f"invalid banlist entry: {line}")
            code, limit = int(parts[0]), int(parts[1])
            if code <= 0 or limit < 0:
                raise ValueError("invalid banlist card ID or limit")
            current[1][code] = limit
    if name is None and len(sections) != 1:
        raise ValueError("select a banlist by name when the file has multiple sections")
    selected = [section for section in sections if name is None or section[0] == name]
    if len(selected) != 1:
        raise ValueError("banlist name is missing or ambiguous")
    _, limits, whitelist = selected[0]
    return limits, frozenset(limits) if whitelist[0] else None
