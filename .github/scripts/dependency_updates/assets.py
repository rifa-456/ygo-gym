from pathlib import Path

from git import Repository

URLS = {
    "third_party/WindBot": "https://github.com/ProjectIgnis/windbot.git",
    "third_party/Puzzles": "https://github.com/ProjectIgnis/Puzzles.git",
    "third_party/CardScripts": "https://github.com/ProjectIgnis/CardScripts.git",
    "third_party/BabelCDB": "https://github.com/ProjectIgnis/BabelCDB.git",
}


def prepare(root: Path, gym: Repository, urls: dict[str, str]) -> list[dict]:
    if set(urls) != set(URLS):
        raise RuntimeError("Expected the configured asset repositories")
    candidates = []
    for path, url in urls.items():
        gym.command("submodule", "update", "--init", "--depth", "1", "--", path)
        base = gym.command("rev-parse", f"HEAD:{path}")
        repository = Repository(root / path)
        repository.command("fetch", "--depth", "1", "--no-tags", "--no-recurse-submodules", url, "HEAD")
        head = repository.command("rev-parse", "FETCH_HEAD")
        repository.command("checkout", "--detach", head)
        candidates.append({"path": path, "url": url, "base": base, "head": head})
    return candidates


def verify_pins(gym: Repository, candidates: list[dict]) -> None:
    if len(candidates) != len(URLS) or {row["path"] for row in candidates} != set(URLS):
        raise RuntimeError("Candidate must include every asset pin")
    for row in candidates:
        if gym.command("rev-parse", f"HEAD:{row['path']}") != row["head"]:
            raise RuntimeError(f"Candidate asset pin mismatch: {row['path']}")
