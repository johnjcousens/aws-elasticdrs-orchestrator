# DRS AllowLaunchingIntoThisInstance Pattern - Specification

## Overview

This specification covers the implementation of the AWS DRS AllowLaunchingIntoThisInstance pattern, which enables launching recovery instances into pre-provisioned EC2 instances. This pattern dramatically reduces Recovery Time Objective (RTO) from 2-4 hours to 15-30 minutes and preserves instance identity (instance ID, private IP, network configuration) through complete disaster recovery cycles.

## Spec Structure

```
.kiro/specs/drs-allow-launching-into-instance/
├── README.md                    # This file - spec overview
├── requirements.md              # User stories and acceptance criteria
├── design.md                    # Technical design and architecture (TO BE CREATED)
├── tasks.md                     # Implementation tasks checklist (TO BE CREATED)
└── reference/                   # Supporting documentation (TO BE CREATED)
    ├── AWSM-1111-RESEARCH.md   # Original research document
    ├── INSTANCE_MATCHING_ALGORITHM.md
    ├── DRS_LAUNCH_CONFIGURATION.md
    ├── FAILOVER_FAILBACK_WORKFLOWS.md
    └── TESTING_STRATEGY.md
```

## Quick Start

### 1. Review Requirements ✅
Start by reading `requirements.md` to understand:
- User stories and acceptance criteria
- Non-functional requirements
- Technical constraints
- Success metrics
- Business value (88-92% RTO improvement)

### 2. Review Design 📋
Read `design.md` to understand (TO BE CREATED):
- Architecture overview
- Component design
- Instance matching algorithm
- DRS configuration workflow
- Failover and failback processes
- Error handling and retry logic

### 3. Execute Tasks 📋
Follow `tasks.md` to implement the feature (TO BE CREATED):
- Phase 1: Core Modules (instance matcher, DRS client)
- Phase 2: Configuration Management
- Phase 3: Recovery Orchestration
- Phase 4: Failback Implementation
- Phase 5: API Integration
- Phase 6: Frontend Integration
- Phase 7: Testing & Validation
- Phase 8: Production Rollout

### 4. Reference Documentation 📋
Use files in `reference/` for detailed guidance (TO BE CREATED):
- **AWSM-1111-RESEARCH.md** - Original research and analysis
- **INSTANCE_MATCHING_ALGORITHM.md** - Name tag matching details
- **DRS_LAUNCH_CONFIGURATION.md** - Configuration patterns
- **FAILOVER_FAILBACK_WORKFLOWS.md** - Complete workflows
- **TESTING_STRATEGY.md** - Test plan and coverage

## Current Status

### ✅ Completed
- Requirements document with 12 user stories
- Research analysis (archive/docs/Customer/.../AWSM-1111/README.md)
- Business case and value proposition

### 🚧 In Progress
- Design document (NEXT STEP)

### 📋 Pending
- Task breakdown
- Core module implementation
- API integration
- Frontend integration
- Testing and validation
- Production rollout

## Key Features

### Recovery Patterns

1. **Failover with AllowLaunchingIntoThisInstance**
   - Launches into pre-provisioned instances in DR region
   - Preserves network configuration
   - RTO: 15-30 minutes (vs 2-4 hours standard)
   - Zero DNS changes required

2. **Failback to Original Instances**
   - Returns to original source instances in primary region
   - Preserves instance ID and IP address
   - Eliminates application reconfiguration
   - True round-trip DR capability

### Core Capabilities

- Pre-provisioned instance discovery via AWSDRS tag
- Name tag matching between primary and DR regions
- Automated DRS launch configuration
- Wave-based orchestration integration
- Cross-account support
- Comprehensive validation and error handling
- Real-time monitoring and metrics

## Business Value

### RTO Improvement
- **Current State**: 2-4 hours for 100 instances
- **Future State**: 15-30 minutes for 100 instances
- **Improvement**: 88-92% reduction

### Operational Benefits
- **Zero DNS Changes**: Preserves IP addresses
- **Zero Reconfiguration**: Maintains instance identity
- **Reduced Complexity**: Eliminates manual steps
- **Lower Risk**: Fewer opportunities for human error
- **Cost Savings**: Faster recovery = less downtime cost

