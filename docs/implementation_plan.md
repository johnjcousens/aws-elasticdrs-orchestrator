# Implementation Plan

## Overview

Build a comprehensive AWS Elastic Disaster Recovery (DRS) orchestration and automation solution from scratch that achieves functional parity with VMware Site Recovery Manager (SRM), deployed via a single CloudFormation master template with minimal nested stacks for Lambda and frontend deployment.

This greenfield solution will provide a modern, serverless DR management platform enabling users to define, execute, and monitor complex failover/failback procedures through a React-based web interface. The architecture eliminates deprecated AWS services (CodeCommit/CodePipeline) in favor of direct CloudFormation deployment with SAM-based Lambda packaging and custom resource-based frontend builds. The solution targets new AWS customers with simplified deployment (single AWS CLI command) while maintaining enterprise-grade reliability and observability through Step Functions orchestration, DynamoDB persistence, and CloudWatch monitoring.

The implementation follows a three-phase approach: Phase 1 establishes infrastructure and data layer (DynamoDB, Lambda, Step Functions), Phase 2 adds API and integration layer (API Gateway, Cognito, SSM), and Phase 3 delivers frontend and complete integration (React SPA, CloudFront, S3). This phased strategy enables incremental testing at each layer with comprehensive validation before advancing to the next phase.

## Types

Define comprehensive data types, interfaces, and structures for Protection Groups, Recovery Plans, Waves, and execution state management.

### DynamoDB Schema Types

**DRProtectionGroup Table Schema:**
```typescript
interface DRProtectionGroup {
  GroupId: string;              // Partition Key (UUID)
  GroupName: string;            // User-defined name
  Description: string;          // User-defined description
  SourceServerIds: string[];    // Array of DRS Source Server IDs
  Tags: {                       // AWS tags for server selection
    KeyName: string;
    KeyValue: string;
  };
  AccountId: string;            // AWS Account where servers reside
  Region: string;               // AWS Region where servers reside
  Owner: string;                // Email address
  CreatedDate: number;          // Epoch timestamp
  LastModifiedDate: number;     // Epoch timestamp
}
```

**RecoveryPlan Table Schema:**
```typescript
interface RecoveryPlan {
  PlanId: string;               // Partition Key (UUID)
  PlanName: string;             // User-defined plan name
  Description: string;          // User-defined description
  AccountId: string;            // Target AWS Account
  Region: string;               // Target AWS Region
  Owner: string;                // Email address
  RPO: number;                  // Recovery Point Objective (minutes)
  RTO: number;                  // Recovery Time Objective (minutes)
  Waves: Wave[];                // Ordered array of Wave definitions
  CreatedDate: number;          // Epoch timestamp
  LastModifiedDate: number;     // Epoch timestamp
  LastExecutedDate?: number;    // Epoch timestamp
}

interface Wave {
  WaveId: string;               // UUID
  WaveName: string;             // User-defined name
  Description: string;          // User-defined description
  ProtectionGroupId: string;    // Reference to DRProtectionGroup
  ExecutionOrder: number;       // Sequence number (1, 2, 3...)
  Dependencies: WaveDependency[]; // Array of dependency rules
  MaxWaitTime: number;          // Maximum wait time (seconds)
  UpdateInterval: number;       // Status check interval (seconds)
  PreWaveActions: AutomationAction[];
  PostWaveActions: AutomationAction[];
}

interface WaveDependency {
  DependsOnWaveId: string;      // UUID of prerequisite wave
  ConditionType: 'COMPLETE' | 'RUNNING' | 'HEALTHY';
  InstanceId?: string;          // Specific EC2 instance (optional)
  HealthCheckType?: 'STATUS_CHECK' | 'CUSTOM_SCRIPT';
}

interface AutomationAction {
  ActionId: string;             // UUID
  ActionName: string;           // User-defined name
  Description: string;          // User-defined description
  ActionType: 'SSM_DOCUMENT' | 'LAMBDA' | 'WAIT' | 'MANUAL_APPROVAL';
  SSMDocument?: {
    DocumentName: string;       // SSM Document name
    Parameters: Record<string, string[]>; // SSM parameters
    TargetType: 'SOURCE_SERVER' | 'RECOVERED_INSTANCE' | 'TAG' | 'RESOURCE_GROUP';
    TargetKey?: string;         // Tag key or resource group name
    TargetValue?: string;       // Tag value
  };
  MaxWaitTime: number;          // Timeout (seconds)
  UpdateInterval: number;       // Status check interval (seconds)
}
```

**ExecutionHistory Table Schema:**
```typescript
interface ExecutionHistory {
  ExecutionId: string;          // Partition Key (Step Functions execution ARN)
  PlanId: string;               // Sort Key
  ExecutionType: 'DRILL' | 'RECOVERY' | 'FAILBACK';
  Status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMEOUT' | 'CANCELLED';
  StartTime: number;            // Epoch timestamp
  EndTime?: number;             // Epoch timestamp
  Duration?: number;            // Seconds
  InitiatedBy: string;          // User email
  TopicArn?: string;            // SNS notification topic
  WaveResults: WaveExecutionResult[];
  ErrorDetails?: {
    ErrorType: string;
    ErrorMessage: string;
    FailedWaveId?: string;
    FailedActionId?: string;
  };
}

interface WaveExecutionResult {
  WaveId: string;
  WaveName: string;
  Status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMEOUT';
  StartTime: number;
  EndTime?: number;
  Duration?: number;
  PreWaveActionResults: ActionExecutionResult[];
  DRSJobId?: string;
  DRSJobStatus?: string;
  RecoveredInstances: RecoveredInstance[];
  PostWaveActionResults: ActionExecutionResult[];
  Logs: string[];
}

interface ActionExecutionResult {
  ActionId: string;
  ActionName: string;
  Status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMEOUT';
  StartTime: number;
  EndTime?: number;
  Duration?: number;
  SSMExecutionId?: string;
  SSMExecutionStatus?: string;
  Output?: Record<string, any>;
  ErrorMessage?: string;
}

interface RecoveredInstance {
  SourceServerId: string;
  RecoveredInstanceId: string;
  RecoveredInstanceState: string;
  LaunchTime: number;
  PrivateIpAddress?: string;
  PublicIpAddress?: string;
}
```

### Step Functions State Machine Types

**State Machine Input:**
```typescript
interface StepFunctionsInput {
  ExecutionType: 'DRILL' | 'RECOVERY' | 'FAILBACK';
  PlanId: string;
  InitiatedBy: string;
  TopicArn?: string;
  DryRun?: boolean;
}
```

**State Machine Context:**
```typescript
interface ExecutionContext {
  ExecutionId: string;
  PlanId: string;
  Plan: RecoveryPlan;
  CurrentWaveIndex: number;
  WaveResults: WaveExecutionResult[];
  Status: 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMEOUT';
  ErrorDetails?: {
    ErrorType: string;
    ErrorMessage: string;
  };
}
```

### API Gateway Request/Response Types

**Create Protection Group Request:**
```typescript
interface CreateProtectionGroupRequest {
  GroupName: string;
  Description: string;
  Tags: {
    KeyName: string;
    KeyValue: string;
  };
  AccountId: string;
  Region: string;
  Owner: string;
}
```

**Create Recovery Plan Request:**
```typescript
interface CreateRecoveryPlanRequest {
  PlanName: string;
  Description: string;
  AccountId: string;
  Region: string;
  Owner: string;
  RPO: number;
  RTO: number;
}
```

**Execute Recovery Plan Request:**
```typescript
interface ExecuteRecoveryPlanRequest {
  PlanId: string;
  ExecutionType: 'DRILL' | 'RECOVERY' | 'FAILBACK';
  TopicArn?: string;
  DryRun?: boolean;
}
```

