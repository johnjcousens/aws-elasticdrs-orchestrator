p# Generic Orchestration Refactoring - Implementation Tasks

**Spec**: generic-orchestration-refactoring  
**Status**: Ready for Implementation  
**Created**: January 31, 2026  
**Last Updated**: February 3, 2026

---

## Overview

**PRIMARY OBJECTIVE**: Move 4 DRS-specific functions (~720 lines) from orchestration Lambda into existing handler Lambdas using a parallel Lambda strategy.

**Parallel Lambda Strategy**: Create NEW Lambda directory (`dr-orchestration-stepfunction`) alongside existing one for safe development. Keep original code intact as reference.

**Scope**: 
- Create new orchestration Lambda directory
- Move `start_wave_recovery()` + `apply_launch_config_before_recovery()` → execution-handler (~275 lines)
- Move `update_wave_status()` + `query_drs_servers_by_tags()` → query-handler (~445 lines)
- Update new orchestration to invoke handlers via boto3 Lambda client
- Add new Lambda resource to CloudFormation
- Update Step Functions to use new Lambda
- Keep all 3 handler Lambdas DRS-specific (no refactoring to generic)

**Success Criteria**:
- New orchestration Lambda has zero DRS API calls
- All existing DRS functionality preserved (zero regression)
- All tests pass (unit, integration, property-based)
- Code quality gates pass (black, flake8, bandit, cfn-lint)
- Deployment successful to test environment
- Easy rollback available (switch Step Functions ARN)

**Out of Scope**:
- Creating new adapter Lambdas
- Making handlers generic
- 4-phase lifecycle architecture
- Multi-technology support

---

## Task List

### 0. Create New Orchestration Lambda Directory

**Validates**: Requirements 1.0

- [x] 0.1 Create new Lambda directory structure
  - **Action**: Create `lambda/dr-orchestration-stepfunction/` directory
  - **Note**: No 's' at end (singular, not plural)

- [x] 0.2 Copy orchestration code to new directory
  - **Source**: `lambda/orchestration-stepfunctions/index.py`
  - **Destination**: `lambda/dr-orchestration-stepfunction/index.py`
  - **Action**: Complete copy of existing code

- [x] 0.3 Verify original directory unchanged
  - **Check**: `lambda/orchestration-stepfunctions/` still exists
  - **Check**: Original code unmodified
  - **Purpose**: Keep as reference during refactoring

### 1. Move start_wave_recovery() to execution-handler

**Validates**: Requirements 1.1, 2.1

- [x] 1.1 Copy `start_wave_recovery()` function to execution-handler
  - **Source**: `lambda/orchestration-stepfunctions/index.py` lines 745-870
  - **Destination**: `lambda/execution-handler/index.py`
  - **Size**: ~125 lines
  - **Requirements**: 
    - PEP 8 compliant (79 char lines, 4 spaces, double quotes)
    - Type hints on all functions
    - Google-style docstrings
    - Black formatted

- [x] 1.2 Copy function signature and docstring
  ```python
  def start_wave_recovery(state: Dict, wave_number: int) -> None:
      """
      Start DRS recovery for a wave with tag-based server resolution.
      
      Modifies state in-place (archive pattern) to update current wave tracking,
      job details, and wave results.
      
      Args:
          state: Complete state object with execution context (modified in-place)
          wave_number: Zero-based wave index to start
          
      Returns:
          None (modifies state in-place)
      """
  ```

- [x] 1.3 Copy helper function `apply_launch_config_before_recovery()`
  - **Source**: Lines 200-350 in orchestration Lambda
  - **Size**: ~150 lines
  - **Note**: This is called by `start_wave_recovery()` and must move with it

- [x] 1.4 Copy required imports
  - `from shared.account_utils import construct_role_arn`
  - `from shared.cross_account import create_drs_client`
  - `from shared.config_merge import get_effective_launch_config`

- [x] 1.5 Copy required helper functions
  - `get_protection_groups_table()` - DynamoDB table accessor
  - `get_execution_history_table()` - DynamoDB table accessor
  - `get_account_context()` - Extract cross-account context

- [x] 1.6 Copy required environment variables
  - Add to execution-handler: `PROTECTION_GROUPS_TABLE`
  - Add to execution-handler: `EXECUTION_HISTORY_TABLE`

- [x] 1.7 Add action handler in `lambda_handler()`
  ```python
  if action == 'start_wave_recovery':
      state = event.get('state', {})
      wave_number = event.get('wave_number', 0)
      start_wave_recovery(state, wave_number)  # Modifies state in-place
      return state  # Return modified state
  ```