### Technical Benefits
- **Instance Identity Preservation**: Same instance ID through DR cycle
- **Network Configuration Preservation**: Same IP, security groups, ENI
- **Faster Recovery**: Volume replacement vs full instance launch
- **True Failback**: Return to exact original instances

## Implementation Phases

### Lambda Integration Strategy

**DECISION**: Integrate AllowLaunchingIntoThisInstance functionality into existing Lambda handlers based on operation type, NOT as a new handler.

**Rationale**:
- AllowLaunchingIntoThisInstance operations are fundamentally CRUD, execution, and query operations
- Separation should be by operation type (CRUD vs execution vs query), not by feature
- Maintains architectural consistency with existing handler organization
- Maximizes code reuse and simplifies deployment

See [INTEGRATION_DECISION.md](./INTEGRATION_DECISION.md) for detailed analysis.

### Integration Points

The feature integrates with existing infrastructure through:

1. **Data Management Handler**: Configuration operations (instance pairs, DRS settings, IP mappings)
2. **Execution Handler**: Execution operations (failover, failback, monitoring)
3. **Query Handler**: Query operations (instance matching, validation, status)
4. **DRS Agent Deployer**: Agent installation during failback (existing Lambda, invoked by execution handler)
5. **Shared Modules**: Reuses `shared/cross_account.py`, `shared/drs_utils.py`, `shared/account_utils.py`
6. **DynamoDB Tables**: New tables for instance pair configuration and failback state
7. **IAM Roles**: Uses same `UnifiedOrchestrationRole` with enhanced EC2 permissions

### API Endpoint Organization

**Configuration Endpoints** (data-management-handler):
- `POST /protection-groups/{id}/instance-pairs` - Configure instance pairs
- `PUT /protection-groups/{id}/instance-pairs/{pairId}` - Update instance pair
- `DELETE /protection-groups/{id}/instance-pairs/{pairId}` - Delete instance pair
- `POST /protection-groups/{id}/configure-allow-launching` - Configure DRS launch settings

**Execution Endpoints** (execution-handler):
- `POST /executions/allow-launching/failover` - Execute failover
- `POST /executions/allow-launching/failback` - Execute failback
- `GET /executions/{id}/allow-launching/status` - Get execution status

**Query Endpoints** (query-handler):
- `POST /drs/instances/match` - Match instances by Name tag
- `POST /drs/instances/validate-pairs` - Validate instance pairs
- `POST /drs/instances/validate-ip` - Validate IP preservation

## Implementation Phases

### Phase 1: Core Modules 📋
Implement instance matcher, DRS client, job monitor, error handler.

**Estimated Duration**: 2 weeks

**Deliverables**:
- `lambda/shared/instance_matcher.py`
- `lambda/shared/drs_client.py`
- `lambda/shared/drs_job_monitor.py`
- `lambda/shared/drs_error_handler.py`
- Unit tests (59 tests)

### Phase 2: Configuration Management 📋
Implement DRS launch configuration with AllowLaunchingIntoThisInstance.

**Estimated Duration**: 1 week

**Deliverables**:
- Two-step configuration process
- Validation logic
- DynamoDB state tracking
- Configuration API endpoints

### Phase 3: Recovery Orchestration 📋
Integrate with existing wave-based orchestration.

**Estimated Duration**: 1 week

**Deliverables**:
- Failover workflow integration
- Step Functions state machine updates
- Recovery job creation and monitoring
- Post-recovery validation

### Phase 4: Failback Implementation 📋
Implement reverse replication and failback to original instances.

**Estimated Duration**: 1 week

**Deliverables**:
- Reverse replication monitoring
- Failback workflow
- Original instance identification
- Failback validation

### Phase 5: API Integration 📋
Add REST API endpoints for AllowLaunchingIntoThisInstance operations.

**Estimated Duration**: 3 days

**Deliverables**:
- API endpoints (configure, validate, failover, failback, status)
- API documentation
- Integration tests

### Phase 6: Frontend Integration 📋
Create UI components for managing AllowLaunchingIntoThisInstance.

**Estimated Duration**: 1 week

**Deliverables**:
- Instance matching display
- Failover wizard
- Failback wizard
- Status monitoring dashboard

### Phase 7: Testing & Validation 📋
Comprehensive testing across all scales.

**Estimated Duration**: 1 week

**Deliverables**:
- Unit tests (59 tests)
- Integration tests (37 tests)
- End-to-end tests (8 tests)
- Performance tests
- Test report

