# DRS AllowLaunchingIntoThisInstance Pattern - Requirements

## Feature Overview

Implementation of AWS DRS AllowLaunchingIntoThisInstance pattern to enable launching recovery instances into pre-provisioned EC2 instances, preserving instance identity (instance ID, private IP, network configuration) during disaster recovery operations. This feature dramatically reduces Recovery Time Objective (RTO) from 2-4 hours to 15-30 minutes and eliminates the need for DNS changes and application reconfiguration during failback operations.

## Business Value

### Current State (Without AllowLaunchingIntoThisInstance)
- **RTO**: 2-4 hours for 100 instances
- **Failover**: Creates new instances with new IDs and IPs
- **Failback**: Creates yet another set of new instances
- **Impact**: Requires DNS updates, application reconfiguration, and extensive validation
- **Cost**: Higher due to multiple instance launches and longer downtime

### Future State (With AllowLaunchingIntoThisInstance)
- **RTO**: 15-30 minutes for 100 instances (88-92% improvement)
- **Failover**: Launches into pre-provisioned instances in DR region
- **Failback**: Returns to original instances in primary region
- **Impact**: Zero DNS changes, zero application reconfiguration
- **Cost**: Lower due to instance reuse and faster recovery

### Key Benefits
- **88-92% RTO reduction** for large-scale recoveries
- **Preserves instance identity** (ID, IP, metadata) through complete DR cycle
- **Eliminates manual reconfiguration** after recovery
- **Enables true round-trip DR** (failover + failback to original instances)
- **Reduces operational complexity** and human error risk

## User Stories

### US-1: Pre-Provisioned Instance Discovery
**As a** DR administrator  
**I want** the system to automatically discover pre-provisioned instances tagged for AllowLaunchingIntoThisInstance  
**So that** I can identify target instances for DRS recovery without manual inventory

**Acceptance Criteria:**
- System discovers instances with `AWSDRS=AllowLaunchingIntoThisInstance` tag
- Discovery filters for instances in `stopped` state
- Discovery works across multiple AWS accounts via role assumption
- Instances are matched to source servers by Name tag
- Discovery results include instance metadata (ID, name, IP, subnet, security groups)
- Unmatched instances are logged with clear warnings
- Discovery validates target instance prerequisites (stopped state, correct tags, network configuration)

### US-2: Name Tag Matching for Primary-DR Instance Pairs
**As a** DR administrator  
**I want** instances matched between primary and DR regions by Name tag  
**So that** the system knows which pre-provisioned instance to use for each source server

**Acceptance Criteria:**
- Name tag matching uses normalized comparison (lowercase, strip whitespace)
- Exact match required between source server hostname and target instance Name tag
- 1:1 mapping validation ensures no duplicate matches
- Unmatched instances are logged with detailed information
- Matching algorithm handles naming conventions: `{customer}-{environment}-{workload}-{role}{number}`
- Fuzzy matching tolerance for minor variations (configurable)
- Matching results stored in DynamoDB for audit trail
- API endpoint returns matching pairs for validation before recovery

### US-3: DRS Launch Configuration for AllowLaunchingIntoThisInstance
**As a** DR administrator  
**I want** DRS launch configuration automatically updated with target instance IDs  
**So that** recovery jobs launch into pre-provisioned instances instead of creating new ones

**Acceptance Criteria:**
- Two-step configuration process:
  1. Disable conflicting DRS settings (`copyTags=false`, `copyPrivateIp=false`, `targetInstanceTypeRightSizingMethod=NONE`)
  2. Configure `launchIntoInstanceProperties.launchIntoEC2InstanceID`
- Configuration validates target instance is stopped before applying
- Configuration validates AWSDRS tag is present on target instance
- Configuration stored in DynamoDB for idempotency and rollback
- Configuration changes are logged with before/after state
- API endpoint allows manual configuration override if needed
- Validation prevents configuration of instances that don't meet prerequisites

### US-4: Failover with AllowLaunchingIntoThisInstance
**As a** DR administrator  
**I want** to execute failover that launches into pre-provisioned DR instances  
**So that** I can recover workloads quickly while preserving network configuration

