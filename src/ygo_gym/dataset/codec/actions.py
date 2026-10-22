from ..schema.actions import ACTION_FIELDS, ACTION_VARIANTS
from ..schema.types import integers
from .values import fields, scalar


def action(value) -> dict:
    name = type(value).__name__
    if name not in ACTION_VARIANTS:
        raise TypeError(f"unsupported semantic action: {name}")
    result = dict.fromkeys(ACTION_FIELDS)
    result.update(variant=name, kind=value.kind.name)
    for field in ACTION_VARIANTS[name]:
        item = getattr(value, field)
        if field == "zone":
            item = fields(item, integers("player", "location", "sequence"))
        elif field == "choice":
            item = item.name
        else:
            item = scalar(item)
        result[field] = item
    return result