### Phase 8: Production Rollout 📋
Deploy to production and validate.

**Estimated Duration**: 1 week

**Deliverables**:
- Production deployment
- DR drill execution
- Performance validation
- Documentation updates

**Total Estimated Duration**: 8 weeks

## Prerequisites

### Source Account (Primary Region)
- EC2 instances with DRS agents installed
- Source servers in `CONTINUOUS` replication state
- Instances tagged with `dr:enabled=true`, `dr:recovery-strategy=drs`
- Name tags following naming convention
- Cross-account IAM role for orchestration

### Target Account (DR Region)
- Pre-provisioned EC2 instances in `stopped` state
- Instances tagged with `AWSDRS=AllowLaunchingIntoThisInstance`
- Name tags matching source instances
- Compatible network configuration (subnet, security groups)
- DRS service initialized

### Orchestration Account
- Lambda functions deployed
- UnifiedOrchestrationRole with enhanced EC2 permissions
- Step Functions state machine
- DynamoDB tables for state management
- CloudWatch metrics and alarms

## Success Metrics

### Performance Metrics
- **RTO**: <30 minutes for 100 instances (target: 88-92% improvement)
- **Instance Matching Accuracy**: >98%
- **Configuration Success Rate**: >99%
- **Recovery Success Rate**: >95%
- **Failback Success Rate**: >90%

### Operational Metrics
- **API Response Time**: <2 seconds
- **Recovery Job Polling**: 30-second intervals
- **Validation Time**: <10 seconds for 1000 instances
- **Error Recovery Time**: <10 minutes

### Quality Metrics
- **Test Coverage**: >80% for new code
- **Unit Test Pass Rate**: 100%
- **Integration Test Pass Rate**: >95%
- **End-to-End Test Pass Rate**: >90%

## Related Features

### Dependencies
- **DRS Agent Deployer** - Installs DRS agents (prerequisite)
- **Wave-Based Orchestration** - Existing Step Functions workflow
- **Cross-Account Utilities** - Existing role assumption logic
- **Tag Sync** - Existing manual tag sync capability

### Related Specs
- [DRS Agent Deployer](./../drs-agent-deployer/README.md)
- [Generic Orchestration Refactoring](./../generic-orchestration-refactoring/README.md)
- [Staging Accounts Management](./../staging-accounts-management/README.md)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│    AllowLaunchingIntoThisInstance - Failback Pattern           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Primary Region (us-east-1)          DR Region (us-east-2)      │
│  ┌──────────────────────┐             ┌──────────────────────┐  │
│  │  Source Instance     │   Failover  │  Recovery Instance   │  │
│  │  i-0abc123 (running) │ ─────────>  │  i-0xyz789 (stopped) │  │
│  │  Name: web-app01     │   (DR Event)│  Name: web-app01     │  │
│  │  IP: 10.0.1.100      │             │  IP: 10.1.1.100      │  │
│  │  AWSDRS: (none)      │             │  AWSDRS: Allow...    │  │
│  └──────────────────────┘             └──────────────────────┘  │
│           │                                     │               │
│           │ After DR Event                      │               │
│           ▼                                     ▼               │
│  ┌──────────────────────┐             ┌──────────────────────┐  │
│  │  Source Instance     │             │  Recovery Instance   │  │
│  │  i-0abc123 (stopped) │             │  i-0xyz789 (running) │  │
│  │  Name: web-app01     │             │  Name: web-app01     │  │
│  │  IP: 10.0.1.100      │             │  IP: 10.1.1.100      │  │
│  │  (Original instance) │             │  (Active workload)   │  │
│  └──────────────────────┘             └──────────────────────┘  │
│           ▲                                     │               │
│           │            Failback                 │               │
│           └─────────────────────────────────────┘               │
│           (Launches into ORIGINAL instance,                     │
│            preserves i-0abc123 and 10.0.1.100)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Key Benefits:
- Preserves original instance ID (i-0abc123)
- Maintains original private IP (10.0.1.100)
- No application reconfiguration needed
- No DNS changes required
- Faster than creating new instance
```

## Key Workflows

### Failover Workflow
```
1. Discovery
   ├─ Query instances with dr:recovery-strategy=drs
   ├─ Filter for AWSDRS=AllowLaunchingIntoThisInstance
   └─ Validate prerequisites

