#!/bin/bash

# ============================================================================
# Smart Energy Platform - 集成测试脚本
# ============================================================================

set -e

echo "=========================================="
echo "Smart Energy Platform - Integration Test"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TESTS_PASSED=0
TESTS_FAILED=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -e "\n${YELLOW}Testing: ${test_name}${NC}"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED: ${test_name}${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAILED: ${test_name}${NC}"
        ((TESTS_FAILED++))
    fi
}

# 等待服务启动
wait_for_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1

    echo "Waiting for ${service_name} to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}${service_name} is ready!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}${service_name} failed to start${NC}"
    return 1
}

# ============================================================================
# 测试开始
# ============================================================================

echo ""
echo "Step 1: Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}Docker is running${NC}"

echo ""
echo "Step 2: Starting services with docker-compose..."
docker-compose up -d --build

echo ""
echo "Step 3: Waiting for services to be ready..."

# 等待各个服务
wait_for_service "PostgreSQL" "http://localhost:5432" || true
wait_for_service "InfluxDB" "http://localhost:8086/health"
wait_for_service "Data Service" "http://localhost:8000/health"
wait_for_service "Web App" "http://localhost:3000"
wait_for_service "Analyst Tool" "http://localhost:8501/_stcore/health"
wait_for_service "Nginx" "http://localhost:80/health"

echo ""
echo "Step 4: Running integration tests..."

# 测试1: API健康检查
run_test "API Health Check" \
    "curl -s http://localhost:8000/health | grep -q 'healthy'"

# 测试2: API状态检查
run_test "API Status" \
    "curl -s http://localhost:8000/api/status | grep -q 'running'"

# 测试3: 获取设备列表
run_test "Get Devices List" \
    "curl -s http://localhost:8000/api/devices | python3 -c 'import sys,json; json.load(sys.stdin)'"

# 测试4: 创建测试读数
run_test "Create Reading" \
    "curl -s -X POST http://localhost:8000/api/readings \
        -H 'Content-Type: application/json' \
        -d '{
            \"device_id\": \"test_device_001\",
            \"power_watts\": 1500.5,
            \"energy_kwh\": 45.2,
            \"voltage\": 220.0,
            \"current_amps\": 6.82
        }' | python3 -c 'import sys,json; data=json.load(sys.stdin); assert \"id\" in data'"

# 测试5: 获取设备读数
run_test "Get Device Readings" \
    "curl -s 'http://localhost:8000/api/devices/test_device_001/readings?limit=10' | python3 -c 'import sys,json; json.load(sys.stdin)'"

# 测试6: Web App可访问
run_test "Web App Accessible" \
    "curl -s http://localhost:3000 | grep -q 'Smart Energy'"

# 测试7: Analyst Tool可访问
run_test "Analyst Tool Accessible" \
    "curl -s http://localhost:8501/_stcore/health | grep -q 'ok'"

# 测试8: Nginx反向代理 - 主应用
run_test "Nginx Proxy - Web App" \
    "curl -s http://localhost:80 | grep -q 'Smart Energy'"

# 测试9: Nginx反向代理 - API
run_test "Nginx Proxy - API" \
    "curl -s http://localhost:80/api/health | grep -q 'healthy'"

# 测试10: Nginx反向代理 - Analyst
run_test "Nginx Proxy - Analyst" \
    "curl -s http://localhost:80/analyst/_stcore/health | grep -q 'ok'"

# 测试11: MQTT连接检查
run_test "MQTT Broker Running" \
    "docker exec smart-energy-mqtt mosquitto_pub -t 'test' -m 'hello' && echo 'MQTT OK'"

# 测试12: 数据库连接检查
run_test "Database Connection" \
    "docker exec smart-energy-postgres pg_isready -U energy_admin -d smart_energy"

# 测试13: InfluxDB连接检查
run_test "InfluxDB Connection" \
    "curl -s http://localhost:8086/health | python3 -c 'import sys,json; data=json.load(sys.stdin); assert data[\"status\"]==\"pass\"'"

# ============================================================================
# 测试结果
# ============================================================================

echo ""
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo -e "${GREEN}Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
echo "Total: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Services are running at:"
    echo "  - Web App: http://localhost:3000"
    echo "  - Analyst Tool: http://localhost:8501"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Nginx (Main): http://localhost:80"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed. Please check the logs.${NC}"
    echo ""
    echo "View logs with:"
    echo "  docker-compose logs"
    exit 1
fi