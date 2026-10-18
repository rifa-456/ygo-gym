cmake_minimum_required(VERSION 3.20)
project(ygo_gym_native LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

include(cmake/ocgcore.cmake)
add_subdirectory(engine)

install(TARGETS _native LIBRARY DESTINATION ygo_gym RUNTIME DESTINATION ygo_gym)
