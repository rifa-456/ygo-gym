#include <filesystem>
#include <iostream>
#include <memory>
#include "lua.h"
#include "lauxlib.h"

int main(int argc, char** argv) {
    if(argc != 2 || !std::filesystem::is_directory(argv[1])) {
        std::cerr << "Expected a Lua script directory\n";
        return 1;
    }
    std::unique_ptr<lua_State, decltype(&lua_close)> state(luaL_newstate(), lua_close);
    if(!state)
        return 1;
    size_t checked = 0;
    for(const auto& entry : std::filesystem::recursive_directory_iterator(argv[1])) {
        if(!entry.is_regular_file() || entry.path().extension() != ".lua")
            continue;
        if(luaL_loadfilex(state.get(), entry.path().string().c_str(), "t") != LUA_OK) {
            std::cerr << entry.path() << ": " << lua_tostring(state.get(), -1) << '\n';
            return 1;
        }
        lua_settop(state.get(), 0);
        ++checked;
    }
    std::cout << "Compiled " << checked << " Lua scripts\n";
    return checked ? 0 : 1;
}
