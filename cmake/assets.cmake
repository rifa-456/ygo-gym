set(YGO_ASSET_DESTINATION "ygo_gym/assets")
set(YGO_SCRIPTS_DIR "${PROJECT_SOURCE_DIR}/third_party/CardScripts")
set(YGO_DATABASE_DIR "${PROJECT_SOURCE_DIR}/third_party/BabelCDB")
set(YGO_WINDBOT_DIR "${PROJECT_SOURCE_DIR}/third_party/WindBot")

foreach(required_asset IN ITEMS
    "${YGO_DATABASE_DIR}/cards.cdb"
    "${YGO_SCRIPTS_DIR}/utility.lua"
    "${YGO_WINDBOT_DIR}/bots.json"
)
    if(NOT EXISTS "${required_asset}")
        message(FATAL_ERROR "Missing ${required_asset}. Initialize the repository submodules before building a wheel.")
    endif()
endforeach()

install(FILES "${YGO_DATABASE_DIR}/cards.cdb" DESTINATION "${YGO_ASSET_DESTINATION}/database")
install(DIRECTORY "${YGO_SCRIPTS_DIR}/" DESTINATION "${YGO_ASSET_DESTINATION}/scripts"
    FILES_MATCHING PATTERN "*.lua" PATTERN "COPYING" PATTERN ".git" EXCLUDE)
include("${CMAKE_CURRENT_LIST_DIR}/puzzles.cmake")
install(DIRECTORY "${YGO_WINDBOT_DIR}/Decks" "${YGO_WINDBOT_DIR}/Dialogs"
    DESTINATION "${YGO_ASSET_DESTINATION}/windbot"
    FILES_MATCHING PATTERN "*.ydk" PATTERN "*.json")
install(FILES "${YGO_WINDBOT_DIR}/bots.json" "${YGO_WINDBOT_DIR}/LICENSE" "${YGO_WINDBOT_DIR}/COPYING"
    DESTINATION "${YGO_ASSET_DESTINATION}/windbot")
install(FILES "${YGO_DATABASE_DIR}/README.md" DESTINATION "${YGO_ASSET_DESTINATION}/database")
install(FILES "${OCGCORE_DIR}/COPYING" DESTINATION "${YGO_ASSET_DESTINATION}/licenses/core")
install(FILES "${LUA_DIR}/src/lua.h" DESTINATION "${YGO_ASSET_DESTINATION}/licenses/lua")

set(YGO_ASSET_MANIFEST "${PROJECT_BINARY_DIR}/assets-manifest.json")
add_custom_target(ygo_asset_manifest ALL
    COMMAND "${Python_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/assets_manifest.py"
        "${PROJECT_SOURCE_DIR}" "${YGO_ASSET_MANIFEST}"
    VERBATIM)
install(FILES "${YGO_ASSET_MANIFEST}" DESTINATION "${YGO_ASSET_DESTINATION}" RENAME "manifest.json")
