set(YGO_NATIVE_EXTRAS)
if(YGO_PROFILE_SYMBOLS AND NOT MSVC)
    list(APPEND YGO_NATIVE_EXTRAS NO_EXTRAS)
endif()

pybind11_add_module(_native MODULE ${YGO_NATIVE_EXTRAS}
    binding.cpp
    engine.cpp
)

target_include_directories(_native PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    "${PROJECT_SOURCE_DIR}/third_party"
)
target_link_libraries(_native PRIVATE ocgcore)

if(MSVC)
    target_compile_options(_native PRIVATE /W4)
else()
    target_compile_options(_native PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_subdirectory(action)

add_subdirectory(duel)

add_subdirectory(event)

add_subdirectory(protocol)

add_subdirectory(state)

add_subdirectory(profiling)
