# DRS Agent Deployer - Requirements

## Feature Overview

Automated deployment of AWS Elastic Disaster Recovery (DRS) agents to EC2 instances across multiple AWS accounts with support for cross-account replication patterns. This feature enables centralized DR orchestration from a single account while supporting both same-account and cross-account replication scenarios.

## User Stories

### US-1: Auto-Discovery of DR-Enabled Instances
**As a** DR administrator  
**I want** the system to automatically discover EC2 instances tagged for DR  
**So that** I don't have to manually maintain instance lists

**Acceptance Criteria:**
- System discovers instances with configurable tag filters (default: `dr:enabled=true` AND `dr:recovery-strategy=drs`)
- Tag filters can be customized via event parameters or environment variables
- Discovery works across multiple AWS accounts via role assumption
- Instances are grouped by configurable wave tag (default: `dr:wave`)
- Only running instances are included in discovery
- Discovery results include instance metadata (ID, name, wave, priority, IP, type, platform)
- Tag configuration supports multiple tag key-value pairs

### US-2: Same-Account DRS Replication
**As a** DR administrator  
**I want** to deploy DRS agents that replicate within the same AWS account  
**So that** I can implement regional DR failover

**Acceptance Criteria:**
- Lambda accepts `source_account_id`, `source_region`, `target_region`
- Agents installed in source account replicate to same account's target region
- SSM command includes correct region parameter
- DRS source servers appear in same account's DRS console
- Deployment status is tracked and reported

### US-3: Cross-Account DRS Replication
**As a** DR administrator  
**I want** to deploy DRS agents in a source account that replicate to a separate staging account  
**So that** I can implement multi-account DR with dedicated DR infrastructure

**Acceptance Criteria:**
- Lambda accepts `source_account_id`, `staging_account_id`, `source_role_arn`, `staging_role_arn`
- System assumes role in source account for agent installation
- System assumes role in staging account for DRS verification
- SSM command includes `StagingAccountID` parameter
- DRS source servers appear in staging account's DRS console (not source account)
- Deployment pattern is automatically detected and logged

### US-4: SSM-Based Agent Installation
**As a** DR administrator  
**I want** agents installed via AWS Systems Manager  
**So that** I can leverage existing SSM infrastructure and avoid manual installation

**Acceptance Criteria:**
- System verifies SSM agents are online before deployment
- Uses AWS-provided document `AWSDisasterRecovery-InstallDRAgentOnInstance`
- Waits up to 5 minutes for SSM agents to come online
- Monitors command execution status for each instance
- Reports success/failure for each instance
- Supports configurable timeout for command completion

### US-5: Wave-Based Orchestration
**As a** DR administrator  
**I want** instances grouped by DR wave  
**So that** I can deploy agents in organized phases

**Acceptance Criteria:**
- Instances are grouped by `dr:wave` tag value
- Deployment results show instances organized by wave
- Wave information is included in all status reports
- Unassigned instances are grouped as "unassigned" wave

### US-6: Cross-Account Role Assumption
**As a** DR administrator  
**I want** the system to use cross-account IAM roles  
**So that** I don't need to manage credentials for each account

**Acceptance Criteria:**
- System assumes roles using STS AssumeRole
- External ID is required for security
- Separate roles for source and staging accounts
- Role assumption failures are clearly reported
- Session credentials are used for all AWS API calls

### US-7: Deployment Status Monitoring
**As a** DR administrator  
**I want** real-time status updates during deployment  
**So that** I can monitor progress and troubleshoot issues

**Acceptance Criteria:**
- CloudWatch Logs show detailed deployment progress
- Status includes: instances discovered, SSM agents online, agents deployed
- Command execution status is tracked per instance
- DRS source server registration is verified
- Total deployment duration is reported
- Failures include detailed error messages

### US-8: API Gateway Integration
**As a** DR administrator  
**I want** to trigger agent deployment via REST API  
**So that** I can integrate with UI and automation tools

**Acceptance Criteria:**
- POST endpoint `/drs/agents/deploy` accepts deployment parameters
- API validates required parameters
- Returns deployment status and command ID
- Supports both synchronous and asynchronous invocation
- Includes proper authentication and authorization
- Returns structured JSON response

### US-9: Frontend UI Integration
**As a** DR administrator  
**I want** a UI to deploy agents and monitor status  
**So that** I can manage DR without using CLI tools

**Acceptance Criteria:**
- UI shows list of accounts available for deployment
- Form accepts source account, staging account (optional), regions
- Deployment pattern is automatically detected and displayed
- Real-time status updates during deployment
- Results show instances deployed, source servers registered
- Error messages are user-friendly
- Deployment history is accessible

