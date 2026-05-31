# Multi-stage build for C++ device simulator

# ============================================================================
# Stage 1: Build
# ============================================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    nlohmann-json3-dev \
    libpaho-mqtt-dev \
    libpaho-mqttcpp-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source code
COPY CMakeLists.txt .
COPY include/ include/
COPY src/ src/

# Build
RUN mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libssl3 \
    libpaho-mqtt1.1 \
    libpaho-mqttpp1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash simulator
USER simulator
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/build/smart_energy_device_simulator .

# Environment variables with defaults
ENV MQTT_BROKER=mosquitto
ENV MQTT_PORT=1883
ENV PUBLISH_INTERVAL=10
ENV API_URL=http://data_service:8000

# Expose nothing (outbound MQTT only)

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD pgrep -x smart_energy_device_simulator || exit 1

# Run
CMD ["./smart_energy_device_simulator"]