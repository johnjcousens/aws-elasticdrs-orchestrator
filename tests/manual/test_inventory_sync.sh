#!/bin/bash

# Task 7.1: Inventory Sync End-to-End Test Script
# Tests EventBridge rule triggering and inventory table updates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="aws-drs-orchestration-qa"
REGION="us-east-1"
RULE_NAME="aws-drs-orchestration-inventory-sync-qa"
INVENTORY_TABLE="aws-drs-orchestration-SourceServerInventory-qa"
REGION_STATUS_TABLE="aws-drs-orchestration-RegionStatus-qa"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Task 7.1: Inventory Sync End-to-End Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Verify EventBridge Rule
echo -e "${YELLOW}[Step 1/8] Verifying EventBridge Rule...${NC}"
RULE_INFO=$(aws events describe-rule \
  --name $RULE_NAME \
  --region $REGION \
  --query '{Name:Name,State:State,Schedule:ScheduleExpression,Description:Description}' \
  --output json 2>/dev/null || echo "{}")

if [ "$RULE_INFO" == "{}" ]; then
  echo -e "${RED}✗ EventBridge rule not found: $RULE_NAME${NC}"
  exit 1
fi

echo -e "${GREEN}✓ EventBridge rule found${NC}"
echo "$RULE_INFO" | jq .
echo ""

# Step 2: Verify Rule Target
echo -e "${YELLOW}[Step 2/8] Verifying Rule Target Configuration...${NC}"
TARGET_INFO=$(aws events list-targets-by-rule \
  --rule $RULE_NAME \
  --region $REGION \
  --query 'Targets[0].{Id:Id,Arn:Arn,Input:Input}' \
  --output json)

echo -e "${GREEN}✓ Rule target configuration:${NC}"
echo "$TARGET_INFO" | jq .

# Extract Lambda function ARN
LAMBDA_ARN=$(echo "$TARGET_INFO" | jq -r '.Arn')
LAMBDA_NAME=$(echo "$LAMBDA_ARN" | awk -F: '{print $NF}')
echo -e "${BLUE}Target Lambda: $LAMBDA_NAME${NC}"
echo ""

# Step 3: Get Current Inventory Count (Before Sync)
echo -e "${YELLOW}[Step 3/8] Getting Current Inventory State (Before Sync)...${NC}"
BEFORE_COUNT=$(aws dynamodb scan \
  --table-name $INVENTORY_TABLE \
  --select COUNT \
  --region $REGION \
  --query 'Count' \
  --output text 2>/dev/null || echo "0")

echo -e "${BLUE}Current inventory item count: $BEFORE_COUNT${NC}"

# Get sample items
echo -e "${BLUE}Sample inventory items (last 5):${NC}"
aws dynamodb scan \
  --table-name $INVENTORY_TABLE \
  --limit 5 \
  --region $REGION \
  --query 'Items[*].{ServerID:sourceServerId.S,Hostname:hostname.S,LastUpdated:lastUpdated.S,Region:region.S}' \
  --output table 2>/dev/null || echo "No items found"
echo ""

# Step 4: Invoke Lambda Function Directly
echo -e "${YELLOW}[Step 4/8] Triggering Inventory Sync (Direct Lambda Invocation)...${NC}"
echo -e "${BLUE}Invoking Lambda: $LAMBDA_NAME${NC}"

# Create payload
PAYLOAD='{"operation": "sync_source_server_inventory"}'

# Invoke Lambda
aws lambda invoke \
  --function-name $LAMBDA_NAME \
  --payload "$PAYLOAD" \
  --region $REGION \
  --log-type Tail \
  response.json > invoke_result.json 2>&1

# Check invocation status
INVOKE_STATUS=$(cat invoke_result.json | jq -r '.StatusCode')
if [ "$INVOKE_STATUS" == "200" ]; then
  echo -e "${GREEN}✓ Lambda invoked successfully (Status: $INVOKE_STATUS)${NC}"
else
  echo -e "${RED}✗ Lambda invocation failed (Status: $INVOKE_STATUS)${NC}"
  cat invoke_result.json | jq .
  exit 1
fi

# Show response
echo -e "${BLUE}Lambda response:${NC}"
cat response.json | jq . 2>/dev/null || cat response.json
echo ""

# Step 5: Monitor Lambda Execution (CloudWatch Logs)
echo -e "${YELLOW}[Step 5/8] Checking Lambda Execution Logs...${NC}"
echo -e "${BLUE}Fetching recent logs from /aws/lambda/$LAMBDA_NAME...${NC}"