2. Instance Matching
   ├─ Match by Name tag (normalized)
   ├─ Validate 1:1 mapping
   └─ Store matching results

3. Configuration
   ├─ Disable conflicting DRS settings
   ├─ Configure launchIntoInstanceProperties
   └─ Validate configuration

4. Recovery
   ├─ Create DRS recovery jobs
   ├─ Monitor job status
   └─ Validate recovery instances

5. Post-Recovery
   ├─ Verify instance IDs match targets
   ├─ Check EC2 status
   └─ Test application health
```

### Failback Workflow
```
1. Identify Original Instances
   ├─ Get stopped instances in primary region
   ├─ Match to active DR instances
   └─ Validate instance pairs

2. Prepare Recovery Instance for Reverse Replication
   ├─ Validate network connectivity (port 1500, 443)
   ├─ Verify security groups allow DRS traffic
   ├─ Check IAM instance profile has DRS permissions
   ├─ Confirm recovery instance is running
   └─ Validate DRS service initialized in primary region

3. Initiate Reverse Replication
   ├─ Call reverse_replication() API
   ├─ DRS automatically installs agent on recovery instance
   ├─ Monitor agent installation progress
   ├─ Detect and report installation failures
   └─ Begin reverse replication: DR → Primary

4. Monitor Reverse Replication
   ├─ Poll replication state until CONTINUOUS
   ├─ Monitor replication lag (<60 seconds target)
   ├─ Track data sync progress
   └─ Alert on replication issues

5. Configuration
   ├─ Configure launchIntoInstanceProperties
   ├─ Target original instance IDs
   └─ Validate configuration

6. Failback Recovery
   ├─ Create DRS recovery jobs
   ├─ Monitor job status
   └─ Validate recovery instances

7. Cleanup
   ├─ Terminate DR instances
   ├─ Verify primary instances running
   └─ Resume normal replication
```

## Getting Started

To begin implementation:

1. **Review the requirements**: Read `requirements.md` thoroughly
2. **Understand the research**: Review archive research document
3. **Create design document**: Next step - design.md
4. **Break down tasks**: Create tasks.md with detailed checklist
5. **Start implementation**: Begin with Phase 1 (Core Modules)

## Support

For questions or issues:
1. Review the requirements document
2. Consult the research document in archive
3. Check existing DRS guides in docs/guides/
4. Review related specs (DRS Agent Deployer)
5. Consult AWS DRS documentation

## Next Steps

**Ready to proceed?**

The next step is to create the design document (`design.md`) that will detail:
- Architecture and component design
- Instance matching algorithm
- DRS configuration workflow
- Failover and failback processes
- Data models and state management
- Error handling and retry logic
- Security design
- Testing strategy

Once the design is approved, we'll create the task breakdown (`tasks.md`) and begin implementation.

## Important Notes

### Relationship to Existing Features
- **Builds on**: DRS Agent Deployer (agents must be installed first)
- **Integrates with**: Wave-Based Orchestration (existing Step Functions)
- **Extends**: DRS Recovery capabilities (adds instance identity preservation)
- **Complements**: Cross-Account utilities (reuses role assumption logic)

### Key Differences from Standard DRS Recovery
- **Standard DRS**: Creates new instances with new IDs and IPs
- **AllowLaunchingIntoThisInstance**: Launches into existing instances, preserves identity
- **Standard RTO**: 2-4 hours for large-scale recovery
- **AllowLaunchingIntoThisInstance RTO**: 15-30 minutes for large-scale recovery
- **Standard Failback**: Creates new instances in primary region
- **AllowLaunchingIntoThisInstance Failback**: Returns to original instances

### Critical Success Factors
1. **Accurate Instance Matching**: Name tags must match between regions
2. **Proper Tagging**: AWSDRS=AllowLaunchingIntoThisInstance required
3. **Instance State**: Target instances must be stopped
4. **Network Configuration**: Compatible subnets and security groups
5. **IAM Permissions**: Enhanced EC2 permissions for orchestration role
6. **Validation**: Comprehensive pre-recovery validation
7. **Monitoring**: Real-time job monitoring and alerting
8. **Testing**: Thorough testing at all scales before production

---

**Specification Status**: Requirements Complete ✅ | Design Pending 📋 | Implementation Pending 📋

**Last Updated**: 2026-02-03  
**Maintained By**: AWS DRS Orchestration Project Team
