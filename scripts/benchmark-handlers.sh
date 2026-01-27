#!/bin/bash
# Simple Performance Benchmark for Lambda Handlers
# Measures cold start times with reliable timing

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGION="us-east-1"
QUERY_FUNCTION="aws-drs-orchestration-query-handler-dev"
EXEC_FUNCTION="aws-drs-orchestration-execution-handler-dev"
DM_FUNCTION="aws-drs-orchestration-data-management-handler-dev"

echo "=========================================="
echo "Lambda Handler Performance Benchmark"
echo "=========================================="
echo ""

# Function to measure cold start
measure_cold_start() {
  local function_name=$1
  local handler_name=$2
  
  echo -e "${BLUE}Measuring cold start: $handler_name${NC}" >&2
  
  # Force cold start by updating environment variable
  echo "  Forcing cold start..." >&2
  aws lambda update-function-configuration \
    --function-name "$function_name" \
    --environment "Variables={FORCE_COLD_START=$(date +%s)}" \
    --region "$REGION" > /dev/null 2>&1
  
  # Wait for update to complete
  sleep 5
  
  # Measure invocation time
  local start=$(python3 -c 'import time; print(int(time.time() * 1000))')
  aws lambda invoke \
    --function-name "$function_name" \
    --payload '{"httpMethod":"GET","path":"/health"}' \
    --region "$REGION" \
    /tmp/lambda-response.json > /dev/null 2>&1
  local end=$(python3 -c 'import time; print(int(time.time() * 1000))')
  local duration=$((end - start))
  
  echo -e "  ${GREEN}Cold start: ${duration}ms${NC}" >&2
  echo "" >&2
  
  echo "$duration"
}

# Function to measure warm execution
measure_warm_execution() {
  local function_name=$1
  local handler_name=$2
  local samples=5
  
  echo -e "${BLUE}Measuring warm execution: $handler_name (${samples} samples)${NC}" >&2
  
  local total=0
  local min=999999
  local max=0
  declare -a durations
  
  for i in $(seq 1 $samples); do
    local start=$(python3 -c 'import time; print(int(time.time() * 1000))')
    aws lambda invoke \
      --function-name "$function_name" \
      --payload '{"httpMethod":"GET","path":"/health"}' \
      --region "$REGION" \
      /tmp/lambda-response.json > /dev/null 2>&1
    local end=$(python3 -c 'import time; print(int(time.time() * 1000))')
    local duration=$((end - start))
    
    durations+=($duration)
    total=$((total + duration))
    [ $duration -lt $min ] && min=$duration
    [ $duration -gt $max ] && max=$duration
    
    echo "    Sample $i: ${duration}ms" >&2
    sleep 1
  done
  
  local avg=$((total / samples))
  echo -e "  ${GREEN}Average: ${avg}ms (min: ${min}ms, max: ${max}ms)${NC}" >&2
  echo "" >&2
  
  echo "$avg $min $max"
}

# Measure Query Handler
echo "=========================================="
echo "Query Handler"
echo "=========================================="
echo ""
query_cold=$(measure_cold_start "$QUERY_FUNCTION" "Query Handler")
query_warm=$(measure_warm_execution "$QUERY_FUNCTION" "Query Handler")
query_warm_avg=$(echo $query_warm | cut -d' ' -f1)
query_warm_min=$(echo $query_warm | cut -d' ' -f2)
query_warm_max=$(echo $query_warm | cut -d' ' -f3)

# Measure Execution Handler
echo "=========================================="
echo "Execution Handler"
echo "=========================================="
echo ""
exec_cold=$(measure_cold_start "$EXEC_FUNCTION" "Execution Handler")
exec_warm=$(measure_warm_execution "$EXEC_FUNCTION" "Execution Handler")
exec_warm_avg=$(echo $exec_warm | cut -d' ' -f1)
exec_warm_min=$(echo $exec_warm | cut -d' ' -f2)
exec_warm_max=$(echo $exec_warm | cut -d' ' -f3)

# Measure Data Management Handler
echo "=========================================="
echo "Data Management Handler"
echo "=========================================="
echo ""
dm_cold=$(measure_cold_start "$DM_FUNCTION" "Data Management Handler")
dm_warm=$(measure_warm_execution "$DM_FUNCTION" "Data Management Handler")
dm_warm_avg=$(echo $dm_warm | cut -d' ' -f1)
dm_warm_min=$(echo $dm_warm | cut -d' ' -f2)
dm_warm_max=$(echo $dm_warm | cut -d' ' -f3)

# Summary
echo "=========================================="
echo "Benchmark Summary"
echo "=========================================="
echo ""

echo "Cold Start Performance:"
echo "  Query Handler:          ${query_cold}ms (target: < 2000ms)"
echo "  Execution Handler:      ${exec_cold}ms (target: < 3000ms)"
echo "  Data Management Handler: ${dm_cold}ms (target: < 3000ms)"
echo ""

echo "Warm Execution Performance (5 samples):"
echo "  Query Handler:          ${query_warm_avg}ms avg (${query_warm_min}-${query_warm_max}ms)"
echo "  Execution Handler:      ${exec_warm_avg}ms avg (${exec_warm_min}-${exec_warm_max}ms)"
echo "  Data Management Handler: ${dm_warm_avg}ms avg (${dm_warm_min}-${dm_warm_max}ms)"
echo ""

# Check targets
echo "Target Validation:"
if [ $query_cold -lt 2000 ]; then
  echo -e "  Query Handler cold start:          ${GREEN}✓ PASS${NC}"
else
  echo -e "  Query Handler cold start:          ${RED}✗ FAIL${NC}"
fi

if [ $exec_cold -lt 3000 ]; then
  echo -e "  Execution Handler cold start:      ${GREEN}✓ PASS${NC}"
else
  echo -e "  Execution Handler cold start:      ${RED}✗ FAIL${NC}"
fi

if [ $dm_cold -lt 3000 ]; then
  echo -e "  Data Management Handler cold start: ${GREEN}✓ PASS${NC}"
else
  echo -e "  Data Management Handler cold start: ${RED}✗ FAIL${NC}"
fi

if [ $query_warm_avg -lt 500 ]; then
  echo -e "  Query Handler warm execution:      ${GREEN}✓ PASS${NC}"
else
  echo -e "  Query Handler warm execution:      ${YELLOW}⚠ WARN (target: < 500ms)${NC}"
fi

if [ $exec_warm_avg -lt 500 ]; then
  echo -e "  Execution Handler warm execution:  ${GREEN}✓ PASS${NC}"
else
  echo -e "  Execution Handler warm execution:  ${YELLOW}⚠ WARN (target: < 500ms)${NC}"
fi

if [ $dm_warm_avg -lt 500 ]; then
  echo -e "  Data Management Handler warm exec: ${GREEN}✓ PASS${NC}"
else
  echo -e "  Data Management Handler warm exec: ${YELLOW}⚠ WARN (target: < 500ms)${NC}"
fi

echo ""
echo "=========================================="
echo "Benchmark Complete"
echo "=========================================="
