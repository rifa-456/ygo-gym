from pathlib import Path

from candidate import CORE_PATH, CORE_URL, GYM_URL, checkout
from git import Repository, authentication
from lua import LUA_URL


def publish(root: Path, output: Path, token: str,
            core_url: str = CORE_URL, gym_url: str = GYM_URL, lua_url: str = LUA_URL) -> None:
    env = authentication(token)
    manifest = checkout(root, output)
    gym, core = Repository(root), Repository(root / CORE_PATH)
    if not core.ancestor(manifest["core_base"], core.head()):
        raise RuntimeError("Candidate core does not descend from the fork")
    if gym.command("rev-parse", "HEAD^") != manifest["gym_base"]:
        raise RuntimeError("Unexpected candidate YGO Gym parent")
    if gym.command("diff", "--name-only", "HEAD^", "HEAD") != CORE_PATH:
        raise RuntimeError("Candidate YGO Gym changes more than the core pin")
    if list(core.lua("HEAD")) != manifest["lua"]:
        raise RuntimeError("Candidate core does not pin the prepared Lua dependency")
    if gym.fetch(gym_url, "main") != manifest["gym_base"]:
        raise RuntimeError("YGO Gym advanced during testing; rerun the workflow")
    current_core = core.fetch(core_url, "master")
    if current_core not in (manifest["core_base"], manifest["core_head"]):
        raise RuntimeError("Core fork advanced during testing; rerun the workflow")
    if update := manifest["lua_update"]:
        lua = Repository(core.path / "lua/src")
        if update["url"] != lua_url or not lua.ancestor(update["base"], update["head"]):
            raise RuntimeError("Invalid candidate Lua fork")
        current_lua = lua.fetch(lua_url, "master")
        if current_lua not in (update["base"], update["head"]):
            raise RuntimeError("Lua fork advanced during testing; rerun the workflow")
        if current_lua != update["head"]:
            lua.command("push", lua_url, "HEAD:refs/heads/master", env=env)
    if current_core != manifest["core_head"]:
        core.command("push", core_url, "HEAD:refs/heads/master", env=env)
    gym.command("push", gym_url, "HEAD:refs/heads/main", env=env)
    print(f"Published core {core.head()} and YGO Gym {gym.head()}")
