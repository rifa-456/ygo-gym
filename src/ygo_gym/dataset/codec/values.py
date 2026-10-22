def scalar(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return int(value)


def fields(value, specification):
    if value is None:
        return None
    result = {}
    for name, kind in specification.items():
        item = getattr(value, name)
        if kind.endswith("[]"):
            result[name] = [scalar(x) for x in item]
        elif kind == "VARCHAR":
            result[name] = None if item is None else item.name
        else:
            result[name] = scalar(item)
    return result
