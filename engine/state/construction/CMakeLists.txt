target_sources(_native PRIVATE
    card_lookup.cpp
    clone.cpp
)

add_subdirectory(full_state)

add_subdirectory(observation)
