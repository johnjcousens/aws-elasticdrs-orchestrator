# Step Functions Orchestration - Phase 2 Design Plan

**Status**: 📋 **PLANNED** - To be designed after Phase 1 validation  
**Date Created**: November 28, 2025  
**Target**: Phase 2 Implementation  
**Dependencies**: Phase 1 DRS API functional testing complete

## Overview

This document outlines the design for Step Functions-based orchestration to enable sequential wave execution, dependency enforcement, and SSM document integration.

## Phase 1 vs Phase 2

### Phase 1 Capabilities (Current)
✅ **Implemented**:
- Parallel wave execution (all waves start together)
- DRS job tracking via ExecutionPoller
- Wave completion detection
- Basic execution lifecycle management

❌ **Limitations**:
- No sequential execution
- Wave dependencies ignored
- No pre/post launch scripts
- Manual orchestration only

### Phase 2 Goals (Future)
🎯 **Target Capabilities**:
1. Sequential wave execution with dependency enforcement
2. Pre-launch SSM document execution
3. Post-launch SSM document execution
4. Real-time orchestration via Step Functions
5. Advanced error handling and retry logic
6. Visual workflow monitoring in AWS Console

## Architecture Design

### High-Level Pattern
```
Step Functions State Machine
├── Initialize Execution
├── For Each Wave (Sequential)
│   ├── Check Dependencies
│   │   └── Wait if dependencies not met
│   ├── Pre-Launch Phase
│   │   ├── Execute SSM Documents (if configured)
│   │   └── Wait for SSM completion
│   ├── DRS Launch Phase
│   │   ├── Invoke Lambda: start_drs_recovery_for_wave()
│   │   └── Store Job ID in execution state
│   ├── Polling Phase
│   │   ├── Wait (adaptive intervals)
│   │   ├── Poll DRS job status
│   │   └── Check completion
│   └── Post-Launch Phase
│       ├── Execute SSM Documents (if configured)
│       └── Wait for SSM completion
└── Finalize Execution
```

### State Machine Components

#### 1. Wave Iterator
- Iterate through waves in order
- Check dependencies before processing each wave
- Track wave completion state

#### 2. Dependency Checker
- Query previous wave status from DynamoDB
- Wait for dependent waves to complete
- Timeout if dependencies never satisfied

#### 3. SSM Document Executor
- Invoke SSM Run Command API
- Support pre-launch and post-launch phases
- Pass wave context (server IDs, region, etc.)

#### 4. DRS Launch Orchestrator
- Invoke existing Lambda function
- Wait for job ID response
- Store job ID for polling

#### 5. DRS Status Poller
- Query DRS job status
- Adaptive wait intervals (15s → 30s → 60s)
- Detect completion or timeout

#### 6. Error Handler
- Retry logic for transient failures
- Rollback capabilities
- Alert on critical failures

## Data Model

### Execution State
```json
{
  "ExecutionId": "uuid",
  "PlanId": "uuid",
  "CurrentWave": 0,
  "Waves": [
    {
      "WaveId": "wave-1",
      "Status": "PENDING|IN_PROGRESS|COMPLETED|FAILED",
      "DependenciesMet": true,
      "PreLaunchSSM": {
        "DocumentName": "string",
        "CommandId": "string",
        "Status": "PENDING|SUCCESS|FAILED"
      },
      "DRSLaunch": {
        "JobId": "string",
        "Status": "PENDING|STARTED|COMPLETED|FAILED"
      },
      "PostLaunchSSM": {
        "DocumentName": "string",
        "CommandId": "string",
        "Status": "PENDING|SUCCESS|FAILED"
      }
    }
  ]
}
```

### Recovery Plan Extensions
```json
{
  "Waves": [
    {
      "WaveId": "wave-1",
      "Dependencies": ["wave-0"],
      "PreLaunchScripts": [
        {
          "Type": "SSM_DOCUMENT",
          "DocumentName": "DatabaseBackup",
          "Parameters": {},
          "TimeoutSeconds": 300
        }
      ],
      "PostLaunchScripts": [
        {
          "Type": "SSM_DOCUMENT",
          "DocumentName": "HealthCheck",
          "Parameters": {},
          "TimeoutSeconds": 600
        }
      ]
    }
  ]
}
```

## CloudFormation Resources

### New Resources Required
```yaml
# Step Functions State Machine
DRSOrchestrationStateMachine:
  Type: AWS::StepFunctions::StateMachine
  Properties:
    StateMachineName: drs-orchestration-state-machine-test
    RoleArn: !GetAtt StateMachineRole.Arn
    DefinitionString: !Sub |
      {
        "Comment": "DRS Recovery Plan Orchestration",
        "StartAt": "InitializeExecution",
        ...
      }

# IAM Role for State Machine
StateMachineRole:
  Type: AWS::IAM::Role
  Properties:
    AssumeRolePolicyDocument:
      Statement:
        - Effect: Allow
          Principal:
            Service: states.amazonaws.com
          Action: sts:AssumeRole
    Policies:
      - PolicyName: StateMachineExecutionPolicy
        PolicyDocument:
          Statement:
            - Effect: Allow
              Action:
                - lambda:InvokeFunction
                - dynamodb:*
                - ssm:SendCommand
                - ssm:GetCommandInvocation
                - drs:DescribeJobs
              Resource: "*"
```

### Modified Resources
- Lambda execution role needs Step Functions invoke permissions
- DynamoDB table needs state machine read/write access
- CloudWatch Logs for state machine execution traces

## Integration Points