## Files

Organize solution into master template with strategic nested stacks and supporting assets for Lambda, frontend, SSM documents, and deployment scripts.

### New Files to Create

**CloudFormation Templates:**
- `AWS-DRS-Orchestration/cfn/master-template.yaml` - Main CloudFormation template containing DynamoDB tables, API Gateway, Cognito, Step Functions, CloudFront, S3 bucket, IAM roles, SSM documents, and custom resources. References nested stacks for Lambda and frontend deployment.
- `AWS-DRS-Orchestration/cfn/lambda-stack.yaml` - AWS SAM-based nested stack containing all Lambda functions with automatic code packaging. Includes API Lambda, orchestration Lambda, custom resource Lambda, and frontend build Lambda.
- `AWS-DRS-Orchestration/cfn/frontend-build-stack.yaml` - Nested stack with custom resource Lambda that builds React application, uploads to S3, and invalidates CloudFront cache.

**Lambda Function Source Code:**
- `AWS-DRS-Orchestration/lambda/api-handler/index.py` - API Gateway request handler implementing REST endpoints for Protection Groups, Recovery Plans, Waves, and execution management. Uses boto3 for DynamoDB operations and Step Functions execution.
- `AWS-DRS-Orchestration/lambda/api-handler/requirements.txt` - Python dependencies (boto3>=1.34.0).
- `AWS-DRS-Orchestration/lambda/orchestration/drs_orchestrator.py` - Step Functions Lambda implementing wave execution logic, DRS API calls (StartRecovery), instance health checks, and SSM automation coordination.
- `AWS-DRS-Orchestration/lambda/orchestration/requirements.txt` - Python dependencies (boto3>=1.34.0).
- `AWS-DRS-Orchestration/lambda/custom-resources/s3_cleanup.py` - Custom resource Lambda for emptying S3 bucket on stack deletion to enable clean removal.
- `AWS-DRS-Orchestration/lambda/custom-resources/requirements.txt` - Python dependencies (boto3>=1.34.0, crhelper>=2.0.0).
- `AWS-DRS-Orchestration/lambda/frontend-builder/build_and_deploy.py` - Custom resource Lambda that runs npm install/build for React app and uploads to S3.
- `AWS-DRS-Orchestration/lambda/frontend-builder/requirements.txt` - Python dependencies (boto3>=1.34.0, crhelper>=2.0.0).

**React Frontend Application:**
- `AWS-DRS-Orchestration/frontend/package.json` - React application dependencies including React 18.3+, Material-UI 6+, AWS Amplify 6+, React Hook Form 7+, React Router 7+.
- `AWS-DRS-Orchestration/frontend/src/index.js` - Application entry point with Amplify configuration and React root rendering.
- `AWS-DRS-Orchestration/frontend/src/App.js` - Main application component with routing, authentication, and layout.
- `AWS-DRS-Orchestration/frontend/src/aws-exports.js` - Amplify configuration template (populated by CloudFormation outputs).
- `AWS-DRS-Orchestration/frontend/src/components/ProtectionGroups.jsx` - Protection Group management UI component with create/edit/delete operations and DRS source server listing.
- `AWS-DRS-Orchestration/frontend/src/components/RecoveryPlans.jsx` - Recovery Plan management UI component with plan builder, wave configuration, and dependency mapping.
- `AWS-DRS-Orchestration/frontend/src/components/ExecutionDashboard.jsx` - Real-time execution status dashboard with wave progress, logs, and historical executions.
- `AWS-DRS-Orchestration/frontend/src/components/WaveBuilder.jsx` - Wave configuration UI for adding servers, configuring actions, and setting dependencies.
- `AWS-DRS-Orchestration/frontend/src/api/client.js` - API Gateway client using Amplify API module with Cognito authentication.
- `AWS-DRS-Orchestration/frontend/src/theme.js` - Material-UI theme configuration.
- `AWS-DRS-Orchestration/frontend/public/index.html` - HTML template.

**SSM Documents:**
- `AWS-DRS-Orchestration/ssm-documents/post-launch-health-check.yaml` - SSM Document for post-recovery health validation (OS-agnostic: Bash for Linux, PowerShell for Windows).
- `AWS-DRS-Orchestration/ssm-documents/application-startup.yaml` - SSM Document for starting application services post-recovery.
- `AWS-DRS-Orchestration/ssm-documents/network-validation.yaml` - SSM Document for validating network connectivity and DNS resolution.

**Deployment and Testing:**
- `AWS-DRS-Orchestration/deploy.sh` - Bash script to package Lambda functions, build frontend (optional pre-build), and deploy CloudFormation stack with parameter prompts.
- `AWS-DRS-Orchestration/parameters.json` - CloudFormation parameter file template with placeholders for required values.
- `AWS-DRS-Orchestration/README.md` - Comprehensive documentation covering prerequisites, deployment steps, configuration, usage, and troubleshooting.

**Testing Assets:**
- `AWS-DRS-Orchestration/tests/unit/test_api_handler.py` - Unit tests for API Lambda handler with mocked DynamoDB/Step Functions.
- `AWS-DRS-Orchestration/tests/unit/test_orchestrator.py` - Unit tests for orchestration Lambda with mocked DRS API.
- `AWS-DRS-Orchestration/tests/integration/test_api_endpoints.py` - Integration tests for API Gateway endpoints with test Cognito user.
- `AWS-DRS-Orchestration/tests/integration/test_step_functions.py` - Integration tests for Step Functions execution with mock DRS servers.
- `AWS-DRS-Orchestration/tests/e2e/test_complete_recovery.py` - End-to-end test executing complete recovery plan with real DRS source servers.
- `AWS-DRS-Orchestration/tests/fixtures/sample_protection_group.json` - Sample Protection Group data for testing.
- `AWS-DRS-Orchestration/tests/fixtures/sample_recovery_plan.json` - Sample Recovery Plan with multiple waves.

### Existing Files to Modify

None - this is a greenfield implementation with no existing files to modify.

### Files to Delete or Move

None - no cleanup required as this is a new implementation.

### Configuration File Updates

None initially - all configuration is managed through CloudFormation parameters.

## Functions

Define all Lambda functions, Step Functions states, and utility functions required for the solution.

### New Functions

**API Handler Lambda (`api-handler/index.py`):**

- `lambda_handler(event, context)` - Main entry point for API Gateway requests, routes to appropriate handler based on HTTP method and path (POST /protection-groups, GET /protection-groups, PUT /protection-groups/{id}, DELETE /protection-groups/{id}, etc.).
- `create_protection_group(body)` - Validates request, generates GroupId UUID, queries DRS DescribeSourceServers API to validate servers exist with specified tags, stores to DynamoDB ProtectionGroups table, returns created group.
- `get_protection_groups()` - Scans DynamoDB ProtectionGroups table, enriches with current DRS source server status, returns array of groups.
- `get_protection_group(group_id)` - Retrieves single Protection Group from DynamoDB, enriches with DRS source server details, returns group object.
- `update_protection_group(group_id, body)` - Updates Protection Group in DynamoDB, validates no server conflicts with other groups, returns updated group.
- `delete_protection_group(group_id)` - Validates group not referenced in active plans, deletes from DynamoDB, returns success status.
- `create_recovery_plan(body)` - Validates request, generates PlanId UUID, stores to DynamoDB RecoveryPlans table with empty Waves array, returns created plan.
- `get_recovery_plans()` - Scans DynamoDB RecoveryPlans table, returns array of plans with wave counts.
- `get_recovery_plan(plan_id)` - Retrieves single Recovery Plan from DynamoDB with full wave details, returns plan object.
- `update_recovery_plan(plan_id, body)` - Updates Recovery Plan in DynamoDB including waves configuration, validates wave dependencies are acyclic, returns updated plan.
- `delete_recovery_plan(plan_id)` - Validates no active executions, deletes from DynamoDB, returns success status.
- `execute_recovery_plan(body)` - Validates plan exists and has waves, generates ExecutionId, creates ExecutionHistory record, starts Step Functions execution with plan details, returns execution ARN.
- `get_execution_history(plan_id)` - Queries DynamoDB ExecutionHistory table by PlanId, returns sorted array of historical executions.
- `get_execution_status(execution_id)` - Queries Step Functions DescribeExecution and DynamoDB ExecutionHistory, returns current execution state with wave progress.
- `list_drs_source_servers(account_id, region)` - Assumes cross-account role, calls DRS DescribeSourceServers API, returns filtered array of source servers with replication status.