**Acceptance Criteria:**
- Failover validates all source servers are in `CONTINUOUS` replication state
- Failover validates all target instances are in `stopped` state
- DRS recovery job created with correct source server IDs
- Recovery job monitored with 30-second polling interval
- Job status tracked: PENDING → STARTED → COMPLETED/FAILED
- Recovery instance IDs captured and validated against expected target instances
- Post-recovery validation confirms instances launched into correct targets
- Recovery preserves target instance IP address and network configuration
- Failover duration measured and logged (target: <30 minutes for 100 instances)
- CloudWatch metrics published for recovery duration and success rate

### US-5: Failback to Original Source Instances
**As a** DR administrator  
**I want** to execute failback that returns workloads to original source instances  
**So that** I can restore normal operations without creating new instances

**Acceptance Criteria:**
- Failback identifies original source instances (now stopped in primary region)
- Failback matches DR recovery instances to original source instances using metadata
- **CRITICAL: Staging account tracking for replication consistency**:
  - During failover (is_drill=false), the staging/target account ID is stored in the execution record
  - During failback, the system retrieves the original staging account ID from the failover execution
  - DRS agent is installed on recovery instance to replicate back to the SAME staging account used during failover
  - This ensures replication consistency and prevents agents from replicating to different accounts
  - If original staging account cannot be determined, failback is blocked with clear error message
- **CRITICAL: Private IP address preservation**:
  - System captures source instance private IP before failover
  - System captures target instance private IP during failover
  - System validates recovery instance has expected private IP after failover
  - System validates recovery instance private IP before initiating reverse replication
  - System blocks failback if private IP mismatch detected (indicates wrong target instance)
  - System preserves original private IP when failing back to pre-provisioned instances
  - System validates private IP preserved after failback completes
  - Private IP preservation eliminates need for DNS updates or application reconfiguration
- **Prerequisites validated before reverse replication**:
  - Recovery instance is running in DR region
  - Network connectivity verified: DR region → Primary region (port 1500)
  - Security groups allow DRS replication traffic
  - IAM instance profile has DRS permissions
  - Private IP matches expected value (if validation enabled)
- **DRS agent automatically installed on recovery instance** during `reverse_replication()` API call
- Agent configured to replicate from DR region back to original staging account
- Reverse replication initiated from DR instances to original source instances
- Reverse replication monitored until `CONTINUOUS` state with lag <60 seconds
- Agent installation failures detected and reported with remediation steps
- DRS launch configuration updated to target original source instance IDs
- Failback recovery job created and monitored
- Post-failback validation confirms instances launched into original source instances
- Original instance IDs, IPs, and network configuration preserved
- Failback duration measured and logged (target: <45 minutes for 100 instances)
- DR recovery instances terminated after successful failback

### US-6: Wave-Based Orchestration with AllowLaunchingIntoThisInstance
**As a** DR administrator  
**I want** AllowLaunchingIntoThisInstance integrated with existing wave-based orchestration  
**So that** I can execute phased recovery with instance identity preservation

**Acceptance Criteria:**
- Wave-based execution processes instances by `dr:wave` tag
- Each wave configures AllowLaunchingIntoThisInstance before starting recovery
- Wave dependencies respected (Wave N+1 waits for Wave N completion)
- Parallel execution within waves (up to 20 concurrent DRS jobs)
- Wave status tracked in DynamoDB execution history
- Post-wave validation runs before proceeding to next wave
- Wave failures don't block subsequent waves (configurable)
- Step Functions state machine orchestrates wave execution
- CloudWatch metrics track wave-level success rates and duration

### US-7: Cross-Account AllowLaunchingIntoThisInstance
**As a** DR administrator  
**I want** AllowLaunchingIntoThisInstance to work across AWS accounts  
**So that** I can implement hub-and-spoke DR architecture