### 1. Lambda API Handler
**Changes Required**:
- `execute_recovery_plan()` invokes Step Functions instead of async Lambda
- Remove `execute_recovery_plan_worker()` (replaced by state machine)
- Keep `initiate_wave()` for state machine to call

### 2. ExecutionPoller
**Changes Required**:
- Called by Step Functions during polling phase
- Return job status to state machine
- Remove autonomous wave completion logic

### 3. DynamoDB Schema
**New Fields**:
- `StateMachineExecutionArn` - Link to Step Functions execution
- `CurrentWaveIndex` - Track which wave is processing
- `WaveDependencyStatus` - Track dependency resolution

### 4. Frontend
**No Changes Required**:
- Frontend continues to poll execution status from DynamoDB
- Status updates come from state machine (transparent to UI)

## SSM Integration Design

### Document Structure
```yaml
# Example Pre-Launch Document
schemaVersion: "2.2"
description: "Pre-launch validation and backup"
parameters:
  WaveId:
    type: String
  ExecutionId:
    type: String
mainSteps:
  - action: "aws:runShellScript"
    name: "ValidateAndBackup"
    inputs:
      runCommand:
        - echo "Validating wave {{ WaveId }}"
        - # Validation logic here
        - echo "Creating backup"
        - # Backup logic here
```

### Invocation Pattern
```python
response = ssm_client.send_command(
    DocumentName='PreLaunchValidation',
    Parameters={
        'WaveId': wave_id,
        'ExecutionId': execution_id
    },
    Targets=[
        {'Key': 'InstanceIds', 'Values': server_ids}
    ]
)
```

## Error Handling Strategy

### Transient Errors
- **DRS API Throttling**: Exponential backoff with retries
- **SSM Command Timeout**: Configurable timeout with retry
- **Network Issues**: Automatic retry (up to 3 attempts)

### Permanent Errors
- **Invalid Configuration**: Fail fast, don't retry
- **Insufficient Permissions**: Alert and stop
- **Resource Not Found**: Mark wave failed, continue or stop based on config

### Rollback Strategy
- **Wave Failure**: Option to continue or stop execution
- **SSM Failure**: Mark as warning or critical based on config
- **DRS Launch Failure**: Attempt rollback or leave for manual cleanup

## Testing Strategy

### Unit Testing
- Test each state in isolation
- Mock DRS/SSM API responses
- Validate state transitions

### Integration Testing
- Test full state machine with mock services
- Verify dependency enforcement
- Test SSM document execution

### End-to-End Testing
- Execute real recovery drill with Step Functions
- Verify sequential wave execution
- Test pre/post launch scripts
- Measure orchestration overhead

## Performance Considerations

### Latency
- Step Functions adds ~500ms per state transition
- Acceptable for wave orchestration (minutes to hours)
- Minimal impact on overall execution time

### Cost
- Step Functions: $0.025 per 1,000 state transitions
- Typical execution: ~50 transitions per 3-wave plan = $0.00125
- Negligible cost impact

### Scalability
- Step Functions supports 100,000 concurrent executions
- Well within MVP requirements
- Can handle multiple parallel recovery plans

## Migration Plan

### Phase 1 → Phase 2 Transition
1. **Deploy Step Functions resources** (CloudFormation update)
2. **Update Lambda to invoke state machine**
3. **Keep ExecutionPoller functional** (still needed for DRS polling)
4. **Add SSM document support** (optional initially)
5. **Test with existing recovery plans** (backward compatible)

### Backward Compatibility
- Existing executions continue with Phase 1 logic
- New executions use Step Functions
- Data model compatible with both approaches
- Frontend requires no changes

## Success Metrics

### Functional Requirements
- ✅ Sequential wave execution enforced
- ✅ Dependencies properly checked and enforced
- ✅ SSM documents execute successfully
- ✅ Real-time status updates
- ✅ Error handling works as designed

### Performance Requirements
- ⏱️ Orchestration overhead < 5% of total execution time
- ⏱️ State transitions complete within 1 second
- ⏱️ Dependency checks complete within 5 seconds

### Reliability Requirements
- 🛡️ 99.9% successful state machine executions
- 🛡️ Zero data loss during state transitions
- 🛡️ Graceful degradation on service failures

## Open Questions

1. **SSM Document Library**: Should we provide pre-built documents or require users to create their own?
2. **Rollback Strategy**: Automatic vs manual rollback on wave failure?
3. **Approval Gates**: Should we support manual approval between waves?
4. **Cost Optimization**: Should we use Express Workflows for lower latency/cost?
5. **Monitoring**: What CloudWatch metrics/alarms should we create?

## References

### AWS Documentation
- [Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/)
- [SSM Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html)
- [DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/)

### Related Documents
- `docs/BUG_4_WAVE_DEPENDENCY_ANALYSIS.md` - Dependency gap analysis
- `docs/DRS_DRILL_LEARNING_SESSION.md` - DRS API patterns
- `docs/PHASE_2_IMPLEMENTATION_SUMMARY.md` - Phase 2 infrastructure

### VMware SRM Reference
- VMware SRM uses similar orchestration patterns
- Recovery Plan Steps execute sequentially
- Supports pre/post scripts per protection group
- This design mirrors that proven pattern

---

**Status**: Design document created. Ready for detailed design after Phase 1 validation complete.

**Next Actions**: 
1. Complete Phase 1 functional testing
2. Review this design with stakeholders
3. Create detailed state machine definition
4. Implement CloudFormation resources
5. Test Step Functions orchestration
