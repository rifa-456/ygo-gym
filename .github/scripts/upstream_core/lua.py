from git import Repository

LUA_URL = "https://github.com/rifa-456/ygo-lua.git"


def prepare(core: Repository, base: str, upstream: str, url: str) -> dict | None:
    if core.ancestor(upstream, base):
        return None
    bases = core.command("merge-base", "--all", base, upstream).splitlines()
    if len(bases) != 1:
        raise RuntimeError("Cannot determine the upstream Lua dependency baseline")
    previous, incoming = core.lua(bases[0]), core.lua(upstream)
    if previous == incoming:
        return None
    core.command("submodule", "sync", "--", "lua/src")
    core.command("submodule", "update", "--init", "--", "lua/src")
    lua = Repository(core.path / "lua/src")
    if lua.command("rev-parse", "--is-shallow-repository") == "true":
        lua.command("fetch", "--unshallow", "--no-recurse-submodules", url, "master")
    lua_base = lua.fetch(url, "master")
    if not lua.ancestor(core.lua(base)[0], lua_base):
        raise RuntimeError("Lua fork does not descend from the core's current pin")
    lua.command("checkout", "--detach", lua_base)
    revision = lua.fetch(incoming[1], incoming[0])
    if not lua.ancestor(revision, lua_base):
        lua.identity()
        lua.command("merge", "--no-ff", "--no-edit", revision)
    return {"base": lua_base, "head": lua.head(), "upstream": revision, "url": url}


def adapt_upstream(core: Repository, upstream: str, update: dict) -> str:
    core.command("checkout", "--detach", upstream)
    core.command("config", "-f", ".gitmodules", "submodule.lua/src.url", update["url"])
    core.command("add", "--", ".gitmodules")
    core.command("update-index", "--add", "--cacheinfo", f"160000,{update['head']},lua/src")
    if core.command("diff", "--cached", "--name-only"):
        core.command("commit", "-m", "build(lua): retain merged clone-enabled Lua fork")
    return core.head()