**Acceptance Criteria:**
- Cross-account role assumption for source and target accounts
- IAM permissions validated before configuration
- DRS clients created with assumed role credentials
- EC2 operations use correct account context
- Cross-account KMS keys supported for encrypted volumes
- External ID required for security
- Role assumption failures clearly reported with remediation guidance
- Cross-account operations logged in CloudTrail for both accounts

### US-8: Validation and Error Handling
**As a** DR administrator  
**I want** comprehensive validation and error handling  
**So that** I can identify and resolve issues before they impact recovery

**Acceptance Criteria:**
- Pre-recovery validation checks:
  - Source servers in `CONTINUOUS` replication state
  - Target instances in `stopped` state
  - AWSDRS tags present on all target instances
  - Name tag matching successful for all instances
  - IAM permissions sufficient for recovery operations
  - Network configuration compatible (subnet, security groups)
- Validation failures block recovery with clear error messages
- Validation results stored in DynamoDB for audit
- API endpoint for on-demand validation without executing recovery
- Retry logic with exponential backoff for transient failures
- DRS API rate limit handling (see AWSM-1112)
- Failed operations stored in DynamoDB for manual retry
- SNS notifications for critical failures

### US-9: Monitoring and Observability
**As a** DR administrator  
**I want** comprehensive monitoring and metrics  
**So that** I can track recovery performance and troubleshoot issues

**Acceptance Criteria:**
- CloudWatch metrics published:
  - Recovery job duration (per wave, per instance, total)
  - Success rate (percentage of successful recoveries)
  - Replication lag before recovery
  - Instance matching accuracy
  - Configuration success rate
- CloudWatch Logs capture:
  - Detailed recovery progress
  - Configuration changes (before/after)
  - Validation results
  - Error messages with context
- DynamoDB execution history stores:
  - Recovery job metadata
  - Instance matching results
  - Configuration state
  - Validation results
  - Performance metrics
- CloudWatch Dashboard displays:
  - Real-time recovery status
  - Historical performance trends
  - Error rates and types
  - Capacity utilization

### US-10: API Integration
**As a** DR administrator  
**I want** REST API endpoints for AllowLaunchingIntoThisInstance operations  
**So that** I can integrate with UI and automation tools

**Acceptance Criteria:**
- API endpoints:
  - `POST /drs/recovery/configure-allow-launching` - Configure target instances
  - `POST /drs/recovery/validate` - Validate prerequisites
  - `POST /drs/recovery/failover` - Execute failover
  - `POST /drs/recovery/failback` - Execute failback
  - `GET /drs/recovery/status/{executionId}` - Get recovery status
  - `GET /drs/recovery/instances/match` - Get instance matching results
- API validates required parameters
- API returns structured JSON responses
- API supports both synchronous and asynchronous invocation
- API includes proper authentication and authorization
- API rate limiting to prevent abuse
- API documentation with examples

### US-11: Frontend UI Integration
**As a** DR administrator  
**I want** a UI to manage AllowLaunchingIntoThisInstance operations  
**So that** I can execute recovery without using CLI tools

**Acceptance Criteria:**
- UI displays pre-provisioned instances with status indicators
- UI shows instance matching results (primary ↔ DR pairs)
- UI allows manual override of instance matching
- UI provides failover wizard with validation steps
- UI provides failback wizard with reverse replication monitoring
- UI displays real-time recovery progress
- UI shows recovery history with performance metrics
- UI includes troubleshooting guidance for common errors
- UI supports filtering by account, region, wave, status

### US-12: Testing and Validation Framework
**As a** developer  
**I want** comprehensive test coverage  
**So that** I can ensure AllowLaunchingIntoThisInstance works correctly

**Acceptance Criteria:**
- Unit tests (59 tests):
  - DRS API integration (18 tests)
  - Instance matching algorithm (12 tests)
  - Error handling (14 tests)
  - Configuration validation (15 tests)
- Integration tests (37 tests):
  - Recovery job creation (15 tests)
  - Job monitoring (10 tests)
  - Failover/failback cycles (12 tests)
- End-to-end tests (8 tests):
  - 10-instance recovery
  - 50-instance recovery
  - 100-instance recovery
  - Complete failover + failback cycle
