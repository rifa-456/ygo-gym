from importlib.resources import files
from pathlib import Path


def source_checkout() -> Path | None:
    root = Path(__file__).resolve().parents[3]
    if (root / "pyproject.toml").is_file() and (root / "src/ygo_gym/engine.py").is_file():
        return root
    return None


def checkout_root(root: str | Path | None = None) -> Path:
    result = Path(root).resolve() if root is not None else source_checkout()
    if result is None:
        raise FileNotFoundError("supply root= to use a checkout from an installed package")
    return result


def directory(name: str, submodule: str) -> Path:
    checkout = source_checkout()
    if checkout is not None:
        return checkout / "third_party" / submodule
    return Path(str(files("ygo_gym").joinpath("assets", name)))


def engine_defaults() -> tuple[Path, tuple[Path, ...]]:
    database = directory("database", "BabelCDB") / "cards.cdb"
    scripts = directory("scripts", "CardScripts")
    return database, (scripts, scripts / "official")