**Orchestration Lambda (`orchestration/drs_orchestrator.py`):**

- `lambda_handler(event, context)` - Main entry point called by Step Functions, routes to appropriate handler based on action type (BEGIN, EXECUTE_WAVE, UPDATE_WAVE_STATUS, EXECUTE_ACTION, UPDATE_ACTION_STATUS, COMPLETE).
- `begin_execution(event)` - Initializes execution context, retrieves full Recovery Plan from DynamoDB, validates all Protection Groups exist, creates initial ExecutionHistory record, returns context with first wave ready.
- `execute_wave(event)` - Processes current wave from context, executes PreWaveActions sequentially, initiates DRS StartRecovery job for Protection Group servers, initializes WaveExecutionResult, returns context with wave in progress.
- `update_wave_status(event)` - Polls DRS DescribeRecoveryJobs API for job status, checks EC2 instance states for recovered instances, evaluates wave dependencies and health checks, updates WaveExecutionResult, returns context with completion status.
- `execute_action(event)` - Executes single AutomationAction (PreWave or PostWave), starts SSM Automation execution with configured parameters, creates ActionExecutionResult, returns context with action in progress.
- `update_action_status(event)` - Polls SSM DescribeAutomationExecutions API for status, retrieves output parameters, updates ActionExecutionResult, returns context with completion status.
- `complete_execution(event)` - Aggregates all wave results, calculates total duration, updates final ExecutionHistory record in DynamoDB, sends SNS notification if TopicArn provided, returns final execution summary.
- `check_wave_dependencies(wave, context)` - Evaluates all WaveDependency conditions, checks prerequisite wave completion states, validates instance health for HEALTHY dependencies, returns boolean ready status.
- `check_instance_health(instance_id, health_check_type)` - Performs EC2 status checks or runs custom SSM health check script, returns boolean health status.
- `assume_cross_account_role(account_id, role_name)` - Uses STS AssumeRole to get temporary credentials for target account, returns boto3 client configured with assumed role.
- `start_drs_recovery(source_server_ids, is_drill, account_id, region)` - Calls DRS StartRecovery API with array of source servers and drill flag, returns job ID and tracks ParticipatingServers.
- `send_execution_notification(execution_id, status, topic_arn)` - Publishes formatted message to SNS topic with execution details, wave results, and dashboard link.

**Custom Resource Lambda (`custom-resources/s3_cleanup.py`):**

- `lambda_handler(event, context)` - CloudFormation custom resource handler, routes to appropriate function based on RequestType (Create, Update, Delete).
- `handle_create(event)` - No-op for Create operation, returns success to CloudFormation.
- `handle_update(event)` - No-op for Update operation, returns success to CloudFormation.
- `handle_delete(event)` - Empties S3 bucket specified in ResourceProperties, deletes all objects and versions, returns success to CloudFormation to unblock stack deletion.
- `empty_bucket(bucket_name)` - Lists all objects and versions in bucket, deletes in batches of 1000, handles errors gracefully.

**Frontend Builder Lambda (`frontend-builder/build_and_deploy.py`):**