- Performance tests:
  - RTO measurement for various scales
  - Concurrent recovery job handling
  - API response time under load
- All tests pass in CI/CD pipeline
- Test coverage >80% for new code

### US-13: Reverse Replication Prerequisites Validation
**As a** DR administrator  
**I want** automated validation of reverse replication prerequisites before initiating failback  
**So that** I can ensure failback will succeed and avoid failed reverse replication attempts

**Acceptance Criteria:**
- **Network Connectivity Validation**:
  - Verify recovery instance can reach primary region on port 1500 (DRS replication traffic)
  - Verify recovery instance can reach AWS DRS endpoints on port 443 (HTTPS)
  - Test connectivity using VPC Reachability Analyzer or network probes
  - Report specific network path failures (security group, NACL, route table)
- **Security Group Validation**:
  - Verify recovery instance security groups allow outbound TCP 1500
  - Verify recovery instance security groups allow outbound TCP 443
  - Check for overly restrictive egress rules
  - Validate security group associations are correct
- **IAM Permissions Validation**:
  - Verify recovery instance has IAM instance profile attached
  - Verify instance profile has DRS agent permissions
  - Check for `drs:SendAgentMetricsForDrs`, `drs:SendAgentLogsForDrs`, `drs:SendChannelCommandResultForDrs`
  - Validate STS assume role permissions if cross-account
- **DRS Service Validation**:
  - Verify DRS service is initialized in primary region
  - Verify staging area subnet is configured
  - Check DRS service quotas are not exceeded
  - Validate replication server capacity
- **Recovery Instance Validation**:
  - Verify recovery instance is in `running` state
  - Verify instance has sufficient disk space for agent
  - Check instance OS is supported by DRS agent
  - Validate instance metadata service is accessible
- **Validation Reporting**:
  - Generate detailed validation report with pass/fail per check
  - Provide remediation steps for each failed check
  - Block failback initiation if critical checks fail
  - Allow override for non-critical checks (with warning)
- **API Integration**:
  - `POST /drs/recovery/validate-reverse-replication` endpoint
  - Returns validation report with detailed results
  - Supports dry-run mode (validation only, no changes)
- **Automatic Agent Installation**:
  - Document that DRS automatically installs agent during `reverse_replication()` API call
  - Validate prerequisites BEFORE calling `reverse_replication()`
  - Monitor agent installation progress after API call
  - Detect and report agent installation failures with remediation steps

## Non-Functional Requirements

### NFR-1: Performance
- **RTO Target**: <30 minutes for 100 instances (vs 2-4 hours without pattern)
- **Instance Matching**: <10 seconds for 1000 instance pairs
- **Configuration Update**: <5 seconds per source server
- **API Response Time**: <2 seconds for synchronous endpoints
- **Recovery Job Polling**: 30-second intervals (configurable)
- **Lambda Timeout**: 15 minutes (900 seconds)
- **Lambda Memory**: 1024 MB (increased from 512 MB for instance matching)

### NFR-2: Reliability
- **Recovery Success Rate**: >95% for properly configured instances
- **Instance Matching Accuracy**: >98% with standard naming conventions
- **Configuration Idempotency**: Safe to retry without side effects
- **Partial Failure Handling**: Continue with successful instances, report failures
- **Automatic Retry**: Exponential backoff for transient failures (3 attempts)
- **Rollback Capability**: Restore previous DRS configuration on failure

### NFR-3: Security
- **Cross-Account Access**: IAM roles only (no credentials stored)
- **External ID**: Required for all cross-account role assumptions
- **Least Privilege**: Minimal IAM permissions for each operation
- **Encryption**: TLS for all API calls, KMS for data at rest
- **Audit Trail**: All operations logged in CloudTrail
- **Sensitive Data**: No credentials or secrets in logs
- **Tag-Based Access Control**: Restrict operations to tagged resources