- [x] 1.8 Write unit tests for start_wave_recovery in execution-handler
  - **File**: `tests/unit/test_execution_handler_start_wave.py`
  - **Coverage**: Test function independently with mocked DRS client

- [x] 1.9 Test successful wave start

- [x] 1.10 Test Protection Group not found

- [x] 1.11 Test empty server list (no tags matched)

- [x] 1.12 Test DRS API error handling

- [x] 1.13 Test cross-account context handling

- [x] 1.14 Remove functions from NEW orchestration Lambda
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`
  - **Action**: Delete `start_wave_recovery()` and `apply_launch_config_before_recovery()`
  - **Note**: Do NOT touch original `lambda/orchestration-stepfunctions/`

### 2. Move update_wave_status() to query-handler

**Validates**: Requirements 1.2, 2.2

- [x] 2.1 Copy `update_wave_status()` function to query-handler (rename to `poll_wave_status`)
  - **Source**: `lambda/orchestration-stepfunctions/index.py` lines 873-1219
  - **Destination**: `lambda/query-handler/index.py`
  - **Size**: ~346 lines
  - **New name**: `poll_wave_status()` (more descriptive)

- [x] 2.2 Copy function signature and docstring
  ```python
  def poll_wave_status(state: Dict) -> Dict:
      """
      Poll DRS job status and track server launch progress.
      
      Called repeatedly by Step Functions Wait state until wave completes or times out.
      Checks for cancellation, tracks server launch status, and manages wave transitions.
      
      Args:
          state: Complete state object with job_id, region, wave tracking
          
      Returns:
          Updated state object with wave status and completion flags
      """
  ```

- [x] 2.3 Copy required imports
  - `from shared.account_utils import construct_role_arn`
  - `from shared.cross_account import create_drs_client`

- [x] 2.4 Copy required constants
  - `DRS_JOB_STATUS_COMPLETE_STATES = ["COMPLETED"]`
  - `DRS_JOB_STATUS_WAIT_STATES = ["PENDING", "STARTED"]`
  - `DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ["LAUNCHED"]`
  - `DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ["FAILED", "TERMINATED"]`
  - `DRS_JOB_SERVERS_WAIT_STATES = ["PENDING", "IN_PROGRESS"]`

- [x] 2.5 Copy required helper functions
  - `get_execution_history_table()` - DynamoDB table accessor
  - `get_account_context()` - Extract cross-account context

- [x] 2.6 Copy required environment variables
  - Add to query-handler: `EXECUTION_HISTORY_TABLE`
  - Add to query-handler: `EXECUTION_HANDLER_ARN`

- [x] 2.7 Update function to invoke execution-handler for next wave
  - Replace direct `start_wave_recovery()` call with Lambda invocation:
  ```python
  lambda_client = boto3.client('lambda')
  response = lambda_client.invoke(
      FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
      InvocationType='RequestResponse',
      Payload=json.dumps({
          'action': 'start_wave_recovery',
          'state': state,
          'wave_number': next_wave
      })
  )
  result = json.loads(response['Payload'].read())
  state.update(result)
  ```

- [x] 2.8 Add action handler in `lambda_handler()`
  ```python
  if action == 'poll_wave_status':
      state = event.get('state', {})
      result = poll_wave_status(state)
      return result
  ```

- [x] 2.9 Write unit tests for poll_wave_status in query-handler
  - **File**: `tests/unit/test_query_handler_poll_wave.py`
  - **Coverage**: Test function independently with mocked DRS client

- [x] 2.10 Test wave in progress (servers launching)

- [x] 2.11 Test wave completed (all servers launched)

- [x] 2.12 Test wave failed (servers failed to launch)

- [x] 2.13 Test wave timeout

- [x] 2.14 Test execution cancellation

- [x] 2.15 Test pause before next wave

- [x] 2.16 Test starting next wave (mock Lambda invocation)

- [x] 2.17 Remove function from NEW orchestration Lambda
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`
  - **Action**: Delete `update_wave_status()`
  - **Note**: Do NOT touch original `lambda/orchestration-stepfunctions/`

### 3. Move query_drs_servers_by_tags() to query-handler

**Validates**: Requirements 1.3, 2.3

- [x] 3.1 Copy `query_drs_servers_by_tags()` function to query-handler
  - **Source**: `lambda/orchestration-stepfunctions/index.py` lines 645-744
  - **Destination**: `lambda/query-handler/index.py`
  - **Size**: ~99 lines