### US-10: Multi-Account Batch Deployment
**As a** DR administrator  
**I want** to deploy agents to multiple accounts in parallel  
**So that** I can efficiently manage large-scale DR deployments

**Acceptance Criteria:**
- Accepts array of account configurations
- Deploys to accounts in parallel (configurable concurrency)
- Each account deployment is independent
- Aggregate results show status per account
- Failures in one account don't block others
- Overall deployment status is reported

### US-11: Backward Compatibility
**As a** DR administrator  
**I want** existing integrations to continue working  
**So that** I don't break current deployments

**Acceptance Criteria:**
- Old parameter names (`account_id`, `role_arn`) still work
- Automatically maps old parameters to new structure
- Defaults to same-account pattern if staging account not specified
- Existing test events and API calls continue to work
- No breaking changes to response structure

### US-13: Configurable Tag Filters
**As a** DR administrator  
**I want** to configure which tags identify DR-enabled instances  
**So that** I can use my organization's tagging standards

**Acceptance Criteria:**
- Tag filters can be specified in event parameters
- Default tags: `dr:enabled=true` AND `dr:recovery-strategy=drs`
- Wave tag is configurable (default: `dr:wave`)
- Priority tag is configurable (default: `dr:priority`)
- Supports multiple tag filters with AND logic
- Tag configuration can be set via environment variables
- Invalid tag configurations return clear error messages
- Tag filters are validated before instance discovery

### US-14: Agent Deployment Status Tracking & Visualization
**As a** DR administrator  
**I want** visual status tracking of agent deployments with success/failure metrics  
**So that** I can quickly identify and troubleshoot failed deployments per account

**Acceptance Criteria:**
- Dashboard displays agent deployment status card with visual indicators
- Shows total agents deployed vs failed (success rate percentage)
- Displays status breakdown by account (account name, success count, failure count)
- Failed instances are highlighted with error details
- Clicking on failed instances shows detailed error messages
- Status updates in real-time during deployment
- Historical deployment data is persisted in DynamoDB
- Export capability for failed instances report (CSV/JSON)
- Filter by date range, account, deployment pattern
- Visual indicators: green (success), red (failed), yellow (in-progress), gray (pending)

### US-15: CloudFormation Stack Integration
**As a** DevOps engineer  
**I want** the Lambda function deployed via CloudFormation  
**So that** infrastructure is managed as code

**Acceptance Criteria:**
- Lambda function defined in `cfn/lambda-stack.yaml`
- Uses existing `UnifiedOrchestrationRole` from master stack
- Environment variables configurable via parameters
- CloudWatch Logs group created automatically
- Function timeout and memory are configurable
- Outputs include function ARN and name

## Non-Functional Requirements

### NFR-1: Performance
- Agent discovery completes within 30 seconds for up to 100 instances
- SSM command execution monitored with 20-second intervals
- Total deployment time under 10 minutes for typical workloads
- Lambda function timeout: 15 minutes (900 seconds)
- Lambda memory: 512 MB

### NFR-2: Security
- All cross-account access uses IAM roles (no credentials stored)
- External ID required for role assumption
- Least privilege permissions for all roles
- All API calls logged in CloudTrail
- Sensitive data not logged (credentials, tokens)
- DRS replication uses TLS encryption in transit

### NFR-3: Reliability
- Handles transient AWS API failures with retries
- Graceful degradation if some instances fail
- Partial success reported clearly
- Idempotent operations (safe to retry)
- No data loss on failure

### NFR-4: Observability
- Detailed CloudWatch Logs for all operations
- Structured logging with JSON format
- Metrics for deployment success/failure rates
- Deployment duration tracked
- Error rates monitored

### NFR-5: Maintainability
- Code follows PEP 8 standards
- Type hints on all functions
- Comprehensive docstrings
- Unit tests for core logic
- Integration tests for AWS interactions
- Clear error messages

### NFR-6: Scalability
- Supports up to 1000 instances per deployment
- Handles up to 50 concurrent account deployments
- No hard-coded limits on account count
- Efficient pagination for large result sets

## Technical Constraints

### TC-1: AWS Service Limits
- DRS: ~$0.028/hour per source server
- Lambda: 15-minute maximum execution time
- SSM: Command execution timeout configurable
- STS: Role session duration 1 hour default

### TC-2: Prerequisites
- Source account must have EC2 instances with DR tags
- Instances must have SSM agent installed and online
- Instance IAM role must have DRS agent installation policy
- Cross-account roles must exist in all accounts
- DRS service must be initialized in staging account

