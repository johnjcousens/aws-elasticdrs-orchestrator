# Lambda Functions Inventory

## Current Architecture (6 Functions)

All Lambda functions verified against CloudFormation template `cfn/lambda-stack.yaml`.

### 1. Query Handler
- **Function Name**: `${ProjectName}-query-handler-${Environment}`
- **S3 Key**: `lambda/query-handler.zip`
- **Directory**: `lambda/query-handler/`
- **Purpose**: Read-only infrastructure queries
  - Source servers
  - DRS quotas and capacity
  - EC2 resources
  - Configuration export
- **Timeout**: 60s
- **Memory**: 256 MB
- **Status**: ✅ Implemented

### 2. Data Management Handler
- **Function Name**: `${ProjectName}-data-management-handler-${Environment}`
- **S3 Key**: `lambda/data-management-handler.zip`
- **Directory**: `lambda/data-management-handler/`
- **Purpose**: Protection Groups & Recovery Plans CRUD
  - Tag resolution
  - Launch configuration
  - Conflict detection
- **Timeout**: 120s
- **Memory**: 512 MB
- **Status**: ✅ Implemented

### 3. Execution Handler
- **Function Name**: `${ProjectName}-execution-handler-${Environment}`
- **S3 Key**: `lambda/execution-handler.zip`
- **Directory**: `lambda/execution-handler/`
- **Purpose**: DR execution lifecycle operations
  - Recovery plan execution
  - Pause/resume operations
  - Termination
  - DRS operations
- **Timeout**: 300s (5 minutes)
- **Memory**: 512 MB
- **Status**: ✅ Implemented

### 4. Frontend Deployer
- **Function Name**: `${ProjectName}-frontend-deployer-${Environment}`
- **S3 Key**: `lambda/frontend-deployer.zip`
- **Directory**: `lambda/frontend-deployer/`
- **Purpose**: Frontend deployment automation
  - Frontend build
  - S3 bucket operations
  - CloudFront invalidation
- **Timeout**: 900s (15 minutes)
- **Memory**: 2048 MB
- **Special**: Includes pre-built frontend/dist/ in package
- **Status**: ✅ Implemented

### 5. Orchestration Step Functions
- **Function Name**: `${ProjectName}-orch-sf-${Environment}`
- **S3 Key**: `lambda/orchestration-stepfunctions.zip`
- **Directory**: `lambda/orchestration-stepfunctions/`
- **Purpose**: Step Functions orchestration
  - Archive Pattern implementation
  - State management via OutputPath
- **Timeout**: 120s
- **Memory**: 512 MB
- **Status**: ✅ Implemented

### 6. Notification Formatter
- **Function Name**: `${ProjectName}-notification-formatter-${Environment}`
- **S3 Key**: `lambda/notification-formatter.zip`
- **Directory**: `lambda/notification-formatter/`
- **Purpose**: SNS notification formatting
  - Routes to appropriate SNS topics
  - Event type-based routing
- **Timeout**: 60s
- **Memory**: 256 MB
- **Status**: ✅ Implemented

## Removed/Legacy Functions

### Not in Current Architecture:
- ❌ **api-handler** - Monolithic handler, replaced by decomposed handlers (query, data-management, execution)
- ❌ **execution-finder** - Legacy, functionality moved to execution-handler
- ❌ **execution-poller** - Legacy, functionality moved to execution-handler
- ❌ **frontend-builder** - Replaced by frontend-deployer
- ❌ **bucket-cleaner** - Functionality consolidated into frontend-deployer

## Script Alignment

### ✅ package_lambda.py
```python
lambdas = [
    ("query-handler", False),
    ("data-management-handler", False),
    ("execution-handler", False),
    ("frontend-deployer", True),  # Includes frontend dist
    ("notification-formatter", False),
    ("orchestration-stepfunctions", False),
]
```

### ✅ scripts/deploy.sh
```bash
FUNCTIONS="data-management-handler execution-handler query-handler frontend-deployer orch-sf:orchestration-stepfunctions notification-formatter"
```

### ✅ scripts/local-deploy.sh
```bash
FUNCTIONS="query-handler data-management-handler execution-handler frontend-deployer:frontend-deployer orch-sf:orchestration-stepfunctions notification-formatter"
```

### ✅ scripts/prepare-deployment-bucket.sh
```bash
for func_dir in query-handler data-management-handler execution-handler frontend-deployer notification-formatter orchestration-stepfunctions; do
```

## Verification Commands

### Check all Lambda directories exist:
```bash
ls -d lambda/query-handler lambda/data-management-handler lambda/execution-handler lambda/frontend-deployer lambda/notification-formatter lambda/orchestration-stepfunctions
```

### Package all Lambda functions:
```bash
python3 package_lambda.py
ls -lh build/lambda/
```

### Verify CloudFormation template:
```bash
grep -A 5 "Type: AWS::Lambda::Function" cfn/lambda-stack.yaml
```

## Notes

1. All 6 Lambda functions are properly defined in CloudFormation
2. All 6 directories exist in the repository
3. All deployment scripts reference the correct functions
4. S3 keys match the expected naming convention
5. No orphaned or missing functions
6. Package script will skip non-existent directories gracefully