### NFR-4: Scalability
- **Instance Limit**: Support up to 1000 instances per recovery
- **Concurrent Jobs**: Up to 20 DRS jobs in parallel (DRS service limit)
- **Account Limit**: Support up to 50 AWS accounts
- **Wave Limit**: Support up to 20 waves per recovery plan
- **API Rate Limits**: Handle DRS API throttling gracefully
- **DynamoDB Capacity**: Auto-scaling for execution history table

### NFR-5: Observability
- **Structured Logging**: JSON format with correlation IDs
- **CloudWatch Metrics**: Custom metrics for all key operations
- **Distributed Tracing**: X-Ray integration for request tracing
- **Alerting**: SNS notifications for critical failures
- **Dashboard**: Real-time recovery status visualization
- **Historical Analysis**: 90-day retention for execution history

### NFR-6: Maintainability
- **Code Standards**: PEP 8 compliance, type hints, docstrings
- **Modular Design**: Separate modules for matching, configuration, recovery
- **Configuration Management**: Environment variables for all settings
- **Documentation**: Comprehensive API docs, runbooks, troubleshooting guides
- **Version Control**: Git with semantic versioning
- **Deployment**: CloudFormation for infrastructure as code

## Technical Constraints

### TC-1: AWS Service Limits
- **DRS**: Maximum 20 concurrent recovery jobs per region
- **DRS**: Maximum 100 source servers per recovery job
- **DRS**: Maximum 300 source servers per account (extendable to 600 with extended source servers)
- **Lambda**: 15-minute maximum execution time
- **Step Functions**: 1-year maximum execution time
- **EC2**: Instance type availability varies by region/AZ

### TC-2: Prerequisites
- **Source Servers**: Must be in `CONTINUOUS` replication state
- **Target Instances**: Must be in `stopped` state
- **Tags**: AWSDRS=AllowLaunchingIntoThisInstance required on target instances
- **Name Tags**: Must match between source servers and target instances
- **IAM Permissions**: Orchestration role must have EC2 launch permissions
- **Network**: Target instances must have compatible network configuration

### TC-3: DRS API Behavior
- **Configuration Sequence**: Must disable conflicting settings before configuring launchIntoInstanceProperties
- **Tags Parameter**: Must NOT include tags in start_recovery() call (skips conversion phase)
- **Drill Mode**: AllowLaunchingIntoThisInstance works but terminates instances after drill
- **Failback**: Only available for Recovery mode (not Drill mode)
- **Reverse Replication**: Requires recovery instance to be running

### TC-4: Network Requirements
- **Outbound HTTPS**: Port 443 to DRS endpoints
- **Outbound DRS**: Port 1500 for replication traffic
- **VPC Endpoints**: Recommended for private subnets
- **Security Groups**: Must allow DRS traffic
- **Subnets**: Must have available IP addresses

## Dependencies

### External Dependencies
- **AWS SDK (boto3)**: DRS, EC2, STS, DynamoDB, CloudWatch APIs
- **AWS DRS Service**: Elastic Disaster Recovery
- **AWS Systems Manager**: For agent installation (existing feature)
- **AWS Step Functions**: For wave-based orchestration
- **AWS CloudWatch**: For metrics and logging
- **AWS DynamoDB**: For state management and execution history

### Internal Dependencies
- **DRS Agent Deployer**: Existing feature for agent installation
- **Wave-Based Orchestration**: Existing Step Functions workflow
- **Cross-Account Utilities**: Existing `lambda/shared/cross_account.py`
- **DRS Utilities**: Existing `lambda/shared/drs_utils.py`
- **Tag Sync**: Existing manual tag sync capability
- **Resource Discovery**: Existing Resource Explorer integration

### New Modules Required
- `lambda/shared/drs_client.py` - DRS API client with AllowLaunchingIntoThisInstance
- `lambda/shared/instance_matcher.py` - Name tag matching algorithm
- `lambda/shared/drs_job_monitor.py` - Recovery job monitoring
- `lambda/shared/drs_error_handler.py` - Error handling and retry logic

## Success Metrics

