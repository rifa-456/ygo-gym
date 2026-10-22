from ..schema.events import EVENT_FIELDS, EVENT_VARIANTS
from ..schema.types import integers
from .values import fields, scalar


def event(value) -> dict:
    name = type(value).__name__
    if name not in EVENT_VARIANTS:
        raise TypeError(f"unsupported semantic event: {name}")
    result = dict.fromkeys(EVENT_FIELDS)
    result["variant"] = name
    for field in EVENT_VARIANTS[name]:
        item = getattr(value, field)
        if field in ("previous", "current"):
            item = fields(item, integers("controller", "location", "sequence", "position"))
        elif field in ("kind", "stage"):
            item = item.name
        elif field == "results":
            item = list(item)
        else:
            item = scalar(item)
        result[field] = item
    return result


def batch(value) -> dict:
    return {
        "cards": [fields(c, integers("id", "code", "current_card")) for c in value.cards],
        "events": [event(e) for e in value],
    }
