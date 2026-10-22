from importlib.resources import files
from pathlib import Path, PurePosixPath


def collection():
    packaged = files("ygo_gym").joinpath("assets", "puzzles")
    if packaged.joinpath("COPYING").is_file():
        return packaged
    checkout = Path(__file__).resolve().parents[3] / "third_party" / "Puzzles"
    if checkout.joinpath("COPYING").is_file():
        return checkout
    raise FileNotFoundError(
        "puzzle assets are missing; initialize third_party/Puzzles or reinstall ygo-gym"
    )


def builtin_path(name: str):
    path = PurePosixPath(name)
    if (
        not name
        or "\\" in name
        or ":" in name
        or path.is_absolute()
        or any(part in (".", "..") for part in path.parts)
    ):
        raise ValueError("puzzle name must be a relative collection path")
    target = collection().joinpath(*path.parts)
    if path.suffix.lower() != ".lua" or not target.is_file():
        raise FileNotFoundError(f"puzzle does not exist: {name}")
    return target


def list_builtin() -> tuple[str, ...]:
    def walk(root, prefix=""):
        for path in root.iterdir():
            name = prefix + path.name
            if path.is_dir() and not path.name.startswith("."):
                yield from walk(path, name + "/")
            elif (
                path.is_file()
                and path.name.endswith(".lua")
                and name != "Puzzle Creator.lua"
            ):
                yield name

    return tuple(sorted(walk(collection())))
