cmake_minimum_required(VERSION 3.16)
project(smart_energy_core VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find pybind11 for Python bindings
find_package(pybind11 CONFIG REQUIRED)

# Find Eigen for linear algebra
find_package(Eigen3 3.3 QUIET NO_MODULE)
if(NOT Eigen3_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        eigen
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG 3.4.0
    )
    FetchContent_MakeAvailable(eigen)
endif()

# Source files
set(SOURCES
    src/data_processor.cpp
    src/predictor.cpp
    src/statistics.cpp
)

set(HEADERS
    include/data_processor.h
    include/predictor.h
    include/statistics.h
    include/types.h
)

# Create Python module
pybind11_add_module(energy_core
    python_bindings/bindings.cpp
    ${SOURCES}
)

target_include_directories(energy_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(energy_core PRIVATE
    Eigen3::Eigen
)

# Also build standalone library for testing
add_library(energy_core_lib STATIC ${SOURCES})
target_include_directories(energy_core_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(energy_core_lib PUBLIC Eigen3::Eigen)

# Testing
option(BUILD_TESTS "Build tests" ON)
if(BUILD_TESTS)
    enable_testing()
    add_executable(test_processor tests/test_main.cpp)
    target_link_libraries(test_processor PRIVATE energy_core_lib)
    add_test(NAME test_processor COMMAND test_processor)
endif()