- `lambda_handler(event, context)` - CloudFormation custom resource handler for React build and deployment.
- `handle_create(event)` - Extracts React source from embedded zip or S3 location, runs npm install, runs npm build with environment variables from ResourceProperties (API endpoint, Cognito pool ID), uploads build artifacts to S3, invalidates CloudFront distribution, returns success.
- `handle_update(event)` - Same as handle_create, rebuilds and redeploys frontend with updated configuration.
- `handle_delete(event)` - No-op, returns success (bucket cleanup handled by s3_cleanup custom resource).
- `build_react_app(source_dir, env_vars)` - Runs npm commands in subprocess, captures output, raises exception on failure.
- `upload_to_s3(build_dir, bucket_name)` - Recursively uploads all files from build directory to S3 with correct content types.
- `invalidate_cloudfront(distribution_id)` - Creates CloudFront invalidation for /* path, waits for completion.

### Modified Functions

None - this is a greenfield implementation with no existing functions to modify.

### Removed Functions

None - no functions to remove as this is a new implementation.

## Classes

Define all class structures for React components, Python handlers, and data models.

### New Classes

**React Component Classes (`frontend/src/components/`):**

- `ProtectionGroupsList` - React functional component rendering table of Protection Groups with Material-UI DataGrid, implements filtering, sorting, and row actions (edit, delete). Props: `groups: DRProtectionGroup[]`, `onEdit: (group) => void`, `onDelete: (group) => void`, `onRefresh: () => void`.
- `ProtectionGroupForm` - React functional component with Material-UI form for creating/editing Protection Groups, implements React Hook Form validation, DRS source server selection with tag filtering. Props: `group?: DRProtectionGroup`, `onSave: (group) => void`, `onCancel: () => void`.
- `RecoveryPlansList` - React functional component rendering table of Recovery Plans with wave count badges, implements filtering, sorting, row actions. Props: `plans: RecoveryPlan[]`, `onEdit: (plan) => void`, `onDelete: (plan) => void`, `onExecute: (plan) => void`, `onRefresh: () => void`.
- `RecoveryPlanForm` - React functional component with multi-step wizard for creating/editing Recovery Plans, manages plan metadata in step 1, wave configuration in step 2. Props: `plan?: RecoveryPlan`, `onSave: (plan) => void`, `onCancel: () => void`.
- `WaveConfigurationPanel` - React functional component for adding/editing waves within Recovery Plan, manages wave order, Protection Group selection, action configuration. Props: `waves: Wave[]`, `protectionGroups: DRProtectionGroup[]`, `onChange: (waves) => void`.
- `WaveDependencyBuilder` - React functional component with visual dependency graph, allows clicking waves to add dependencies, shows dependency validation errors. Props: `waves: Wave[]`, `onChange: (waves) => void`.
- `AutomationActionForm` - React functional component for configuring PreWave/PostWave actions, implements SSM document selection, parameter configuration. Props: `action?: AutomationAction`, `onSave: (action) => void`, `onCancel: () => void`.
- `ExecutionDashboard` - React functional component with real-time execution status, implements WebSocket or polling for live updates, displays wave progress bars. Props: `executionId: string`.
- `ExecutionHistoryTable` - React functional component rendering historical executions with filtering by date range, status. Props: `planId?: string`, `onViewDetails: (execution) => void`.
- `WaveExecutionTimeline` - React functional component with Material-UI Timeline showing wave execution sequence, action results, instance recovery status. Props: `execution: ExecutionHistory`.

**Python Data Model Classes (`lambda/common/models.py`):**

- `ProtectionGroupModel` - Python dataclass representing Protection Group with validation methods (`validate_servers_exist()`, `validate_no_conflicts()`), DynamoDB serialization methods (`to_dynamodb_item()`, `from_dynamodb_item(item)`).
- `RecoveryPlanModel` - Python dataclass representing Recovery Plan with validation methods (`validate_waves()`, `validate_dependencies()`), wave ordering logic (`get_ordered_waves()`), DynamoDB serialization methods.
- `WaveModel` - Python dataclass representing Wave with dependency evaluation methods (`check_dependencies_met(context)`, `get_prerequisite_waves()`), DynamoDB serialization methods.
- `ExecutionHistoryModel` - Python dataclass representing execution state with result aggregation methods (`add_wave_result()`, `calculate_summary_stats()`), DynamoDB serialization methods.

**Python Helper Classes (`lambda/common/`):**

- `DRSClient` - Wrapper class for AWS DRS API calls with cross-account role assumption, retry logic, error handling. Methods: `list_source_servers(tags)`, `start_recovery(server_ids, is_drill)`, `describe_recovery_job(job_id)`, `get_launch_configuration(server_id)`.
- `SSMClient` - Wrapper class for AWS SSM API calls with automation execution, document management. Methods: `start_automation(document, parameters, targets)`, `describe_automation(execution_id)`, `get_document_parameters(document)`.
- `DynamoDBClient` - Wrapper class for DynamoDB operations with query/scan pagination, batch operations. Methods: `put_item(table, item)`, `get_item(table, key)`, `query_items(table, key_condition)`, `scan_table(table, filter_expression)`, `delete_item(table, key)`.

### Modified Classes

None - this is a greenfield implementation with no existing classes to modify.

### Removed Classes

None - no classes to remove as this is a new implementation.

## Dependencies

Specify all external packages, AWS services, and version requirements for Lambda functions and React frontend.

### Lambda Function Dependencies

**API Handler Lambda (`lambda/api-handler/requirements.txt`):**
```
boto3>=1.34.0
botocore>=1.34.0
```

**Orchestration Lambda (`lambda/orchestration/requirements.txt`):**
```
boto3>=1.34.0
botocore>=1.34.0
```

**Custom Resource Lambda (`lambda/custom-resources/requirements.txt`):**
```
boto3>=1.34.0
botocore>=1.34.0
crhelper>=2.0.0
```

**Frontend Builder Lambda (`lambda/frontend-builder/requirements.txt`):**
```
boto3>=1.34.0
botocore>=1.34.0
crhelper>=2.0.0
```

### React Frontend Dependencies

**Package.json main dependencies:**
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^7.0.0",
    "@mui/material": "^6.0.0",
    "@mui/icons-material": "^6.0.0",
    "@emotion/react": "^11.13.0",
    "@emotion/styled": "^11.13.0",
    "aws-amplify": "^6.0.0",
    "@aws-amplify/ui-react": "^6.0.0",
    "react-hook-form": "^7.50.0",
    "@mui/x-data-grid": "^7.0.0",
    "recharts": "^2.10.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.0.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.35.0"
  }
}
```

### AWS Service Dependencies

**Core Services (all latest versions):**
- AWS CloudFormation - Infrastructure deployment and lifecycle management
- Amazon DynamoDB - Serverless NoSQL database for Protection Groups, Recovery Plans, Execution History
- AWS Lambda - Serverless compute for API handlers, orchestration, custom resources (Python 3.12 runtime)
- AWS Step Functions - Workflow orchestration for recovery plan execution (Standard workflows)
- Amazon API Gateway - REST API endpoints with CORS, throttling, Cognito authorization
- Amazon Cognito - User authentication and authorization (User Pools and Identity Pools)
- Amazon S3 - Static website hosting for React frontend, Lambda deployment packages
- Amazon CloudFront - CDN for frontend distribution with HTTPS, custom domain support
- AWS Systems Manager (SSM) - Post-launch automation, parameter store for configuration
- Amazon SNS - Execution notifications and alerts
- Amazon CloudWatch - Logs, metrics, and alarms for observability
- AWS IAM - Roles and policies for service authentication and authorization
- AWS Key Management Service (KMS) - Encryption for DynamoDB, S3, CloudWatch Logs

**Cross-Account Integration:**
- AWS Security Token Service (STS) - Cross-account role assumption for DRS operations
- AWS Organizations - Optional for organizational deployment

### Integration Requirements

**DRS API Integration:**
- AWS DRS service must be initialized in target region before deployment
- Source servers must have DRS agents installed and replicating
- Cross-account IAM role required in DRS accounts (created by solution)

**SSM Integration:**
- SSM Agent must be installed on source servers (pre-installed on most AMIs)
- SSM Documents deployed by CloudFormation template
- Systems Manager Session Manager for secure instance access

**Cognito Integration:**
- Email verification enabled for user registration (optional)
- Multi-factor authentication configurable post-deployment
- Social identity providers configurable if needed (Google, Facebook, etc.)

## Testing

Comprehensive testing strategy covering unit, integration, and end-to-end testing for each implementation phase.

### Phase 1 Testing (Infrastructure & Data Layer)

**Test Objective:** Validate CloudFormation deployment, DynamoDB schema, Lambda functions, and Step Functions orchestration without frontend dependencies.

**Prerequisites:**
- AWS account with appropriate IAM permissions for CloudFormation, Lambda, DynamoDB, Step Functions, SSM
- AWS CLI configured with credentials
- Python 3.12+ installed locally for unit testing
- pytest and moto libraries installed (`pip install pytest moto boto3`)

**Unit Tests for Lambda Functions:**

Test file: `tests/unit/test_api_handler.py`
```python
# Test cases:
- test_create_protection_group_success() - Validates UUID generation, DynamoDB put_item call
- test_create_protection_group_invalid_tags() - Validates input validation
- test_get_protection_groups_empty() - Validates empty table handling
- test_update_protection_group_not_found() - Validates error handling
- test_delete_protection_group_in_use() - Validates referential integrity check
```

Test file: `tests/unit/test_orchestrator.py`
```python
# Test cases:
- test_begin_execution_valid_plan() - Validates plan retrieval and context initialization
- test_execute_wave_with_actions() - Validates PreWave action execution
- test_update_wave_status_complete() - Validates DRS job polling logic
- test_check_wave_dependencies_met() - Validates dependency evaluation
- test_check_instance_health_running() - Validates health check logic
```

**Execution Commands:**
```bash
# Run unit tests
cd AWS-DRS-Orchestration/tests
pytest unit/ -v --cov=../../lambda --cov-report=html

# Expected results: All tests pass with >80% code coverage
```

**CloudFormation Deployment Test:**

1. Validate template syntax:
```bash
aws cloudformation validate-template --template-body file://cfn/master-template.yaml
aws cloudformation validate-template --template-body file://cfn/lambda-stack.yaml
aws cloudformation validate-template --template-body file://cfn/frontend-build-stack.yaml
```

2. Deploy master stack:
```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-test \
  --template-body file://cfn/master-template.yaml \
  --parameters file://parameters.json \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --region us-west-2
```

3. Monitor deployment:
```bash
aws cloudformation wait stack-create-complete --stack-name drs-orchestration-test
aws cloudformation describe-stacks --stack-name drs-orchestration-test
```

4. Verify resources created:
```bash
# Check DynamoDB tables
aws dynamodb list-tables | grep drs-orchestration

# Check Lambda functions
aws lambda list-functions | grep drs-orchestration

# Check Step Functions state machine
aws stepfunctions list-state-machines | grep drs-orchestration
```

**Expected Results:**
- All CloudFormation stacks reach CREATE_COMPLETE status
- 3 DynamoDB tables created: ProtectionGroups, RecoveryPlans, ExecutionHistory
- 4 Lambda functions deployed: api-handler, orchestration, s3-cleanup, frontend-builder
- 1 Step Functions state machine created
- All resources properly tagged with stack identifiers

**DynamoDB Schema Validation:**

1. Test Protection Group CRUD:
```bash
# Create test item
aws dynamodb put-item --table-name drs-orchestration-protection-groups \
  --item file://tests/fixtures/sample_protection_group.json

# Read item
aws dynamodb get-item --table-name drs-orchestration-protection-groups \
  --key '{"GroupId":{"S":"test-uuid-123"}}'

# Scan table
aws dynamodb scan --table-name drs-orchestration-protection-groups
```

2. Test Recovery Plan CRUD:
```bash
# Create test plan
aws dynamodb put-item --table-name drs-orchestration-recovery-plans \
  --item file://tests/fixtures/sample_recovery_plan.json
```

**Expected Results:**
- Items successfully stored and retrieved
- Schema validation passes for all fields
- Proper JSON serialization/deserialization

**Step Functions Execution Test:**

1. Start test execution with mock plan data:
```bash
aws stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-west-2:123456789012:stateMachine:drs-orchestration-sm \
  --input file://tests/fixtures/test_execution_input.json
```

2. Monitor execution:
```bash
aws stepfunctions describe-execution \
  --execution-arn <execution-arn-from-step-1>
```

3. Retrieve execution history:
```bash
aws stepfunctions get-execution-history \
  --execution-arn <execution-arn>
```

**Expected Results:**
- State machine execution starts successfully
- Lambda functions invoked in correct sequence
- Execution completes or fails with proper error handling
- ExecutionHistory DynamoDB table populated

**Acceptance Criteria Phase 1:**
- [ ] CloudFormation template validates without errors
- [ ] All AWS resources deploy successfully
- [ ] DynamoDB tables have correct schema and indexes
- [ ] Lambda functions execute without errors
- [ ] Step Functions state machine validates and executes
- [ ] IAM roles have least privilege permissions
- [ ] CloudWatch Logs capture all Lambda output
- [ ] Unit tests achieve >80% code coverage

### Phase 2 Testing (API & Integration Layer)

**Test Objective:** Validate API Gateway endpoints, Cognito authentication, SSM document execution, and cross-account role assumption.

**Prerequisites:**
- Phase 1 completed and validated
- Test Cognito user created with verified email
- At least one DRS source server available for testing
- SSM Agent installed and running on test instances

**API Gateway Integration Tests:**

Test file: `tests/integration/test_api_endpoints.py`
```python
# Test cases:
- test_create_protection_group_authenticated() - POST with Cognito token
- test_list_protection_groups_authenticated() - GET with Cognito token
- test_update_protection_group_authorized() - PUT with owner verification
- test_delete_protection_group_authorized() - DELETE with owner verification
- test_unauthorized_access_returns_401() - Request without token
- test_cors_headers_present() - Validates CORS configuration
```

**Execution Commands:**
```bash
# Get Cognito user token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <cognito-client-id> \
  --auth-parameters USERNAME=test@example.com,PASSWORD=TestPass123!

# Test API endpoints with token
export API_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

export AUTH_TOKEN="<token-from-cognito>"

# Test create Protection Group
curl -X POST ${API_ENDPOINT}/protection-groups \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_protection_group_request.json

# Test list Protection Groups
curl -X GET ${API_ENDPOINT}/protection-groups \
  -H "Authorization: Bearer ${AUTH_TOKEN}"

# Test create Recovery Plan
curl -X POST ${API_ENDPOINT}/recovery-plans \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_recovery_plan_request.json
```

**Expected Results:**
- 200 OK for successful operations
- 401 Unauthorized for requests without token
- 403 Forbidden for unauthorized resource access
- Proper JSON response bodies
- CORS headers present in all responses

**Cognito Authentication Flow Test:**

1. Register new user:
```bash
aws cognito-idp sign-up \
  --client-id <cognito-client-id> \
  --username ***REMOVED*** \
  --password TestPass123! \
  --user-attributes Name=email,Value=***REMOVED***
```

2. Confirm user (admin action):
```bash
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id <user-pool-id> \
  --username ***REMOVED***
```

3. Authenticate and get tokens:
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <cognito-client-id> \
  --auth-parameters USERNAME=***REMOVED***,PASSWORD=TestPass123!
```

**Expected Results:**
- User registration succeeds
- Email verification works (if enabled)
- Authentication returns IdToken, AccessToken, RefreshToken
- Tokens validate correctly with API Gateway

**SSM Document Execution Test:**

1. List available SSM documents:
```bash
aws ssm list-documents --filters Key=Owner,Values=Self
```

2. Execute health check document:
```bash
aws ssm start-automation-execution \
  --document-name drs-orchestration-health-check \
  --parameters '{"InstanceId":["i-1234567890abcdef0"]}'
```

3. Monitor execution:
```bash
aws ssm describe-automation-executions \
  --filters Key=ExecutionId,Values=<execution-id>
```

4. Get execution output:
```bash
aws ssm get-automation-execution \
  --automation-execution-id <execution-id>
```

**Expected Results:**
- SSM documents successfully created by CloudFormation
- Documents execute on target instances
- Output parameters captured correctly
- Execution completes with Success status

**Cross-Account Role Assumption Test:**

1. Create test role in DRS account:
```bash
# In DRS account
aws iam create-role \
  --role-name drs-orchestration-cross-account-role \
  --assume-role-policy-document file://tests/fixtures/trust_policy.json

aws iam attach-role-policy \
  --role-name drs-orchestration-cross-account-role \
  --policy-arn arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryRecoveryInstanceRole
```

2. Test role assumption from orchestration Lambda:
```python
# In test script
import boto3

sts_client = boto3.client('sts')
assumed_role = sts_client.assume_role(
    RoleArn='arn:aws:iam::123456789012:role/drs-orchestration-cross-account-role',
    RoleSessionName='test-session'
)

drs_client = boto3.client(
    'drs',
    aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
    aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
    aws_session_token=assumed_role['Credentials']['SessionToken']
)

# Test DRS API call
response = drs_client.describe_source_servers()
```

**Expected Results:**
- Role assumption succeeds
- Temporary credentials work for DRS API calls
- Proper error handling for expired credentials

**Acceptance Criteria Phase 2:**
- [ ] All API endpoints return correct HTTP status codes
- [ ] Cognito authentication flow works end-to-end
- [ ] API Gateway properly validates Cognito tokens
- [ ] CORS configuration allows frontend access
- [ ] SSM documents execute successfully on target instances
- [ ] Cross-account role assumption works correctly
- [ ] DRS API calls succeed with assumed role
- [ ] API rate limiting and throttling configured
- [ ] CloudWatch Logs capture all API requests

### Phase 3 Testing (Frontend & Complete Integration)

**Test Objective:** Validate React frontend, end-to-end user workflows, real DRS recovery execution, and complete system integration.

**Prerequisites:**
- Phase 1 and Phase 2 completed and validated
- At least 2 DRS source servers with different tags for multi-wave testing
- CloudFront distribution deployed and accessible
- Cognito user created for UI testing

**React Component Unit Tests:**

Test file: `tests/frontend/ProtectionGroups.test.jsx`
```javascript
// Test cases:
- test_renders_protection_groups_list() - Component renders correctly
- test_create_protection_group_form_validation() - Form validation works
- test_edit_protection_group_updates_data() - Edit operation updates state
- test_delete_protection_group_confirmation() - Delete requires confirmation
- test_drs_source_server_selection() - Server selection from API data
```

**Execution Commands:**
```bash
cd AWS-DRS-Orchestration/frontend
npm test -- --coverage --watchAll=false
```

**Expected Results:**
- All React component tests pass
- Test coverage >70% for components
- No console errors or warnings

**Frontend Build and Deployment Test:**

1. Test local build:
```bash
cd frontend
npm install
npm run build

# Verify build output
ls -la dist/
```

2. Test CloudFront deployment:
```bash
# Get CloudFront URL
export CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name drs-orchestration-test \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text)

# Test access
curl -I ${CLOUDFRONT_URL}
```

**Expected Results:**
- Build completes without errors
- All assets generated in dist/ directory
- CloudFront returns 200 OK
- HTTPS certificate valid

**End-to-End User Workflow Tests:**

Test file: `tests/e2e/test_complete_workflow.py` (using Selenium or Playwright)

**Test Case 1: Create Protection Group**
1. Navigate to CloudFront URL
2. Log in with test Cognito user
3. Click "Create Protection Group"
4. Fill form with test data
5. Select DRS source servers by tag filter
6. Save Protection Group
7. Verify group appears in list

**Test Case 2: Create Recovery Plan**
1. Navigate to Recovery Plans page
2. Click "Create Recovery Plan"
3. Fill plan metadata (name, RPO, RTO)
4. Add Wave 1: Select Protection Group A
5. Configure PreWave action (health check SSM doc)
6. Add Wave 2: Select Protection Group B
7. Configure dependency: Wave 2 waits for Wave 1
8. Configure PostWave action (startup SSM doc)
9. Save Recovery Plan
10. Verify plan appears with 2 waves

**Test Case 3: Execute Recovery Drill**
1. Navigate to Recovery Plans page
2. Select test plan
3. Click "Execute Drill"
4. Confirm execution
5. Navigate to Execution Dashboard
6. Verify real-time wave progress updates
7. Verify PreWave actions execute
8. Verify DRS recovery job starts
9. Verify instances launch successfully
10. Verify PostWave actions execute
11. Verify execution completes with Success status

**Expected Results:**
- All user interactions work without errors
- Data persists correctly between sessions
- Real-time updates display correctly
- Execution completes successfully

**Real DRS Recovery Integration Test:**

Prerequisites:
- 2 test source servers configured in DRS
- Source Server 1 tagged: Environment=Test, Tier=Database
- Source Server 2 tagged: Environment=Test, Tier=Application
- SSM Agent installed and running on source servers

**Execution Steps:**

1. Create Protection Groups via API:
```bash
# Create DB Protection Group
curl -X POST ${API_ENDPOINT}/protection-groups \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "GroupName": "Test-DB-Group",
    "Tags": {"KeyName": "Tier", "KeyValue": "Database"},
    "AccountId": "123456789012",
    "Region": "us-west-2"
  }'

# Create App Protection Group
curl -X POST ${API_ENDPOINT}/protection-groups \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "GroupName": "Test-App-Group",
    "Tags": {"KeyName": "Tier", "KeyValue": "Application"},
    "AccountId": "123456789012",
    "Region": "us-west-2"
  }'
```

2. Create Recovery Plan with dependencies:
```bash
curl -X POST ${API_ENDPOINT}/recovery-plans \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d @tests/fixtures/two_wave_recovery_plan.json
```

3. Execute drill:
```bash
curl -X POST ${API_ENDPOINT}/executions \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{
    "PlanId": "<plan-id-from-step-2>",
    "ExecutionType": "DRILL"
  }'
```

4. Monitor execution via Step Functions:
```bash
# Get execution ARN from API response
aws stepfunctions describe-execution --execution-arn <execution-arn>

# Watch for completion
while true; do
  STATUS=$(aws stepfunctions describe-execution \
    --execution-arn <execution-arn> \
    --query 'status' --output text)
  echo "Status: $STATUS"
  if [ "$STATUS" != "RUNNING" ]; then break; fi
  sleep 30
done
```

5. Verify recovered instances:
```bash
# List recovery instances
aws drs describe-recovery-instances

# Check instance states
aws ec2 describe-instances \
  --filters Name=tag:LaunchedBy,Values=DRS \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,Type:InstanceType}'
```

6. Verify SSM automation results:
```bash
# List recent automations
aws ssm describe-automation-executions \
  --filters Key=ExecutionStatus,Values=Success \
  --max-results 10

# Get specific automation output
aws ssm get-automation-execution \
  --automation-execution-id <execution-id> \
  --query 'AutomationExecution.Outputs'
```

**Expected Results:**
- Wave 1 (Database) executes first
- PreWave action completes successfully
- DRS recovery job launches database instance
- Database instance reaches running state
- Wave 2 (Application) waits for Wave 1 completion
- Wave 2 executes after Wave 1 succeeds
- Application instance launches successfully
- PostWave actions execute on recovered instances
- Execution History record created in DynamoDB
- CloudWatch Logs capture all execution details

**Performance and Load Testing:**

Test concurrent plan executions:
```bash
# Launch 5 concurrent drill executions
for i in {1..5}; do
  curl -X POST ${API_ENDPOINT}/executions \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -d "{\"PlanId\":\"$PLAN_ID\",\"ExecutionType\":\"DRILL\"}" &
done
wait
```

**Expected Results:**
- All executions start successfully
- No API throttling errors (or proper error handling)
- Step Functions handle concurrent executions
- DynamoDB handles concurrent writes
- CloudWatch Logs remain consistent

**Security Testing:**

1. Test unauthenticated access:
```bash
# Should return 401
curl -X GET ${API_ENDPOINT}/protection-groups
```

2. Test unauthorized resource access:
```bash
# User A tries to delete User B's Protection Group
curl -X DELETE ${API_ENDPOINT}/protection-groups/<user-b-group-id> \
  -H "Authorization: Bearer ${USER_A_TOKEN}"
# Should return 403
```

3. Test SQL injection (should be prevented by DynamoDB):
```bash
curl -X POST ${API_ENDPOINT}/protection-groups \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -d '{"GroupName":"test\"; DROP TABLE--"}'
```

4. Test XSS prevention in frontend:
```javascript
// Attempt to inject script in group name
const maliciousInput = '<script>alert("xss")</script>';
// Should be sanitized by React
```

**Expected Results:**
- Unauthenticated requests blocked
- Cross-user access denied
- Input validation prevents injection attacks
- Frontend sanitizes all user input

**Acceptance Criteria Phase 3:**
- [ ] React frontend builds and deploys successfully
- [ ] CloudFront serves frontend with HTTPS
- [ ] User can log in with Cognito
- [ ] All UI components render correctly
- [ ] Protection Groups CRUD operations work end-to-end
- [ ] Recovery Plans CRUD operations work end-to-end
- [ ] Wave dependencies configure correctly
- [ ] Real DRS drill executes successfully
- [ ] Multiple waves execute in correct sequence
- [ ] Wave dependencies honored (Wave 2 waits for Wave 1)
- [ ] SSM automations execute on recovered instances
- [ ] Execution Dashboard shows real-time progress
- [ ] Execution History displays correctly
- [ ] CloudWatch Logs capture all events
- [ ] Performance acceptable for 5 concurrent executions
- [ ] Security controls prevent unauthorized access
- [ ] No XSS or injection vulnerabilities

### Testing Documentation and Troubleshooting

**Common Issues and Solutions:**

**Issue 1: CloudFormation stack fails during Lambda deployment**
- Cause: Python dependencies not packaged correctly
- Solution: Run `pip install -r requirements.txt -t .` in Lambda directory before deploying
- Validation: Check Lambda console for runtime errors

**Issue 2: API Gateway returns 403 Forbidden**
- Cause: Cognito token missing or invalid
- Solution: Verify token not expired, check Cognito authorizer configuration
- Validation: Test with `aws cognito-idp initiate-auth` to get fresh token

**Issue 3: Step Functions execution times out**
- Cause: DRS recovery job taking longer than MaxWaitTime
- Solution: Increase MaxWaitTime in Wave configuration
- Validation: Check DRS job status in console

**Issue 4: SSM automation fails to run**
- Cause: SSM Agent not installed or instance role missing permissions
- Solution: Verify SSM Agent status, attach AmazonSSMManagedInstanceCore policy to instance role
- Validation: Run `aws ssm describe-instance-information`

**Issue 5: Frontend fails to build**
- Cause: Node version mismatch or missing dependencies
- Solution: Use Node.js 18+ and run `npm install`
- Validation: Check package.json engines field

**Issue 6: Cross-account role assumption fails**
- Cause: Trust policy not configured correctly
- Solution: Verify trust policy allows orchestration Lambda role to assume
- Validation: Test with `aws sts assume-role` CLI command

**Test Data Cleanup:**

After testing, clean up resources:
```bash
# Delete test Protection Groups
aws dynamodb scan --table-name drs-orchestration-protection-groups \
  --filter-expression "begins_with(GroupName, :prefix)" \
  --expression-attribute-values '{":prefix":{"S":"Test-"}}' \
  | jq -r '.Items[].GroupId.S' \
  | xargs -I {} aws dynamodb delete-item \
      --table-name drs-orchestration-protection-groups \
      --key '{"GroupId":{"S":"{}"}}'

# Terminate recovered test instances
aws ec2 describe-instances \
  --filters Name=tag:LaunchedBy,Values=DRS Name=tag:Environment,Values=Test \
  --query 'Reservations[].Instances[].InstanceId' \
  --output text \
  | xargs -I {} aws ec2 terminate-instances --instance-ids {}

# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name drs-orchestration-test
aws cloudformation wait stack-delete-complete --stack-name drs-orchestration-test
```

## Implementation Order

Numbered steps showing the logical order of implementation to minimize conflicts and ensure successful integration.

### Step 1: Project Structure and CloudFormation Templates

**Objective:** Establish project structure and create CloudFormation template skeleton.

**Tasks:**
1. Create directory structure for AWS-DRS-Orchestration project
2. Initialize git repository with .gitignore for Python, Node, AWS artifacts
3. Create `cfn/master-template.yaml` with Parameters section and basic outputs
4. Create `cfn/lambda-stack.yaml` SAM template with Transform declaration
5. Create `cfn/frontend-build-stack.yaml` nested stack template
6. Create `parameters.json` template with placeholder values
7. Add README.md with project overview and architecture diagram link

**Validation:**
- Run `aws cloudformation validate-template` on all templates
- Verify templates parse without syntax errors
- Commit initial structure to git

### Step 2: DynamoDB Tables and IAM Roles

**Objective:** Define data persistence layer and security roles.

**Tasks:**
1. Add DynamoDB ProtectionGroups table resource to master-template.yaml
2. Add DynamoDB RecoveryPlans table resource to master-template.yaml
3. Add DynamoDB ExecutionHistory table resource to master-template.yaml
4. Create IAM role for API Lambda with DynamoDB permissions
5. Create IAM role for Orchestration Lambda with DynamoDB, DRS, SSM, STS permissions
6. Create IAM role for Custom Resource Lambdas with S3 permissions
7. Add CloudWatch Logs permissions to all Lambda roles
8. Export table names and ARNs as CloudFormation outputs

**Validation:**
- Deploy CloudFormation stack with just DynamoDB and IAM resources
- Verify 3 tables created with correct schema
- Verify IAM roles created with least privilege policies
- Test table write with AWS CLI

### Step 3: API Handler Lambda Function

**Objective:** Implement REST API backend for Protection Groups and Recovery Plans.

**Tasks:**
1. Create `lambda/api-handler/index.py` with lambda_handler router
2. Implement create_protection_group() function
3. Implement get_protection_groups() function  
4. Implement get_protection_group(id) function
5. Implement update_protection_group() function
6. Implement delete_protection_group() function
7. Implement create_recovery_plan() function
8. Implement get_recovery_plans() function
9. Implement get_recovery_plan(id) function
10. Implement update_recovery_plan() function
11. Implement delete_recovery_plan() function
12. Implement execute_recovery_plan() function
13. Add error handling and input validation
14. Create requirements.txt with boto3 dependency
15. Write unit tests in `tests/unit/test_api_handler.py`

**Validation:**
- Run unit tests with pytest (>80% coverage)
- Add Lambda function to lambda-stack.yaml
- Deploy updated CloudFormation stack
- Test Lambda locally with `sam local invoke`
- Test Lambda in AWS console with sample events

### Step 4: API Gateway and Cognito

**Objective:** Expose Lambda functions as REST APIs with authentication.

**Tasks:**
1. Add Cognito User Pool resource to master-template.yaml
2. Add Cognito User Pool Client resource
3. Add Cognito Identity Pool resource
4. Add API Gateway REST API resource
5. Create API Gateway resources for /protection-groups endpoints
6. Create API Gateway resources for /recovery-plans endpoints
7. Create API Gateway resources for /executions endpoints
8. Add Cognito authorizer to API Gateway
9. Configure CORS for all API methods
10. Add API Gateway deployment and stage
11. Export API endpoint URL as CloudFormation output

**Validation:**
- Create test Cognito user
- Get authentication token
- Test API endpoints with curl and token
- Verify 401 without token
- Verify CORS headers present

### Step 5: Orchestration Lambda and Step Functions

**Objective:** Implement wave-based recovery orchestration logic.

**Tasks:**
1. Create `lambda/orchestration/drs_orchestrator.py` with handler router
2. Implement begin_execution() function
3. Implement execute_wave() function
4. Implement update_wave_status() function
5. Implement execute_action() function
6. Implement update_action_status() function
7. Implement complete_execution() function
8. Implement check_wave_dependencies() helper
9. Implement check_instance_health() helper
10. Implement assume_cross_account_role() helper
11. Implement start_drs_recovery() with DRS API calls
12. Implement send_execution_notification() with SNS
13. Add comprehensive error handling and retries
14. Create requirements.txt with boto3 dependency
15. Write unit tests in `tests/unit/test_orchestrator.py`
16. Add Step Functions state machine definition to master-template.yaml
17. Wire Lambda function to state machine tasks
18. Add SNS topic for notifications

**Validation:**
- Run unit tests with pytest (>80% coverage)
- Deploy updated CloudFormation stack
- Test Lambda locally with mock DRS responses
- Execute state machine with test input
- Verify execution completes successfully
- Check CloudWatch Logs for execution trace

### Step 6: SSM Documents

**Objective:** Create post-launch automation documents.

**Tasks:**
1. Create `ssm-documents/post-launch-health-check.yaml` with Linux and Windows commands
2. Create `ssm-documents/application-startup.yaml` for service startup
3. Create `ssm-documents/network-validation.yaml` for connectivity checks
4. Add SSM document resources to master-template.yaml
5. Add IAM permissions for document execution
6. Create test scripts to validate documents

**Validation:**
- Deploy SSM documents via CloudFormation
- List documents with AWS CLI
- Execute documents on test instance
- Verify output parameters captured
- Check execution logs in SSM console

### Step 7: Custom Resources for S3 and Frontend Build

**Objective:** Implement custom CloudFormation resources for deployment automation.

**Tasks:**
1. Create `lambda/custom-resources/s3_cleanup.py` with crhelper
2. Implement handle_delete() to empty S3 bucket
3. Create `lambda/frontend-builder/build_and_deploy.py`
4. Implement handle_create() to build React app
5. Implement upload_to_s3() to deploy built assets
6. Implement invalidate_cloudfront() for cache refresh
7. Add Lambda functions to lambda-stack.yaml
8. Create S3 bucket resource in master-template.yaml
9. Add CloudFront distribution resource
10. Add custom resource invocations
11. Create requirements.txt for both Lambdas with crhelper

**Validation:**
- Deploy updated CloudFormation stack
- Verify S3 bucket created
- Verify CloudFront distribution created
- Test stack deletion (bucket should empty automatically)
- Check custom resource Lambda logs

### Step 8: React Frontend Foundation

**Objective:** Create React application structure and build configuration.

**Tasks:**
1. Create `frontend/package.json` with React 18.3+ dependencies
2. Create `frontend/vite.config.js` for build configuration
3. Create `frontend/src/index.js` entry point
4. Create `frontend/src/App.js` with routing skeleton
5. Create `frontend/src/aws-exports.js` template for Amplify config
6. Create `frontend/src/theme.js` with Material-UI theme
7. Create `frontend/src/api/client.js` with API Gateway client
8. Create `frontend/public/index.html` template
9. Add authentication wrapper component
10. Add navigation and layout components

**Validation:**
- Run `npm install` successfully
- Run `npm run dev` for local development
- Verify app renders without errors
- Run `npm run build` successfully
- Check dist/ output directory

### Step 9: Protection Groups UI Components

**Objective:** Implement Protection Group management interface.

**Tasks:**
1. Create `frontend/src/components/ProtectionGroupsList.jsx`
2. Implement Material-UI DataGrid for list display
3. Add filtering and sorting capabilities
4. Create `frontend/src/components/ProtectionGroupForm.jsx`
5. Implement React Hook Form validation
6. Add DRS source server selection with tag filters
7. Implement API calls for CRUD operations
8. Add error handling and loading states
9. Create confirmation dialogs for delete operations
10. Write component unit tests

**Validation:**
- Test component rendering with npm test
- Test CRUD operations with real API
- Verify validation works correctly
- Check responsiveness on mobile
- Test accessibility with screen reader

### Step 10: Recovery Plans UI Components

**Objective:** Implement Recovery Plan management interface with wave builder.

**Tasks:**
1. Create `frontend/src/components/RecoveryPlansList.jsx`
2. Implement table with wave count badges
3. Create `frontend/src/components/RecoveryPlanForm.jsx` multi-step wizard
4. Create `frontend/src/components/WaveConfigurationPanel.jsx`
5. Implement wave ordering with drag-and-drop
6. Create `frontend/src/components/WaveDependencyBuilder.jsx`
7. Add visual dependency graph display
8. Create `frontend/src/components/AutomationActionForm.jsx`
9. Implement SSM document selection and parameter configuration
10. Add validation for dependency cycles
11. Implement API calls for plan CRUD operations
12. Write component unit tests

**Validation:**
- Test multi-step wizard navigation
- Test wave reordering functionality
- Test dependency graph visualization
- Verify cycle detection works
- Test plan save with multiple waves

### Step 11: Execution Dashboard Components

**Objective:** Implement real-time execution monitoring interface.

**Tasks:**
1. Create `frontend/src/components/ExecutionDashboard.jsx`
2. Implement polling for execution status updates
3. Add wave progress bars with percentage completion
4. Create `frontend/src/components/WaveExecutionTimeline.jsx`
5. Implement Material-UI Timeline for execution visualization
6. Add status indicators (running, success, failed)
7. Create `frontend/src/components/ExecutionHistoryTable.jsx`
8. Implement filtering by date range and status
9. Add execution detail modal
10. Implement CloudWatch Logs link integration
11. Write component unit tests

**Validation:**
- Test dashboard with active execution
- Verify polling updates display correctly
- Test timeline visualization
- Verify historical data loads
- Test filtering and sorting

### Step 12: End-to-End Integration Testing

**Objective:** Execute complete workflow tests with real AWS DRS integration.

**Tasks:**
1. Create test DRS source servers with appropriate tags
2. Install and configure SSM Agent on source servers
3. Create test Protection Groups via UI
4. Create test Recovery Plan with 2 waves
5. Configure wave dependencies
6. Add PreWave and PostWave SSM automations
7. Execute drill via UI
8. Monitor execution in real-time via dashboard
9. Verify DRS recovery job completes successfully
10. Verify instances launch and reach running state
11. Verify SSM automations execute on recovered instances
12. Verify execution history persists correctly
13. Run performance tests with concurrent executions
14. Run security tests (authentication, authorization, input validation)
15. Document any issues found and remediation steps

**Validation:**
- All end-to-end tests pass
- DRS drill completes successfully
- Multi-wave execution honors dependencies
- SSM automations execute correctly
- Performance acceptable under load
- Security controls prevent unauthorized access
- CloudWatch Logs capture complete audit trail

### Step 13: Documentation and Deployment Automation

**Objective:** Complete documentation and create simplified deployment scripts.

**Tasks:**
1. Create comprehensive README.md with:
   - Prerequisites and requirements
   - Architecture diagram
   - Deployment instructions
   - Configuration parameters
   - Usage examples
   - Troubleshooting guide
2. Create `deploy.sh` script:
   - Validate prerequisites (AWS CLI, Python, Node.js)
   - Prompt for required parameters
   - Package Lambda functions
   - Optionally build frontend locally
   - Deploy CloudFormation stack
   - Display outputs (API endpoint, CloudFront URL, Cognito pool ID)
3. Create `parameters.json` template with all required parameters
4. Add architecture diagrams to `docs/` directory
5. Create quick-start guide in `docs/quickstart.md`
6. Create troubleshooting guide in `docs/troubleshooting.md`
7. Add API documentation in `docs/api-reference.md`
8. Create example Recovery Plans in `examples/` directory
9. Add license and contributing guidelines
10. Create cleanup script `cleanup.sh` for removing test resources

**Validation:**
- Deploy solution using deploy.sh script
- Verify all parameters prompted correctly
- Verify deployment completes successfully
- Test documentation accuracy
- Verify quick-start guide works for new user
- Test cleanup script removes all resources

**Deployment Script Example (`deploy.sh`):**
```bash
#!/bin/bash
set -e

echo "AWS DRS Orchestration Solution Deployment"
echo "=========================================="

# Check prerequisites
command -v aws >/dev/null 2>&1 || { echo "AWS CLI required but not installed"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required but not installed"; exit 1; }

# Prompt for parameters
read -p "Enter Stack Name [drs-orchestration]: " STACK_NAME
STACK_NAME=${STACK_NAME:-drs-orchestration}

read -p "Enter Deployment Region [us-west-2]: " REGION
REGION=${REGION:-us-west-2}

read -p "Enter Admin Email: " ADMIN_EMAIL

read -p "Package Lambda functions? [y/N]: " PACKAGE_LAMBDA
if [[ $PACKAGE_LAMBDA =~ ^[Yy]$ ]]; then
    echo "Packaging Lambda functions..."
    for lambda_dir in lambda/*/; do
        if [ -f "$lambda_dir/requirements.txt" ]; then
            pip install -r "$lambda_dir/requirements.txt" -t "$lambda_dir" --upgrade
        fi
    done
fi

# Deploy stack
echo "Deploying CloudFormation stack..."
aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-body file://cfn/master-template.yaml \
    --parameters ParameterKey=AdminEmail,ParameterValue=$ADMIN_EMAIL \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --region $REGION

echo "Waiting for stack creation to complete..."
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION

# Get outputs
echo -e "\n=========================================="
echo "Deployment Complete!"
echo "=========================================="
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table

echo -e "\nNext Steps:"
echo "1. Check your email for Cognito temporary password"
echo "2. Access the UI at the CloudFront URL shown above"
echo "3. Create your first Protection Group"
echo "4. Create your first Recovery Plan"
echo "=========================================="
```

**Final Validation:**
- Deploy complete solution in fresh AWS account
- Validate all components work together
- Execute end-to-end recovery drill
- Verify documentation complete and accurate
- Test deployment script on clean environment
- Confirm cleanup script removes all resources
