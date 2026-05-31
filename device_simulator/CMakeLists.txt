cmake_minimum_required(VERSION 3.16)
project(smart_energy_device_simulator VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Find required packages
find_package(Threads REQUIRED)

# Paho MQTT C++ (static linking)
find_package(eclipse-paho-mqtt-cpp QUIET)
if(NOT eclipse-paho-mqtt-cpp_FOUND)
    # Try to find via pkg-config
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(PAHO_MQTT_CPP REQUIRED paho-mqttpp3)
endif()

# nlohmann/json for JSON handling
find_package(nlohmann_json 3.2.0 QUIET)
if(NOT nlohmann_json_FOUND)
    # Will be fetched if not found
    include(FetchContent)
    FetchContent_Declare(
        json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
    )
    FetchContent_MakeAvailable(json)
endif()

# Source files
set(SOURCES
    src/main.cpp
    src/device_simulator.cpp
    src/mqtt_client.cpp
    src/smart_meter.cpp
    src/solar_panel.cpp
    src/battery.cpp
    src/ev_charger.cpp
    src/hvac.cpp
)

# Header files
set(HEADERS
    include/device_simulator.h
    include/mqtt_client.h
    include/smart_meter.h
    include/solar_panel.h
    include/battery.h
    include/ev_charger.h
    include/hvac.h
    include/config.h
)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Include directories
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE
    Threads::Threads
    nlohmann_json::nlohmann_json
)

if(eclipse-paho-mqtt-cpp_FOUND)
    target_link_libraries(${PROJECT_NAME} PRIVATE eclipse-paho-mqttpp3)
else()
    target_include_directories(${PROJECT_NAME} PRIVATE ${PAHO_MQTT_CPP_INCLUDE_DIRS})
    target_link_libraries(${PROJECT_NAME} PRIVATE ${PAHO_MQTT_CPP_LIBRARIES})
endif()

# Compiler warnings
target_compile_options(${PROJECT_NAME} PRIVATE
    -Wall -Wextra -Wpedantic
)

# Install
install(TARGETS ${PROJECT_NAME} RUNTIME DESTINATION bin)