### Recovery Performance
- **RTO Improvement**: 88-92% reduction vs standard DRS recovery
- **Target RTO**: <30 minutes for 100 instances
- **Measured**: End-to-end recovery duration from job start to validation complete

### Instance Matching Accuracy
- **Target**: >98% successful matches with standard naming
- **Measured**: Matched instances / Total instances
- **Tracking**: Unmatched instances logged for analysis

### Configuration Success Rate
- **Target**: >99% successful configurations
- **Measured**: Successful configurations / Total attempts
- **Tracking**: Configuration failures categorized by error type

### Recovery Success Rate
- **Target**: >95% successful recoveries
- **Measured**: Successful recoveries / Total recovery attempts
- **Tracking**: Failures categorized by phase (validation, configuration, recovery, post-recovery)

### Failback Success Rate
- **Target**: >90% successful failbacks
- **Measured**: Successful failbacks / Total failback attempts
- **Tracking**: Failback duration and failure reasons

### API Performance
- **Target**: <2 seconds for synchronous endpoints
- **Measured**: P50, P95, P99 response times
- **Tracking**: API errors and rate limit hits

## Out of Scope

The following are explicitly out of scope for this feature:

- **DRS Agent Installation**: Covered by existing DRS Agent Deployer feature
- **DRS Replication Configuration**: Uses DRS defaults
- **Custom Launch Templates**: Uses DRS-generated templates
- **Agent Updates/Upgrades**: Manual process
- **Cost Optimization**: Separate feature
- **Automated DR Testing**: Separate feature
- **Multi-Region Active-Active**: Different architecture pattern
- **Application-Level Failover**: Application responsibility
- **Database Replication**: Separate from DRS block-level replication

## Related Documentation

### Existing Documentation
- [DRS Agent Deployer Spec](./../drs-agent-deployer/requirements.md)
- [DRS Recovery and Failback Guide](../../docs/guides/DRS_RECOVERY_AND_FAILBACK_COMPLETE_GUIDE.md)
- [DRS Cross-Account Setup](../../docs/guides/DRS_CROSS_ACCOUNT_SETUP_VERIFICATION.md)
- [Wave-Based Orchestration](../../archive/docs/HealthEdge/Cloud%20Migration/Disaster%20Recovery/7-Implementation%20%26%20Runbooks/Enterprise%20DR%20Orchestration%20Platform%20Design%201.0%20--/AWSM-1103-Enterprise-Wave-Orchestration.md)

### Research Documentation
- [AllowLaunchingIntoThisInstance Research](../../archive/docs/HealthEdge/Cloud%20Migration/Disaster%20Recovery/7-Implementation%20%26%20Runbooks/Enterprise%20DR%20Orchestration%20Platform%20Design%201.0%20--/User%20Stories/AWSM-1112-%20DR-E02%20DRS%20Integration%20and%20EC2%20Recovery/AWSM-1111-%20Implement%20DRS%20Orchestration%20Module/README.md)

### AWS Documentation
- [AWS DRS User Guide](https://docs.aws.amazon.com/drs/latest/userguide/)
- [DRS Launch Configuration](https://docs.aws.amazon.com/drs/latest/userguide/launch-settings.html)
- [DRS API Reference](https://docs.aws.amazon.com/drs/latest/APIReference/)

## Glossary

- **AllowLaunchingIntoThisInstance**: DRS pattern that launches recovery instances into pre-provisioned EC2 instances
- **Source Server**: Original server being protected by DRS
- **Recovery Instance**: EC2 instance launched during DRS recovery
- **Target Instance**: Pre-provisioned EC2 instance used as recovery target
- **Failover**: Recovery from primary region to DR region
- **Failback**: Return from DR region to primary region
- **Reverse Replication**: Replication from DR region back to primary region
- **RTO**: Recovery Time Objective (target time to restore operations)
- **RPO**: Recovery Point Objective (acceptable data loss)
- **Wave**: Group of instances recovered together in sequence
- **Launch Configuration**: DRS settings controlling how recovery instances are launched
- **Replication State**: Status of DRS replication (CONTINUOUS, BACKLOG, etc.)
