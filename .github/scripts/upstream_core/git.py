import os
import subprocess
from pathlib import Path


class Repository:
    def __init__(self, path: Path):
        self.path = path.resolve()

    def command(self, *args: str, env: dict[str, str] | None = None) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), *args], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        if result.returncode:
            detail = (result.stderr + "\n" + result.stdout).strip()
            raise RuntimeError(f"git {' '.join(args[:2])}: {detail}")
        return result.stdout.strip()

    def ancestor(self, older: str, newer: str) -> bool:
        result = subprocess.run(
            ["git", "-C", str(self.path), "merge-base", "--is-ancestor", older, newer],
            capture_output=True, text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.strip())
        return result.returncode == 0

    def head(self) -> str:
        return self.command("rev-parse", "HEAD")

    def identity(self) -> None:
        self.command("config", "user.name", "github-actions[bot]")
        self.command("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")

    def fetch(self, url: str, branch: str) -> str:
        self.command("fetch", "--no-tags", url, branch)
        return self.command("rev-parse", "FETCH_HEAD")

    def lua(self, ref: str) -> tuple[str, str]:
        entry = self.command("ls-tree", ref, "--", "lua/src").split()
        if len(entry) != 4 or entry[:2] != ["160000", "commit"]:
            raise RuntimeError("Lua submodule layout changed; manual review required")
        url = self.command("config", "--blob", f"{ref}:.gitmodules", "--get", "submodule.lua/src.url")
        return entry[2], url

    def import_bundle(self, bundle: Path, expected: str) -> None:
        found = self.fetch(str(bundle.resolve()), "HEAD")
        if found != expected:
            raise RuntimeError("Candidate bundle does not match its recorded commit")
        self.command("checkout", "--detach", expected)


def authentication(token: str) -> dict[str, str]:
    import base64

    if not token:
        raise RuntimeError("Set the UPSTREAM_UPDATE_TOKEN repository secret before publishing")
    encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    # Keep credentials out of arguments, remotes, files, and test jobs.
    return {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
        "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {encoded}",
    }
