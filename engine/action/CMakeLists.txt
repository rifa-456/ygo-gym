target_sources(_native PRIVATE
    action.cpp
    response.cpp
    state.cpp
)

add_subdirectory(bindings)

add_subdirectory(candidates)

add_subdirectory(legality)