- [x] 3.2 Copy function signature and docstring
  ```python
  def query_drs_servers_by_tags(
      region: str,
      tags: Dict[str, str],
      account_context: Dict = None
  ) -> List[str]:
      """
      Query DRS source servers matching ALL specified tags (AND logic).
      
      Tag-based discovery enables dynamic server resolution at execution time.
      
      Args:
          region: AWS region to query DRS servers
          tags: Dict of tag key-value pairs that servers must match
          account_context: Optional cross-account context
          
      Returns:
          List of DRS source server IDs matching all tags
      """
  ```

- [x] 3.3 Copy required imports
  - `from shared.cross_account import create_drs_client`

- [x] 3.4 Add action handler in `lambda_handler()`
  ```python
  if action == 'query_servers_by_tags':
      region = event.get('region')
      tags = event.get('tags', {})
      account_context = event.get('account_context')
      result = query_drs_servers_by_tags(region, tags, account_context)
      return {'server_ids': result}
  ```

- [x] 3.5 Write unit tests for query_drs_servers_by_tags in query-handler
  - **File**: `tests/unit/test_query_handler_query_servers.py`
  - **Coverage**: Test function independently with mocked DRS client

- [x] 3.6 Test successful server query with matching tags

- [x] 3.7 Test no servers match tags

- [x] 3.8 Test case-insensitive tag matching

- [x] 3.9 Test AND logic (all tags must match)

- [x] 3.10 Test cross-account context handling

- [x] 3.11 Remove function from NEW orchestration Lambda
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`
  - **Action**: Delete `query_drs_servers_by_tags()`
  - **Note**: Do NOT touch original `lambda/orchestration-stepfunctions/`

### 4. Update NEW orchestration Lambda to invoke handlers

**Validates**: Requirements 3.1, 3.2, 3.3

- [x] 4.1 Update `begin_wave_plan()` to invoke execution-handler
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`
  - **Note**: Working in NEW Lambda, not original

- [x] 4.2 Replace direct `start_wave_recovery()` call with Lambda invocation
  ```python
  lambda_client = boto3.client('lambda')
  response = lambda_client.invoke(
      FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
      InvocationType='RequestResponse',
      Payload=json.dumps({
          'action': 'start_wave_recovery',
          'state': state,
          'wave_number': 0
      })
  )
  result = json.loads(response['Payload'].read())
  state.update(result)
  ```

- [x] 4.3 Add error handling for Lambda invocation failures

