set(YGO_PUZZLES_DIR "${PROJECT_SOURCE_DIR}/third_party/Puzzles")
if(NOT EXISTS "${YGO_PUZZLES_DIR}/COPYING")
    message(FATAL_ERROR "Puzzle assets are missing. Run git submodule update --init --recursive")
endif()
install(DIRECTORY "${YGO_PUZZLES_DIR}/"
    DESTINATION ygo_gym/assets/puzzles
    FILES_MATCHING PATTERN "*.lua" PATTERN "COPYING" PATTERN "README.md"
    PATTERN ".git" EXCLUDE
)
