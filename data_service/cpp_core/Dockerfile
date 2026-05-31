# Multi-stage build for C++ data processing module

# ============================================================================
# Stage 1: Build Python module
# ============================================================================
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libeigen3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pybind11
RUN pip install pybind11[global]

WORKDIR /app

# Copy source code
COPY CMakeLists.txt .
COPY include/ include/
COPY src/ src/
COPY python_bindings/ python_bindings/

# Build Python module
RUN mkdir -p build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF && \
    make -j$(nproc)

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

WORKDIR /app

# Copy built module
COPY --from=builder /app/build/energy_core*.so .

# Verify module can be imported
RUN python -c "import energy_core; print('Module loaded successfully')"

# Set entrypoint for testing
CMD ["python", "-c", "import energy_core; print(energy_core.__doc__)"]