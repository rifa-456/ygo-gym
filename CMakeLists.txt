cmake_minimum_required(VERSION 3.20)
project(ygo_gym_native LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

set(OCGCORE_DIR "${CMAKE_CURRENT_LIST_DIR}/third_party/ygopro-core")
set(LUA_DIR "${OCGCORE_DIR}/lua")

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

set(OCGCORE_SOURCES
    "${OCGCORE_DIR}/card.cpp"
    "${OCGCORE_DIR}/duel.cpp"
    "${OCGCORE_DIR}/effect.cpp"
    "${OCGCORE_DIR}/field.cpp"
    "${OCGCORE_DIR}/interpreter.cpp"
    "${OCGCORE_DIR}/libcard.cpp"
    "${OCGCORE_DIR}/libdebug.cpp"
    "${OCGCORE_DIR}/libduel.cpp"
    "${OCGCORE_DIR}/libeffect.cpp"
    "${OCGCORE_DIR}/libgroup.cpp"
    "${OCGCORE_DIR}/ocgapi.cpp"
    "${OCGCORE_DIR}/operations.cpp"
    "${OCGCORE_DIR}/playerop.cpp"
    "${OCGCORE_DIR}/processor.cpp"
    "${OCGCORE_DIR}/processor_visit.cpp"
    "${OCGCORE_DIR}/scriptlib.cpp"
)

add_library(ocgcore STATIC ${OCGCORE_SOURCES})
set_target_properties(ocgcore PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(ocgcore PUBLIC "${OCGCORE_DIR}" "${LUA_DIR}/src")
target_link_libraries(ocgcore PUBLIC ocg_lua)
target_compile_definitions(ocgcore PRIVATE NOMINMAX)

if(MSVC)
    target_compile_options(ocgcore PRIVATE /GR-)
else()
    target_compile_options(ocgcore PRIVATE -fno-rtti)
endif()

if(APPLE)
    target_compile_definitions(ocgcore PRIVATE _LIBCPP_NO_EXCEPTIONS)
    set_source_files_properties("${OCGCORE_DIR}/processor_visit.cpp" PROPERTIES COMPILE_OPTIONS "-fno-exceptions")
endif()

pybind11_add_module(_native MODULE
    engine/binding.cpp
    engine/action/action.cpp
    engine/action/announcement.cpp
    engine/action/binding.cpp
    engine/action/candidates.cpp
    engine/action/legality.cpp
    engine/action/response.cpp
    engine/action/state.cpp
    engine/action/sum.cpp
    engine/duel.cpp
    engine/engine.cpp
    engine/protocol/binding.cpp
    engine/protocol/decision.cpp
    engine/protocol/decoder.cpp
)
target_include_directories(_native PRIVATE engine engine/action engine/protocol)
target_link_libraries(_native PRIVATE ocgcore)

if(MSVC)
    target_compile_options(_native PRIVATE /W4)
else()
    target_compile_options(_native PRIVATE -Wall -Wextra -Wpedantic)
endif()

install(TARGETS _native LIBRARY DESTINATION ygo_gym RUNTIME DESTINATION ygo_gym)
