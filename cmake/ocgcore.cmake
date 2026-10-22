set(OCGCORE_DIR "${PROJECT_SOURCE_DIR}/third_party/ygopro-core")
set(LUA_DIR "${OCGCORE_DIR}/lua")

include("${CMAKE_CURRENT_LIST_DIR}/lua.cmake")
include("${OCGCORE_DIR}/clone/sources.cmake")

set(OCGCORE_SOURCES
    ${OCG_CLONE_SOURCES}
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
target_link_libraries(ocgcore PUBLIC ocg_lua ocg_clone_boost ${CMAKE_DL_LIBS})
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

if(MSVC)
    set_property(SOURCE "${OCGCORE_DIR}/clone/lua/region.cpp" "${OCGCORE_DIR}/clone/lua/heap.cpp" APPEND PROPERTY COMPILE_OPTIONS /GR)
else()
    set_property(SOURCE "${OCGCORE_DIR}/clone/lua/region.cpp" "${OCGCORE_DIR}/clone/lua/heap.cpp" APPEND PROPERTY COMPILE_OPTIONS -frtti)
endif()