### TC-3: Network Requirements
- Instances must have outbound HTTPS (443) access
- DRS endpoints must be reachable
- SSM endpoints must be reachable
- VPC endpoints recommended for private subnets

## Dependencies

### External Dependencies
- AWS SDK (boto3)
- AWS Systems Manager
- AWS Elastic Disaster Recovery (DRS)
- AWS STS (for role assumption)
- AWS CloudWatch Logs

### Internal Dependencies
- `cfn/master-template.yaml` - Master CloudFormation stack
- `cfn/lambda-stack.yaml` - Lambda function definitions
- `cfn/cross-account-role-stack.yaml` - Cross-account IAM roles
- Existing `UnifiedOrchestrationRole` with STS permissions

## Success Metrics

### Deployment Success Rate
- Target: >95% successful deployments
- Measured: Successful deployments / Total deployments

### Time to Deploy
- Target: <5 minutes for typical workload (10-20 instances)
- Measured: End-to-end deployment duration

### Agent Registration Rate
- Target: >98% of installed agents register with DRS
- Measured: Registered source servers / Agents installed

### API Response Time
- Target: <2 seconds for API endpoint response
- Measured: Time from request to response (async mode)

### Error Recovery Time
- Target: <10 minutes to identify and resolve deployment failures
- Measured: Time from failure to resolution

---

## US-15: Automated Extended Source Server Configuration

**As a** DR administrator  
**I want** source servers to be automatically extended to the target account after agent installation  
**So that** I can scale beyond the 300 source server per-account limit without manual intervention

### Acceptance Criteria

1. **Automatic Extension Detection**
   - Detect when agents are installed in a staging/source account
   - Identify if the account is configured for extended source servers
   - Check if target account is configured in deployment settings

2. **Extension Execution**
   - After successful agent installation, automatically extend source servers to target account
   - Use `create-extended-source-server` API call with source server ARN
   - Apply appropriate tags: `Name`, `ExtendedFrom`, `DeploymentID`
   - Handle already-extended servers gracefully (skip with info message)

3. **Cross-Account Permissions**
   - Verify target account has necessary IAM permissions
   - Verify DRS service-linked role exists in target account
   - Verify cross-account trust relationship is configured
   - Fail gracefully with clear error messages if permissions missing

4. **Configuration**
   - Add `target_account_id` field to deployment configuration
   - Add `auto_extend_source_servers` boolean flag (default: false)
   - Support per-account extension configuration
   - Allow disabling extension for specific deployments

5. **Status Tracking**
   - Track extension status in deployment history
   - Record: source server IDs, extension success/failure, target account
   - Include extension metrics in deployment summary
   - Log extension attempts and results

6. **Error Handling**
   - Retry failed extensions up to 3 times with exponential backoff
   - Continue deployment even if extension fails (log warning)
   - Provide clear error messages for common failures:
     - Missing target account permissions
     - Source server not ready for extension
     - Target account DRS not initialized
     - Network/API errors

7. **Validation**
   - Verify source servers appear in target account after extension
   - Check replication status in target account
   - Validate source server count doesn't exceed limits
   - Alert if approaching capacity limits (e.g., 280/300 servers)

### Technical Notes

- Extension must happen AFTER agents are installed and source servers are registered
- Use `list-extensible-source-servers` to get available servers for extension
- Extension is idempotent - safe to retry
- Target account must have DRS initialized in the same region
- Cross-account KMS keys must be configured if using custom encryption
- Supports capacity scaling architecture (300 + 300 = 600 total servers)

---

## Out of Scope

The following are explicitly out of scope for this feature:

- DRS recovery instance launch (separate feature)
- DRS failback operations (separate feature)
- Agent updates/upgrades (manual process)
- Custom replication configuration (uses DRS defaults)
- Agent uninstallation (manual process)
- Cost optimization recommendations
- Automated DR testing/drills

## Related Documentation

- [DRS Agent Deployment Guide](../../../docs/guides/DRS_AGENT_DEPLOYMENT_GUIDE.md)
- [DRS Cross-Account Replication](../../../docs/guides/DRS_CROSS_ACCOUNT_REPLICATION.md)
- [DRS Cross-Account Orchestration](../../../docs/DRS_CROSS_ACCOUNT_ORCHESTRATION.md)
- [DRS Agent Deployment Frontend Integration](../../../docs/guides/DRS_AGENT_DEPLOYMENT_FRONTEND_INTEGRATION.md)
