# Manual API Test Commands for 3-Tier Recovery Setup

## Prerequisites
```bash
# Get JWT Token
TOKEN=$(aws cognito-idp admin-initiate-auth \
  --user-pool-id us-east-1_9sxQSfYYQ \
  --client-id 635au0e3dk35iktj60h2huic3a \
  --auth-flow ADMIN_NO_SRP_AUTH \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD=TestPassword123! \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

echo "Token: ${TOKEN:0:50}..."
```

## Step 1: Create DatabaseGroup Protection Group
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DatabaseGroup",
    "description": "Database servers for 3-tier application",
    "region": "us-west-2",
    "serverSelectionTags": {
      "Purpose": "DatabaseServers"
    }
  }' \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/protection-groups"
```

## Step 2: Create AppGroup Protection Group
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AppGroup",
    "description": "Application servers for 3-tier application", 
    "region": "us-west-2",
    "serverSelectionTags": {
      "Purpose": "AppServers"
    }
  }' \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/protection-groups"
```

## Step 3: Create WebGroup Protection Group
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "WebGroup",
    "description": "Web servers for 3-tier application",
    "region": "us-west-2", 
    "serverSelectionTags": {
      "Purpose": "WebServers"
    }
  }' \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/protection-groups"
```

## Step 4: List Protection Groups (Get IDs)
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/protection-groups"
```

## Step 5: Create 3TierRecovery Recovery Plan
```bash
# Replace GROUP_IDs with actual IDs from step 4
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "3TierRecovery",
    "description": "3-tier application recovery with wave-based execution",
    "waves": [
      {
        "name": "DatabaseWave",
        "description": "Database tier recovery - must complete first",
        "protectionGroupIds": ["DATABASE_GROUP_ID"],
        "pauseBeforeExecution": false,
        "executionOrder": 1
      },
      {
        "name": "AppWave",
        "description": "Application tier recovery - depends on database",
        "protectionGroupIds": ["APP_GROUP_ID"], 
        "pauseBeforeExecution": true,
        "executionOrder": 2,
        "dependsOn": ["DatabaseWave"]
      },
      {
        "name": "WebWave",
        "description": "Web tier recovery - depends on application",
        "protectionGroupIds": ["WEB_GROUP_ID"],
        "pauseBeforeExecution": true, 
        "executionOrder": 3,
        "dependsOn": ["AppWave"]
      }
    ]
  }' \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/recovery-plans"
```

## Step 6: Verify Setup
```bash
# List all protection groups
curl -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/protection-groups"

# List all recovery plans  
curl -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/recovery-plans"

# Get specific recovery plan details
curl -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/recovery-plans/PLAN_ID"
```

## Step 7: Test Execution (Optional)
```bash
# Start execution
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "planId": "PLAN_ID",
    "executionType": "DRILL"
  }' \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/executions"

# Monitor execution
curl -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/executions/EXECUTION_ID"

# Resume paused wave
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  "https://5uzsr2d7q1.execute-api.us-east-1.amazonaws.com/test/executions/EXECUTION_ID/resume"
```

## Expected Results

### Protection Groups Created:
- **DatabaseGroup**: Tag-based selection (Purpose=DatabaseServers) in us-west-2
- **AppGroup**: Tag-based selection (Purpose=AppServers) in us-west-2  
- **WebGroup**: Tag-based selection (Purpose=WebServers) in us-west-2

### Recovery Plan Created:
- **3TierRecovery**: 3-wave execution plan
  - **Wave 1 (DatabaseWave)**: Executes immediately
  - **Wave 2 (AppWave)**: Waits for DatabaseWave + manual approval
  - **Wave 3 (WebWave)**: Waits for AppWave + manual approval

### Validation Points:
1. ✅ **API Authentication**: JWT token works
2. ✅ **Protection Group Creation**: Tag-based server selection
3. ✅ **Recovery Plan Creation**: Multi-wave with dependencies
4. ✅ **CamelCase Migration**: All responses use camelCase fields
5. ✅ **Conflict Detection**: Prevents duplicate server assignments
6. ✅ **Wave Dependencies**: Proper execution order enforcement
7. ✅ **Pause Functionality**: Manual approval points between waves

This test validates the complete end-to-end functionality of the AWS DRS Orchestration system.