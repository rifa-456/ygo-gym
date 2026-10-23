find_program(YGO_DOTNET_EXECUTABLE NAMES dotnet REQUIRED)
execute_process(COMMAND "${YGO_DOTNET_EXECUTABLE}" --version
    WORKING_DIRECTORY "${PROJECT_SOURCE_DIR}"
    OUTPUT_VARIABLE YGO_DOTNET_SDK_VERSION OUTPUT_STRIP_TRAILING_WHITESPACE
    COMMAND_ERROR_IS_FATAL ANY)
if(NOT YGO_DOTNET_SDK_VERSION MATCHES "^10\\.")
    message(FATAL_ERROR "Building the bundled worker requires the .NET 10 SDK.")
endif()

if(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    set(YGO_DOTNET_PLATFORM "win")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    set(YGO_DOTNET_PLATFORM "linux")
else()
    message(FATAL_ERROR "Bundled WindBot wheels currently support Windows and Linux.")
endif()
if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(AMD64|amd64|x86_64)$")
    set(YGO_DOTNET_ARCH "x64")
else()
    message(FATAL_ERROR "Bundled WindBot wheels currently support x64 processors.")
endif()

set(YGO_WINDBOT_PUBLISH "${PROJECT_BINARY_DIR}/windbot-publish/${YGO_DOTNET_SDK_VERSION}/${YGO_DOTNET_PLATFORM}-${YGO_DOTNET_ARCH}")
file(GLOB_RECURSE YGO_WINDBOT_SOURCES CONFIGURE_DEPENDS
    "${PROJECT_SOURCE_DIR}/integrations/windbot/Host/*.cs"
    "${YGO_WINDBOT_DIR}/*.cs")
add_custom_command(OUTPUT "${YGO_WINDBOT_PUBLISH}/build.json"
    COMMAND "${Python_EXECUTABLE}" "${CMAKE_CURRENT_LIST_DIR}/publish_windbot.py"
        "${YGO_DOTNET_EXECUTABLE}" "${PROJECT_SOURCE_DIR}"
        "${YGO_WINDBOT_PUBLISH}" "${YGO_DOTNET_PLATFORM}-${YGO_DOTNET_ARCH}"
    DEPENDS ${YGO_WINDBOT_SOURCES}
        "${PROJECT_SOURCE_DIR}/integrations/windbot/Host/Host.csproj"
        "${PROJECT_SOURCE_DIR}/global.json"
        "${CMAKE_CURRENT_LIST_DIR}/publish_windbot.py"
    VERBATIM)
add_custom_target(ygo_windbot ALL DEPENDS "${YGO_WINDBOT_PUBLISH}/build.json")
install(DIRECTORY "${YGO_WINDBOT_PUBLISH}/" DESTINATION "${YGO_ASSET_DESTINATION}/windbot/runtime"
    USE_SOURCE_PERMISSIONS PATTERN "obj" EXCLUDE PATTERN "*.pdb" EXCLUDE)
