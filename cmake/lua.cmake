set(LUA_SOURCES
    "${LUA_DIR}/src/lapi.c"
    "${LUA_DIR}/src/lauxlib.c"
    "${LUA_DIR}/src/lbaselib.c"
    "${LUA_DIR}/src/lcode.c"
    "${LUA_DIR}/src/lctype.c"
    "${LUA_DIR}/src/ldebug.c"
    "${LUA_DIR}/src/ldo.c"
    "${LUA_DIR}/src/ldump.c"
    "${LUA_DIR}/src/lfunc.c"
    "${LUA_DIR}/src/lgc.c"
    "${LUA_DIR}/src/liolib.c"
    "${LUA_DIR}/src/llex.c"
    "${LUA_DIR}/src/lmathlib.c"
    "${LUA_DIR}/src/lmem.c"
    "${LUA_DIR}/src/lobject.c"
    "${LUA_DIR}/src/lopcodes.c"
    "${LUA_DIR}/src/lparser.c"
    "${LUA_DIR}/src/lstate.c"
    "${LUA_DIR}/src/lstring.c"
    "${LUA_DIR}/src/lstrlib.c"
    "${LUA_DIR}/src/ltable.c"
    "${LUA_DIR}/src/ltablib.c"
    "${LUA_DIR}/src/ltm.c"
    "${LUA_DIR}/src/lundump.c"
    "${LUA_DIR}/src/lvm.c"
    "${LUA_DIR}/src/lzio.c"
)

set_source_files_properties(${LUA_SOURCES} PROPERTIES LANGUAGE CXX)
add_library(ocg_lua STATIC ${LUA_SOURCES})
set_target_properties(ocg_lua PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(ocg_lua PUBLIC "${LUA_DIR}/src")

if(MSVC)
    target_compile_options(ocg_lua PRIVATE "/FI${LUA_DIR}/luaconf-customize.h")
else()
    target_compile_options(ocg_lua PRIVATE "-include${LUA_DIR}/luaconf-customize.h")
endif()