# Wait a moment for logs to be available
sleep 3

# Get recent logs
aws logs tail /aws/lambda/$LAMBDA_NAME \
  --since 2m \
  --region $REGION \
  --format short 2>/dev/null | head -50 || echo "No recent logs found"
echo ""

# Step 6: Verify Inventory Table Updates (After Sync)
echo -e "${YELLOW}[Step 6/8] Verifying Inventory Table Updates (After Sync)...${NC}"

# Wait for sync to complete
echo -e "${BLUE}Waiting 5 seconds for sync to complete...${NC}"
sleep 5

AFTER_COUNT=$(aws dynamodb scan \
  --table-name $INVENTORY_TABLE \
  --select COUNT \
  --region $REGION \
  --query 'Count' \
  --output text 2>/dev/null || echo "0")

echo -e "${BLUE}Inventory item count after sync: $AFTER_COUNT${NC}"

# Calculate difference
DIFF=$((AFTER_COUNT - BEFORE_COUNT))
if [ $DIFF -gt 0 ]; then
  echo -e "${GREEN}✓ Inventory table updated: +$DIFF items${NC}"
elif [ $DIFF -eq 0 ]; then
  echo -e "${YELLOW}⚠ Inventory count unchanged (may indicate no new servers or sync already current)${NC}"
else
  echo -e "${YELLOW}⚠ Inventory count decreased: $DIFF items (stale records removed)${NC}"
fi

# Get recently updated items
echo -e "${BLUE}Recently updated inventory items (last 10):${NC}"
aws dynamodb scan \
  --table-name $INVENTORY_TABLE \
  --limit 10 \
  --region $REGION \
  --query 'Items[*].{ServerID:sourceServerId.S,Hostname:hostname.S,LastUpdated:lastUpdated.S,Region:region.S,Status:replicationStatus.S}' \
  --output table 2>/dev/null || echo "No items found"
echo ""

# Step 7: Verify Region Status Table Updates
echo -e "${YELLOW}[Step 7/8] Verifying Region Status Table Updates...${NC}"
aws dynamodb scan \
  --table-name $REGION_STATUS_TABLE \
  --region $REGION \
  --query 'Items[*].{Region:region.S,Account:accountId.S,ServerCount:serverCount.N,LastSync:lastSyncTime.S}' \
  --output table 2>/dev/null || echo "No region status data found"
echo ""

# Step 8: Check Lambda Metrics
echo -e "${YELLOW}[Step 8/8] Checking Lambda Metrics...${NC}"

# Get invocation count (last 15 minutes)
echo -e "${BLUE}Lambda invocations (last 15 minutes):${NC}"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=$LAMBDA_NAME \
  --start-time $(date -u -v-15M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region $REGION \
  --query 'Datapoints[*].{Timestamp:Timestamp,Invocations:Sum}' \
  --output table 2>/dev/null || echo "No metrics available"

# Get error count
echo -e "${BLUE}Lambda errors (last 15 minutes):${NC}"
ERROR_COUNT=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=$LAMBDA_NAME \
  --start-time $(date -u -v-15M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --region $REGION \
  --query 'Datapoints[*].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" == "0" ] || [ -z "$ERROR_COUNT" ]; then
  echo -e "${GREEN}✓ No errors detected${NC}"
else
  echo -e "${RED}✗ Errors detected: $ERROR_COUNT${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "EventBridge Rule: ${GREEN}$RULE_NAME${NC}"
echo -e "Target Lambda: ${GREEN}$LAMBDA_NAME${NC}"
echo -e "Inventory Before: ${BLUE}$BEFORE_COUNT items${NC}"
echo -e "Inventory After: ${BLUE}$AFTER_COUNT items${NC}"
echo -e "Change: ${BLUE}$DIFF items${NC}"
echo -e "Lambda Errors: ${BLUE}$ERROR_COUNT${NC}"
echo ""

# Cleanup
rm -f response.json invoke_result.json

# Final status
if [ "$ERROR_COUNT" == "0" ] || [ -z "$ERROR_COUNT" ]; then
  echo -e "${GREEN}✓ Test PASSED - Inventory sync completed successfully${NC}"
  exit 0
else
  echo -e "${RED}✗ Test FAILED - Errors detected during sync${NC}"
  exit 1
fi