- [x] 4.4 Create new `poll_wave_status()` function in NEW orchestration
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`

- [x] 4.5 Create function that invokes query-handler
  ```python
  def poll_wave_status(event: Dict) -> Dict:
      """Poll wave status by invoking query-handler."""
      state = event.get("application", event)
      
      lambda_client = boto3.client('lambda')
      response = lambda_client.invoke(
          FunctionName=os.environ['QUERY_HANDLER_ARN'],
          InvocationType='RequestResponse',
          Payload=json.dumps({
              'action': 'poll_wave_status',
              'state': state
          })
      )
      
      result = json.loads(response['Payload'].read())
      return result
  ```

- [x] 4.6 Update `lambda_handler()` to route to `poll_wave_status()`
  ```python
  elif action == "poll_wave_status":
      return poll_wave_status(event)
  ```

- [x] 4.7 Update `resume_wave()` to invoke execution-handler
  - **File**: `lambda/dr-orchestration-stepfunction/index.py`

- [x] 4.8 Replace direct `start_wave_recovery()` call with Lambda invocation
  ```python
  lambda_client = boto3.client('lambda')
  response = lambda_client.invoke(
      FunctionName=os.environ['EXECUTION_HANDLER_ARN'],
      InvocationType='RequestResponse',
      Payload=json.dumps({
          'action': 'start_wave_recovery',
          'state': state,
          'wave_number': paused_before_wave
      })
  )
  result = json.loads(response['Payload'].read())
  state.update(result)
  ```

- [x] 4.9 Verify all DRS-specific functions removed from NEW orchestration
  - **Check**: No `start_wave_recovery()` function
  - **Check**: No `update_wave_status()` function
  - **Check**: No `query_drs_servers_by_tags()` function
  - **Check**: No `apply_launch_config_before_recovery()` function

- [x] 4.10 Verify no direct DRS API calls in NEW orchestration
  - **Check**: No `drs_client.start_recovery()` calls
  - **Check**: No `drs_client.describe_jobs()` calls
  - **Check**: No `drs_client.describe_source_servers()` calls

- [x] 4.11 Write unit tests for NEW orchestration Lambda invocations
  - **File**: `tests/unit/test_dr_orchestration_handler_invocations.py`
  - **Coverage**: Test Lambda invocations with mocked boto3 client

- [x] 4.12 Test `begin_wave_plan()` invokes execution-handler correctly

- [x] 4.13 Test `poll_wave_status()` invokes query-handler correctly

- [x] 4.14 Test `resume_wave()` invokes execution-handler correctly

- [x] 4.15 Test error handling for invocation failures

### 5. Update CloudFormation infrastructure

**Validates**: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

- [x] 5.1 Add new Lambda resource to CloudFormation
  - **File**: `cfn/lambda-stack.yaml`

- [x] 5.2 Create `DrOrchestrationStepFunctionFunction` resource
  ```yaml
  DrOrchestrationStepFunctionFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: !Sub "${ProjectName}-dr-orch-sf-${Environment}"
      Description: "Generic wave-based orchestration (refactored, no DRS code)"
      Runtime: python3.12
      Handler: index.lambda_handler
      Role: !Ref OrchestrationRoleArn
      Code:
        S3Bucket: !Ref SourceBucket
        S3Key: "lambda/dr-orchestration-stepfunction.zip"
      Timeout: 120
      MemorySize: 512
      Environment:
        Variables:
          PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
          RECOVERY_PLANS_TABLE: !Ref RecoveryPlansTableName
          EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
          EXECUTION_NOTIFICATIONS_TOPIC_ARN: !Ref ExecutionNotificationsTopicArn
          DRS_ALERTS_TOPIC_ARN: !Ref DRSAlertsTopicArn
          EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
          QUERY_HANDLER_ARN: !GetAtt QueryHandlerFunction.Arn
  ```

- [x] 5.3 Keep original Lambda resource unchanged
  - **Resource**: `OrchestrationStepFunctionsFunction`
  - **Action**: No changes (kept as reference)

- [x] 5.4 Update QueryHandlerFunction environment variables
  ```yaml
  Environment:
    Variables:
      # ... existing variables ...
      EXECUTION_HANDLER_ARN: !GetAtt ExecutionHandlerFunction.Arn
      EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
  ```

- [x] 5.5 Update ExecutionHandlerFunction environment variables
  ```yaml
  Environment:
    Variables:
      # ... existing variables ...
      PROTECTION_GROUPS_TABLE: !Ref ProtectionGroupsTableName
      EXECUTION_HISTORY_TABLE: !Ref ExecutionHistoryTableName
  ```

- [x] 5.6 Update OrchestrationRole IAM permissions
  - **File**: `cfn/lambda-stack.yaml` or IAM stack

- [x] 5.7 Add Lambda invoke permissions to orchestration role
  ```yaml
  - Effect: Allow
    Action:
      - lambda:InvokeFunction
    Resource:
      - !GetAtt ExecutionHandlerFunction.Arn
      - !GetAtt QueryHandlerFunction.Arn
  ```

- [x] 5.8 Update QueryHandlerRole IAM permissions

- [x] 5.9 Add Lambda invoke and DynamoDB permissions to query-handler role
  ```yaml
  - Effect: Allow
    Action:
      - lambda:InvokeFunction
    Resource:
      - !GetAtt ExecutionHandlerFunction.Arn
  - Effect: Allow
    Action:
      - dynamodb:GetItem
      - dynamodb:UpdateItem
    Resource:
      - !GetAtt ExecutionHistoryTable.Arn
  ```

- [x] 5.10 Update ExecutionHandlerRole IAM permissions

- [x] 5.11 Add DynamoDB permissions to execution-handler role
  ```yaml
  - Effect: Allow
    Action:
      - dynamodb:GetItem
      - dynamodb:Query
    Resource:
      - !GetAtt ProtectionGroupsTable.Arn
  - Effect: Allow
    Action:
      - dynamodb:UpdateItem
    Resource:
      - !GetAtt ExecutionHistoryTable.Arn
  ```

- [x] 5.12 Update Step Functions state machine
  - **File**: `cfn/step-functions-stack.yaml`

- [x] 5.13 Update state machine to use new Lambda ARN
  ```yaml
  DefinitionSubstitutions:
    OrchestrationLambdaArn: !GetAtt DrOrchestrationStepFunctionFunction.Arn
    # OLD (keep in comment for rollback):
    # OrchestrationLambdaArn: !GetAtt OrchestrationStepFunctionsFunction.Arn
  ```

- [x] 5.14 Update package_lambda.py
  - **File**: `package_lambda.py`

- [x] 5.15 Add new Lambda to packaging list
  ```python
  lambdas = [
      ("query-handler", False),
      ("data-management-handler", False),
      ("execution-handler", False),
      ("frontend-deployer", True),
      ("notification-formatter", False),
      ("orchestration-stepfunctions", False),  # KEEP: Original (reference)
      ("dr-orchestration-stepfunction", False),  # NEW: Refactored (no 's')
  ]
  ```

- [x] 5.16 Validate CloudFormation templates
  - **Command**: `cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml`
  - **Requirement**: Zero errors (warnings acceptable)

### 6. Integration testing

**Validates**: Requirements 6.1, 6.2

**STATUS**: Code refactoring complete, integration testing needed

**INSTRUCTIONS FOR TASK SUBAGENT**:
The refactored code is deployed to test environment. You need to execute recovery plans and verify the new Lambda invocation pattern works correctly.

**Test Environment Details**:
- Stack: `aws-drs-orchestration-test` (account `438465159935`, region `us-east-1`)
- New Lambda: `aws-drs-orchestration-dr-orch-sf-test`
- Execution Handler: `aws-drs-orchestration-execution-handler-test`
- Query Handler: `aws-drs-orchestration-query-handler-test`

**How to Execute Tests**:
1. Use frontend at CloudFront URL to trigger recovery plan executions
2. Monitor CloudWatch logs for all 3 Lambdas
3. Check DynamoDB execution history table for state updates
4. Verify Step Functions execution shows correct Lambda invocations

- [x] 6.1 Test single-wave execution end-to-end
  - **Environment**: test

- [x] 6.2 Deploy to test environment: `./scripts/deploy.sh test`

- [x] 6.3 Execute single-wave recovery plan

- [ ] 6.4 Verify wave starts correctly (execution-handler invoked)
  - **Action**: Check CloudWatch logs for `aws-drs-orchestration-execution-handler-test`
  - **Look for**: Log entry showing `start_wave_recovery` action received
  - **Command**: `AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-execution-handler-test --since 10m --region us-east-1`

- [ ] 6.5 Verify polling works (query-handler invoked)
  - **Action**: Check CloudWatch logs for `aws-drs-orchestration-query-handler-test`
  - **Look for**: Log entry showing `poll_wave_status` action received
  - **Command**: `AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-query-handler-test --since 10m --region us-east-1`

- [ ] 6.6 Verify wave completes successfully
  - **Action**: Check execution history in DynamoDB
  - **Look for**: Execution status = "completed", wave_completed = true
  - **Command**: Query DynamoDB table `aws-drs-orchestration-execution-history-test`

- [ ] 6.7 Verify DynamoDB updates are correct
  - **Action**: Compare execution record structure before/after refactoring
  - **Look for**: Same fields present (job_id, server_ids, wave_results, etc.)

- [ ] 6.8 Verify CloudWatch logs show handler invocations
  - **Action**: Check orchestration Lambda logs for Lambda.Invoke calls
  - **Look for**: "Invoking execution-handler" or "Invoking query-handler" messages
  - **Command**: `AWS_PAGER="" aws logs tail /aws/lambda/aws-drs-orchestration-dr-orch-sf-test --since 10m --region us-east-1`

- [ ] 6.9 Test multi-wave execution
  - **Action**: Create/execute recovery plan with 3 waves

- [ ] 6.10 Execute 3-wave recovery plan
  - **Action**: Use frontend to trigger multi-wave execution
  - **Note**: May need to create test recovery plan with 3 waves if none exists

- [ ] 6.11 Verify sequential wave execution (wave 2 starts after wave 1 completes)
  - **Action**: Check CloudWatch logs show wave 1 complete before wave 2 starts
  - **Look for**: Timestamps showing sequential execution

- [ ] 6.12 Verify all waves complete successfully
  - **Action**: Check execution history shows all 3 waves completed
  - **Look for**: wave_results array has 3 entries, all with success status

- [ ] 6.13 Verify wave results aggregation
  - **Action**: Check execution record has complete wave_results array
  - **Look for**: Each wave result has job_id, server_count, success/failure counts

- [ ] 6.14 Test pause/resume workflow
  - **Action**: Create recovery plan with pause before wave 2

- [ ] 6.15 Execute plan with pause before wave 2
  - **Action**: Trigger execution via frontend
  - **Note**: Set pauseBeforeWave=true for wave 2 in recovery plan

- [ ] 6.16 Verify execution pauses correctly
  - **Action**: Check execution status = "paused", paused_before_wave = 1
  - **Look for**: Step Functions execution in PAUSED state

- [ ] 6.17 Resume execution manually
  - **Action**: Use frontend "Resume" button or API call
  - **Command**: POST to `/executions/{execution_id}/resume`

- [ ] 6.18 Verify wave 2 starts correctly (execution-handler invoked)
  - **Action**: Check execution-handler logs after resume
  - **Look for**: start_wave_recovery called with wave_number=1

- [ ] 6.19 Verify execution completes successfully
  - **Action**: Check final execution status = "completed"
  - **Look for**: All waves completed, no errors

- [ ] 6.20 Test error handling
  - **Action**: Simulate errors to test error paths

- [ ] 6.21 Test DRS API error during wave start
  - **Action**: Trigger execution with invalid server IDs or missing permissions
  - **Look for**: Execution status = "failed", error message captured

- [ ] 6.22 Test DRS API error during polling
  - **Action**: Monitor execution where DRS job fails
  - **Look for**: Wave status shows failure, error details captured

- [ ] 6.23 Test Lambda invocation timeout
  - **Action**: Check handler timeout handling (may need to simulate)
  - **Look for**: Orchestration Lambda handles invocation errors gracefully

- [ ] 6.24 Verify error states are correct
  - **Action**: Check execution records for failed executions
  - **Look for**: status="failed", error field populated

- [ ] 6.25 Verify DynamoDB updates reflect errors
  - **Action**: Query execution history for failed executions
  - **Look for**: Error details stored correctly

- [ ] 6.26 Verify backward compatibility
  - **Action**: Test all API endpoints and frontend features

- [ ] 6.27 Test all 47 API endpoints still work
  - **Action**: Run API test suite or manually test key endpoints
  - **Endpoints**: GET /executions, GET /executions/{id}, POST /executions, etc.
  - **Note**: Focus on execution-related endpoints

- [ ] 6.28 Test frontend execution list page
  - **Action**: Open frontend, navigate to executions list
  - **Verify**: List displays correctly, shows execution status

- [ ] 6.29 Test frontend execution details page
  - **Action**: Click on execution to view details
  - **Verify**: Wave progress, server status, timeline all display correctly

- [ ] 6.30 Test frontend wave status display
  - **Action**: Check wave progress indicators during execution
  - **Verify**: Real-time updates work, status colors correct

- [ ] 6.31 Verify response formats unchanged
  - **Action**: Compare API responses before/after refactoring
  - **Verify**: Same JSON structure, same field names

### 7. Performance validation

**Validates**: Requirements 6.3

**STATUS**: Ready for performance testing

**INSTRUCTIONS FOR TASK SUBAGENT**:
Compare execution performance before/after refactoring to ensure no degradation.

**Performance Baseline**:
- Original Lambda: `aws-drs-orchestration-orch-sf-test`
- New Lambda: `aws-drs-orchestration-dr-orch-sf-test`
- Acceptable variance: ±5% execution time

**How to Measure Performance**:
1. Use CloudWatch Metrics to compare Lambda durations
2. Check Step Functions execution times
3. Monitor DynamoDB read/write capacity

- [ ] 7.1 Compare execution times before/after refactoring
  - **Action**: Compare Step Functions execution duration for same recovery plan
  - **Note**: May need to check historical executions or re-run with old Lambda

- [ ] 7.2 Measure baseline execution time (before refactoring)
  - **Action**: Check CloudWatch metrics for original Lambda
  - **Command**: `AWS_PAGER="" aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value=aws-drs-orchestration-orch-sf-test --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 3600 --statistics Average,Maximum --region us-east-1`
  - **Note**: Original Lambda may not have recent invocations if Step Functions switched to new Lambda

- [ ] 7.3 Measure new execution time (after refactoring)
  - **Action**: Check CloudWatch metrics for new Lambda
  - **Command**: `AWS_PAGER="" aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Duration --dimensions Name=FunctionName,Value=aws-drs-orchestration-dr-orch-sf-test --start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 3600 --statistics Average,Maximum --region us-east-1`

- [ ] 7.4 Verify difference is within ±5%
  - **Action**: Calculate percentage difference between baseline and new
  - **Formula**: `((new_time - baseline_time) / baseline_time) * 100`
  - **Acceptance**: -5% to +5% variance

- [ ] 7.5 Document any performance changes
  - **Action**: Create summary of performance comparison
  - **Include**: Average duration, max duration, invocation count, any anomalies

- [ ] 7.6 Monitor CloudWatch metrics
  - **Action**: Review metrics for all 3 Lambdas

- [ ] 7.7 Lambda invocation count (should increase due to handler calls)
  - **Action**: Check invocation metrics
  - **Expected**: Orchestration invocations same, handler invocations increased
  - **Command**: `AWS_PAGER="" aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Invocations --dimensions Name=FunctionName,Value=aws-drs-orchestration-execution-handler-test --start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 3600 --statistics Sum --region us-east-1`

- [ ] 7.8 Lambda duration (orchestration should decrease, handlers increase)
  - **Action**: Compare duration metrics for all Lambdas
  - **Expected**: Orchestration faster (no DRS calls), handlers slightly slower (new work)
  - **Note**: Overall execution time should be similar due to Lambda invocation overhead

- [ ] 7.9 Lambda errors (should be zero)
  - **Action**: Check error metrics for all Lambdas
  - **Command**: `AWS_PAGER="" aws cloudwatch get-metric-statistics --namespace AWS/Lambda --metric-name Errors --dimensions Name=FunctionName,Value=aws-drs-orchestration-dr-orch-sf-test --start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 3600 --statistics Sum --region us-east-1`
  - **Expected**: Zero errors

- [ ] 7.10 DynamoDB read/write capacity (should be unchanged)
  - **Action**: Check DynamoDB metrics for execution history table
  - **Command**: `AWS_PAGER="" aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedReadCapacityUnits --dimensions Name=TableName,Value=aws-drs-orchestration-execution-history-test --start-time $(date -u -v-1d +%Y-%m-%dT%H:%M:%S) --end-time $(date -u +%Y-%m-%dT%H:%M:%S) --period 3600 --statistics Sum --region us-east-1`
  - **Expected**: Similar read/write patterns as before

### 8. Documentation

**Validates**: Requirements 6.4

**STATUS**: Ready for documentation updates

**INSTRUCTIONS FOR TASK SUBAGENT**:
Update architecture documentation to reflect the refactored Lambda structure.

- [ ] 8.1 Update architecture documentation
  - **File**: `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`
  - **Action**: Add section describing the refactored orchestration pattern

- [ ] 8.2 Document new orchestration → handler invocation pattern
  - **Action**: Add diagram showing Lambda invocation flow
  - **Content**: 
    ```
    Step Functions → Orchestration Lambda (dr-orchestration-stepfunction)
                     ↓ (Lambda.Invoke)
                     Execution Handler (start_wave_recovery)
                     ↓ (Lambda.Invoke)
                     Query Handler (poll_wave_status)
                     ↓ (Lambda.Invoke)
                     Execution Handler (start next wave)
    ```

- [ ] 8.3 Update architecture diagrams
  - **Action**: Update any existing diagrams to show new Lambda structure
  - **Note**: If diagrams are in draw.io or other format, describe changes needed

- [ ] 8.4 Document function locations (which handler has which function)
  - **Action**: Create table showing function distribution
  - **Content**:
    ```
    | Function | Location | Purpose |
    |----------|----------|---------|
    | start_wave_recovery | execution-handler | Start DRS recovery for wave |
    | apply_launch_config_before_recovery | execution-handler | Apply launch configs |
    | poll_wave_status | query-handler | Poll DRS job status |
    | query_drs_servers_by_tags | query-handler | Query servers by tags |
    | begin_wave_plan | orchestration | Orchestrate wave execution |
    | resume_wave | orchestration | Resume paused execution |
    ```

- [ ] 8.5 Update deployment guide
  - **File**: `docs/deployment/QUICK_START_GUIDE.md`
  - **Action**: Update Lambda function list to include new orchestration Lambda

- [ ] 8.6 Document new environment variables
  - **Action**: Add section listing new environment variables
  - **Content**:
    ```
    Orchestration Lambda:
    - EXECUTION_HANDLER_ARN: ARN of execution handler Lambda
    - QUERY_HANDLER_ARN: ARN of query handler Lambda
    
    Query Handler Lambda:
    - EXECUTION_HANDLER_ARN: ARN of execution handler Lambda
    - EXECUTION_HISTORY_TABLE: DynamoDB table name
    
    Execution Handler Lambda:
    - PROTECTION_GROUPS_TABLE: DynamoDB table name
    - EXECUTION_HISTORY_TABLE: DynamoDB table name
    ```

- [ ] 8.7 Document new IAM permissions
  - **Action**: Add section listing new IAM permissions
  - **Content**:
    ```
    Orchestration Role:
    - lambda:InvokeFunction on execution-handler and query-handler
    
    Query Handler Role:
    - lambda:InvokeFunction on execution-handler
    - dynamodb:GetItem, UpdateItem on execution-history table
    
    Execution Handler Role:
    - dynamodb:GetItem, Query on protection-groups table
    - dynamodb:UpdateItem on execution-history table
    ```

- [ ] 8.8 Create refactoring summary document
  - **File**: `docs/analysis/GENERIC_ORCHESTRATION_REFACTORING_SUMMARY.md`
  - **Action**: Create new document in `/docs/analysis/` directory summarizing the refactoring

- [ ] 8.9 Document what was moved and why
  - **Action**: Write summary section in the analysis document
  - **Content**: Explain that 4 DRS-specific functions (~720 lines) were moved from orchestration Lambda to handler Lambdas to make orchestration generic and reusable

- [ ] 8.10 Document testing results
  - **Action**: Add testing results section to analysis document
  - **Include**: Number of tests run, pass/fail status, any issues found

- [ ] 8.11 Document performance impact
  - **Action**: Add performance section to analysis document
  - **Include**: Execution time comparison, Lambda duration changes, any performance notes

- [ ] 8.12 Document lessons learned
  - **Action**: Add lessons learned section to analysis document
  - **Include**: What went well, what was challenging, recommendations for future refactoring

---

## Code Quality Requirements

**CRITICAL**: All code must pass CI/CD pipeline validation before deployment

### Pre-Commit Checklist

- [ ] Virtual environment activated: `source .venv/bin/activate`
- [ ] Code formatted: `black --line-length 79 lambda/`
- [ ] Linting passes: `flake8 lambda/ --config .flake8` (zero errors)
- [ ] Type hints on all functions
- [ ] Google-style docstrings on all public functions
- [ ] No print() statements (use logger.info() instead)
- [ ] No temporal comments (TODO, FIXME, HACK)
- [ ] Tests written and passing: `pytest tests/unit/ -v`
- [ ] CloudFormation valid: `cfn-lint cfn/*.yaml --config-file .cfnlintrc.yaml`
- [ ] Security scan passes: `bandit -r lambda/ -ll`
- [ ] Validation passes: `./scripts/deploy.sh test --validate-only`

### CI/CD Pipeline Stages

**Stage 1: Validation (BLOCKING)**
- [ ] cfn-lint: CloudFormation validation
- [ ] flake8: Python linting (warnings non-blocking)
- [ ] black: Python formatting (BLOCKING)
- [ ] TypeScript: Type checking (BLOCKING)

**Stage 2: Security (NON-BLOCKING - warnings only)**
- [ ] bandit: Python SAST
- [ ] cfn_nag: CloudFormation security
- [ ] detect-secrets: Credential scanning
- [ ] shellcheck: Shell script security
- [ ] npm audit: Frontend dependencies

**Stage 3: Tests (BLOCKING)**
- [ ] pytest: Python tests (unit + integration)
- [ ] vitest: Frontend tests

**Stage 4: Git Push (ALWAYS runs)**
- [ ] Push to remote repository

**Stage 5: Deploy**
- [ ] Build Lambda packages
- [ ] Sync to S3
- [ ] Deploy CloudFormation

### Deployment Commands

```bash
# Full deployment (all stages)
./scripts/deploy.sh test

# Validation only (no deployment)
./scripts/deploy.sh test --validate-only

# Lambda code update only
./scripts/deploy.sh test --lambda-only
```

---

## Success Criteria

### Functional Requirements
- [ ] Orchestration Lambda has zero DRS API calls
- [ ] All 3 functions moved to appropriate handlers
- [ ] All existing DRS operations work identically
- [ ] All existing integration tests pass
- [ ] All existing unit tests pass
- [ ] No regression in functionality
- [ ] Same execution times (±5%)
- [ ] Identical state objects produced
- [ ] Identical DynamoDB records created

### Code Quality Requirements
- [ ] Black formatting passes (79 char lines)
- [ ] Flake8 linting passes (zero errors)
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] No temporal comments
- [ ] Code review approved
- [ ] >90% test coverage for moved code

### Security Requirements
- [ ] Bandit security scan passes
- [ ] cfn_nag validation passes
- [ ] No secrets in code
- [ ] Proper IAM permissions
- [ ] Cross-account security validated

### Deployment Requirements
- [ ] Deployed to test environment successfully
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Documentation complete

---

## Estimated Duration

**Total**: 1-2 weeks

**Breakdown**:
- Task 0 (Create new Lambda directory): 0.5 day
- Task 1 (Move start_wave_recovery + helper): 1-2 days
- Task 2 (Move update_wave_status): 1-2 days
- Task 3 (Move query_drs_servers_by_tags): 0.5 day
- Task 4 (Update NEW orchestration): 1 day
- Task 5 (CloudFormation updates): 1 day
- Task 6 (Integration testing): 2-3 days
- Task 7 (Performance validation): 0.5 day
- Task 8 (Documentation): 1 day

---

## Out of Scope

**NOT doing in this refactoring:**
- Creating new adapter Lambdas
- Making handlers generic/technology-agnostic
- Extracting ALL DRS code from handlers
- 4-phase lifecycle architecture
- Module factory pattern
- Multi-technology support

**Scope**: Create new orchestration Lambda directory, move 4 functions (~720 lines) from orchestration to handlers, update CloudFormation.
