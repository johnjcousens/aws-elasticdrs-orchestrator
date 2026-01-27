# Requirements Document: Deployment Flexibility

## Overview

This feature adds deployment flexibility to the AWS DRS Orchestration Solution to support multiple deployment scenarios including standalone operation, API-only deployments, and integration with the HRP (High-level Recovery Platform).

## User Stories

### US-1: Simplified IAM Management
**As a** DevOps engineer  
**I want** a single unified IAM role for all Lambda functions  
**So that** I can manage permissions more easily and reduce CloudFormation template complexity

**Acceptance Criteria:**
- AC-1.1: Master stack creates a single UnifiedOrchestrationRole when OrchestrationRoleArn parameter is empty
- AC-1.2: All 7 Lambda functions use the unified role
- AC-1.3: Unified role contains all permissions from the original 7 individual roles
- AC-1.4: CloudFormation template is ~500 lines smaller (7 role definitions removed from lambda-stack.yaml)
- AC-1.5: Backward compatibility maintained - default deployment behavior unchanged

### US-2: External Role Integration
**As an** HRP platform architect  
**I want** to provide my own IAM role for Lambda execution  
**So that** I can integrate DRS Orchestration into HRP's centralized permission management

**Acceptance Criteria:**
- AC-2.1: OrchestrationRoleArn parameter accepts external IAM role ARN
- AC-2.2: When OrchestrationRoleArn is provided, no role is created by the stack
- AC-2.3: All Lambda functions use the provided external role
- AC-2.4: Role ARN validation enforces correct IAM ARN format
- AC-2.5: Stack outputs include the role ARN being used (created or provided)

### US-3: API-Only Deployment
**As a** platform integrator  
**I want** to deploy only the API components without the frontend  
**So that** I can integrate DRS Orchestration into existing UIs or use it as a backend service

**Acceptance Criteria:**
- AC-3.1: DeployFrontend parameter controls frontend deployment (default: true)
- AC-3.2: When DeployFrontend=false, no frontend resources are created (S3, CloudFront, frontend-builder Lambda)
- AC-3.3: API Gateway and backend Lambda functions still deploy when DeployFrontend=false
- AC-3.4: Frontend-related outputs are conditionally created based on DeployFrontend
- AC-3.5: API-only deployment completes successfully without frontend dependencies

### US-4: Flexible Deployment Modes
**As a** solutions architect  
**I want** multiple deployment configuration options  
**So that** I can choose the right deployment mode for different use cases

**Acceptance Criteria:**
- AC-4.1: Default mode (OrchestrationRoleArn=empty, DeployFrontend=true) works unchanged
- AC-4.2: API-only standalone mode (OrchestrationRoleArn=empty, DeployFrontend=false) deploys successfully
- AC-4.3: HRP integration with frontend (OrchestrationRoleArn=provided, DeployFrontend=true) works
- AC-4.4: Full HRP integration (OrchestrationRoleArn=provided, DeployFrontend=false) works
- AC-4.5: All deployment modes pass CloudFormation validation

### US-5: Seamless Migration
**As an** existing DRS Orchestration user  
**I want** to update to the new unified role architecture  
**So that** I can benefit from simplified IAM management without service disruption

**Acceptance Criteria:**
- AC-5.1: Existing stacks can be updated in-place without manual intervention
- AC-5.2: CloudFormation handles role migration automatically (create new, update Lambdas, delete old)
- AC-5.3: No downtime during stack update
- AC-5.4: All Lambda functions continue working after update
- AC-5.5: Old individual roles are cleanly removed after migration

## Functional Requirements

### FR-1: CloudFormation Parameters
- FR-1.1: Add OrchestrationRoleArn parameter (String, default empty, with IAM ARN pattern validation)
- FR-1.2: Add DeployFrontend parameter (String, default 'true', allowed values: 'true'/'false')
- FR-1.3: Parameters must include descriptive help text
- FR-1.4: Parameter validation must prevent invalid inputs

### FR-2: CloudFormation Conditions
- FR-2.1: CreateOrchestrationRole condition evaluates to true when OrchestrationRoleArn is empty
- FR-2.2: DeployFrontendCondition evaluates to true when DeployFrontend equals 'true'
- FR-2.3: Conditions must be used correctly on resources and outputs

### FR-3: Unified IAM Role
- FR-3.1: UnifiedOrchestrationRole resource created only when CreateOrchestrationRole is true
- FR-3.2: Role must include all 17 policy statements from original 7 roles:
  - DynamoDBAccess (from ApiHandler, Orchestration, ExecutionFinder, ExecutionPoller)
  - StepFunctionsAccess (from ApiHandler) - **MUST include states:SendTaskHeartbeat for long-running DRS operations**
  - DRSReadAccess (from ApiHandler, Orchestration, ExecutionPoller)
  - DRSWriteAccess (from ApiHandler, Orchestration) - includes drs:CreateRecoveryInstanceForDrs, drs:GetAgentInstallationAssetsForDrs, drs:IssueAgentCertificateForDrs, drs:CreateSourceServerForDrs (agent management for future enhanced features)
  - EC2Access (from ApiHandler, Orchestration) - includes ec2:CreateLaunchTemplateVersion
  - IAMAccess (from ApiHandler, Orchestration)
  - STSAccess (from ApiHandler, Orchestration)
  - KMSAccess (from ApiHandler)
  - CloudFormationAccess (from ApiHandler, CustomResource, BucketCleaner)
  - S3Access (from CustomResource, BucketCleaner)
  - CloudFrontAccess (from CustomResource)
  - LambdaInvokeAccess (from ApiHandler, ExecutionFinder)
  - EventBridgeAccess (from ApiHandler)
  - SSMAccess (from Orchestration) - includes ssm:CreateOpsItem for automation tracking
  - SNSAccess (from Orchestration, NotificationFormatter)
  - CloudWatchAccess (from ExecutionPoller)
- FR-3.3: Role must include AWS Lambda basic execution managed policy
- FR-3.4: Role name must follow pattern: ${ProjectName}-orchestration-role-${Environment}
- FR-3.5: Role must support all features documented in implementation docs (pre-provisioned instances, replication settings management, cross-account operations)

### FR-4: Lambda Stack Simplification
- FR-4.1: Remove all 7 individual IAM role definitions from lambda-stack.yaml
- FR-4.2: Add OrchestrationRoleArn as required parameter to lambda-stack.yaml
- FR-4.3: All 7 Lambda functions must reference !Ref OrchestrationRoleArn for their Role property
- FR-4.4: Lambda function definitions otherwise unchanged

### FR-5: Conditional Frontend Deployment
- FR-5.1: FrontendStack resource must have Condition: DeployFrontendCondition
- FR-5.2: Frontend-related resources created only when condition is true
- FR-5.3: API and backend resources always created regardless of frontend condition

### FR-6: Stack Outputs
- FR-6.1: ApiEndpoint output always present (no condition)
- FR-6.2: OrchestrationRoleArn output uses Fn::If to return created or provided role ARN
- FR-6.3: CloudFrontUrl output has Condition: DeployFrontendCondition
- FR-6.4: CloudFrontDistributionId output has Condition: DeployFrontendCondition
- FR-6.5: FrontendBucketName output has Condition: DeployFrontendCondition

### FR-7: Parameter Passing
- FR-7.1: Master template passes OrchestrationRoleArn to LambdaStack using Fn::If
- FR-7.2: Fn::If returns UnifiedOrchestrationRole.Arn when CreateOrchestrationRole is true
- FR-7.3: Fn::If returns OrchestrationRoleArn parameter value when CreateOrchestrationRole is false

## Non-Functional Requirements

### NFR-1: Backward Compatibility
- NFR-1.1: Default deployment (no parameter overrides) must work identically to current behavior
- NFR-1.2: Existing stacks must update successfully without manual intervention
- NFR-1.3: No breaking changes to API endpoints or Lambda function behavior

### NFR-2: CloudFormation Best Practices
- NFR-2.1: All templates must pass cfn-lint validation
- NFR-2.2: Conditional resource creation must use Condition attribute (not Fn::If on resource)
- NFR-2.3: Conditional outputs must use Condition attribute
- NFR-2.4: All patterns validated against AWS CloudFormation documentation

### NFR-3: Security
- NFR-3.1: Unified role must maintain resource-level restrictions where possible
- NFR-3.2: Condition keys must be used for service-specific access (e.g., KMS via service)
- NFR-3.3: External role ARN validation must prevent invalid IAM ARNs
- NFR-3.4: No permission escalation compared to original 7 roles
- NFR-3.5: Role must include all critical DRS permissions identified in IAM reference documentation:
  - drs:CreateRecoveryInstanceForDrs (prevents AccessDeniedException during recovery)
  - ec2:CreateLaunchTemplateVersion (prevents UnauthorizedOperation failures)
  - states:SendTaskHeartbeat (prevents timeout on long-running operations)
  - ssm:CreateOpsItem (enables OpsItems for automation tracking and operational visibility)
  - drs:GetAgentInstallationAssetsForDrs (enables future agent management capabilities)
  - drs:IssueAgentCertificateForDrs (enables future agent management capabilities)
  - drs:CreateSourceServerForDrs (enables future agent management capabilities)

### NFR-4: Maintainability
- NFR-4.1: Inline comments must document each policy's purpose and source roles
- NFR-4.2: Template structure must be clear and logical
- NFR-4.3: Parameter descriptions must be comprehensive
- NFR-4.4: Code reduction of ~500 lines improves maintainability

### NFR-5: Testing
- NFR-5.1: All 4 deployment modes must be tested
- NFR-5.2: Migration from existing 7-role deployment must be tested
- NFR-5.3: All Lambda functions must be verified working after deployment
- NFR-5.4: API Gateway endpoints must be tested in all modes

## Technical Constraints

### TC-1: CloudFormation Limitations
- TC-1.1: Must use CloudFormation native features (no custom resources for core logic)
- TC-1.2: Condition evaluation happens at stack creation/update time
- TC-1.3: Cannot conditionally pass parameters to nested stacks (must use Fn::If for values)

### TC-2: IAM Constraints
- TC-2.1: Role ARN must be valid IAM role ARN format
- TC-2.2: External role must have Lambda service trust policy
- TC-2.3: External role must have all required permissions for Lambda functions
- TC-2.4: External role must include permissions for all features in implementation docs:
  - Pre-provisioned instance recovery (AllowLaunchingIntoThisInstance)
  - DRS replication settings management
  - Cross-account DRS operations
  - Configuration drift detection and remediation

### TC-3: Deployment Constraints
- TC-3.1: Must work with existing deployment script (./scripts/deploy.sh)
- TC-3.2: Must support parameter overrides via --parameter-overrides flag
- TC-3.3: Must maintain compatibility with S3 deployment bucket structure

### TC-4: Implementation Documentation Compatibility
- TC-4.1: Unified role must support all features described in DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md
- TC-4.2: Unified role must support all features described in DRS_REPLICATION_SETTINGS_MANAGEMENT.md
- TC-4.3: No additional permissions required beyond current 7 roles for documented features

## Success Criteria

### Deployment Success
- All 4 deployment modes deploy successfully
- CloudFormation validation passes for all templates
- No errors during stack creation or update

### Functional Success
- All Lambda functions execute successfully with unified role
- API Gateway endpoints respond correctly
- Step Functions executions complete successfully
- Frontend works when deployed (DeployFrontend=true)

### Migration Success
- Existing stacks update in-place without errors
- No service disruption during update
- Old roles cleanly removed after migration

### Code Quality
- ~500 lines removed from lambda-stack.yaml
- All templates pass cfn-lint
- Inline documentation complete

## Out of Scope

- Changes to Lambda function code or logic
- Changes to API Gateway configuration
- Changes to Step Functions state machine definitions
- Changes to DynamoDB table schemas
- Changes to frontend application code
- Performance optimization
- Cost optimization beyond reduced CloudFormation complexity

## Dependencies

- AWS CloudFormation service
- Existing DRS Orchestration infrastructure
- S3 deployment bucket
- IAM service for role management
- Lambda service for function execution
- Implementation documentation (DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md, DRS_REPLICATION_SETTINGS_MANAGEMENT.md)
- IAM reference documentation (DRS_IAM_AND_PERMISSIONS_REFERENCE.md)

## Risks and Mitigations

### Risk 1: Unified Role Security
**Risk:** Single role has broader permissions than individual function-specific roles  
**Impact:** Larger blast radius if role is compromised  
**Mitigation:** Resource-level restrictions, condition keys, regular permission audits

### Risk 2: Migration Complexity
**Risk:** Updating existing stacks might fail during role transition  
**Impact:** Service disruption, manual recovery required  
**Mitigation:** Thorough testing of update scenarios, CloudFormation handles atomic updates

### Risk 3: External Role Misconfiguration
**Risk:** Provided external role missing required permissions  
**Impact:** Lambda function failures, API errors  
**Mitigation:** Clear documentation of required permissions, validation during deployment

### Risk 4: Conditional Logic Errors
**Risk:** Incorrect Fn::If or Condition usage  
**Impact:** Wrong resources created or missing outputs  
**Mitigation:** CloudFormation best practices research completed, cfn-lint validation

## Validation Checklist

- [ ] All user stories have clear acceptance criteria
- [ ] All functional requirements are testable
- [ ] Non-functional requirements are measurable
- [ ] Technical constraints are documented
- [ ] Success criteria are specific
- [ ] Out of scope items are clear
- [ ] Dependencies are identified
- [ ] Risks have mitigations
- [ ] Implementation documentation analyzed for permission requirements
- [ ] IAM reference documentation reviewed for critical permissions
- [ ] All missing permissions identified and documented (states:SendTaskHeartbeat, ssm:CreateOpsItem)
- [ ] Pre-provisioned instance feature compatibility verified
- [ ] Replication settings management compatibility verified
- [ ] Cross-account operations compatibility verified
- [ ] DRS-Settings-Tool permissions analyzed - 100% coverage confirmed
- [ ] drs-tools reference code analyzed - 100% coverage confirmed
- [ ] DR-FACTORY reference code analyzed - all permissions included for future enhanced features
- [ ] AWS DRS service authorization reference analyzed - comprehensive permission list documented

## Appendix A: Comprehensive DRS Permissions Reference

This appendix documents ALL AWS Elastic Disaster Recovery (DRS) permissions identified through comprehensive research of AWS service authorization reference, managed policies, and reference implementations.

### DRS Core Operations (Read)

**Source Server Management:**
- `drs:DescribeSourceServers` - List and describe source servers
- `drs:DescribeRecoverySnapshots` - View recovery point snapshots
- `drs:ListExtensibleSourceServers` - List servers eligible for extension

**Recovery Instance Management:**
- `drs:DescribeRecoveryInstances` - List and describe recovery instances

**Job Management:**
- `drs:DescribeJobs` - List recovery/failback jobs
- `drs:DescribeJobLogItems` - View job execution logs

**Configuration Management:**
- `drs:GetLaunchConfiguration` - Retrieve launch settings
- `drs:GetReplicationConfiguration` - Retrieve replication settings
- `drs:GetFailbackReplicationConfiguration` - Retrieve failback replication settings
- `drs:DescribeLaunchConfigurationTemplates` - List launch templates
- `drs:DescribeReplicationConfigurationTemplates` - List replication templates
- `drs:ListLaunchActions` - List pre/post-launch actions

**Source Network Management:**
- `drs:DescribeSourceNetworks` - List source networks for network recovery

**Staging Accounts:**
- `drs:ListStagingAccounts` - List staging AWS accounts

**Tagging:**
- `drs:ListTagsForResource` - List resource tags

### DRS Core Operations (Write)

**Recovery Operations:**
- `drs:StartRecovery` - Initiate disaster recovery (launches recovery instances)
- `drs:CreateRecoveryInstanceForDrs` - Create recovery instance (internal operation)
- `drs:TerminateRecoveryInstances` - Terminate recovery instances
- `drs:DisconnectRecoveryInstance` - Disconnect recovery instance from DRS

**Failback Operations:**
- `drs:StartFailbackLaunch` - Initiate failback to source infrastructure
- `drs:StopFailback` - Stop failback operation
- `drs:ReverseReplication` - Reverse replication direction for failback

**Source Server Operations:**
- `drs:CreateSourceServerForDrs` - Create source server entry (agent installation)
- `drs:CreateExtendedSourceServer` - Extend source server for additional regions
- `drs:DeleteSourceServer` - Remove source server from DRS
- `drs:DisconnectSourceServer` - Disconnect source server from DRS
- `drs:RetryDataReplication` - Retry failed replication

**Replication Control:**
- `drs:StartReplication` - Start data replication for source server
- `drs:StopReplication` - Stop data replication

**Configuration Management:**
- `drs:UpdateLaunchConfiguration` - Modify launch settings
- `drs:UpdateReplicationConfiguration` - Modify replication settings
- `drs:UpdateFailbackReplicationConfiguration` - Modify failback replication settings
- `drs:CreateLaunchConfigurationTemplate` - Create launch template
- `drs:UpdateLaunchConfigurationTemplate` - Update launch template
- `drs:DeleteLaunchConfigurationTemplate` - Delete launch template
- `drs:CreateReplicationConfigurationTemplate` - Create replication template
- `drs:UpdateReplicationConfigurationTemplate` - Update replication template
- `drs:DeleteReplicationConfigurationTemplate` - Delete replication template

**Launch Actions:**
- `drs:PutLaunchAction` - Add/update pre/post-launch action
- `drs:DeleteLaunchAction` - Remove launch action

**Source Network Operations:**
- `drs:CreateSourceNetwork` - Create source network for network recovery
- `drs:DeleteSourceNetwork` - Delete source network
- `drs:StartSourceNetworkRecovery` - Start network recovery
- `drs:StartSourceNetworkReplication` - Start network replication
- `drs:StopSourceNetworkReplication` - Stop network replication
- `drs:AssociateSourceNetworkStack` - Associate CloudFormation stack with source network
- `drs:ExportSourceNetworkCfnTemplate` - Export CloudFormation template for source network

**Job Management:**
- `drs:DeleteJob` - Delete completed job
- `drs:DeleteRecoveryInstance` - Delete recovery instance

**Service Initialization:**
- `drs:InitializeService` - Initialize DRS service in AWS region

**Tagging:**
- `drs:TagResource` - Add tags to DRS resources
- `drs:UntagResource` - Remove tags from DRS resources

### DRS Agent Operations (Permission-Only Actions)

**Agent Installation:**
- `drs:GetAgentInstallationAssetsForDrs` - Download agent installation files
- `drs:IssueAgentCertificateForDrs` - Issue agent authentication certificate
- `drs:SendClientLogsForDrs` - Agent sends logs to DRS
- `drs:SendClientMetricsForDrs` - Agent sends metrics to DRS

**Agent Communication:**
- `drs:NotifyAgentAuthenticationForDrs` - Agent authentication notification
- `drs:NotifyAgentConnectedForDrs` - Agent connection notification
- `drs:NotifyAgentDisconnectedForDrs` - Agent disconnection notification
- `drs:GetAgentCommandForDrs` - Agent retrieves commands from DRS
- `drs:GetChannelCommandsForDrs` - Agent retrieves channel commands
- `drs:SendChannelCommandResultForDrs` - Agent sends command results

**Agent Replication:**
- `drs:NotifyAgentReplicationProgressForDrs` - Agent reports replication progress
- `drs:GetAgentReplicationInfoForDrs` - Agent retrieves replication info
- `drs:UpdateAgentReplicationInfoForDrs` - Agent updates replication info
- `drs:UpdateAgentReplicationProcessStateForDrs` - Agent updates replication state
- `drs:GetAgentRuntimeConfigurationForDrs` - Agent retrieves runtime config
- `drs:GetAgentConfirmedResumeInfoForDrs` - Agent retrieves resume info
- `drs:UpdateAgentBacklogForDrs` - Agent updates replication backlog
- `drs:UpdateAgentConversionInfoForDrs` - Agent updates conversion info
- `drs:UpdateAgentSourcePropertiesForDrs` - Agent updates source properties
- `drs:SendAgentLogsForDrs` - Agent sends detailed logs
- `drs:SendAgentMetricsForDrs` - Agent sends detailed metrics
- `drs:SendVolumeStatsForDrs` - Agent sends volume statistics

**Agent Snapshots:**
- `drs:GetAgentSnapshotCreditsForDrs` - Agent retrieves snapshot credits
- `drs:NotifyConsistencyAttainedForDrs` - Agent notifies consistency achieved
- `drs:NotifyVolumeEventForDrs` - Agent notifies volume events
- `drs:CreateConvertedSnapshotForDrs` - Create converted snapshot
- `drs:BatchCreateVolumeSnapshotGroupForDrs` - Batch create volume snapshots
- `drs:BatchDeleteSnapshotRequestForDrs` - Batch delete snapshot requests
- `drs:DescribeSnapshotRequestsForDrs` - Describe snapshot requests

**Failback Client Operations:**
- `drs:AssociateFailbackClientToRecoveryInstanceForDrs` - Associate failback client
- `drs:GetFailbackCommandForDrs` - Failback client retrieves commands
- `drs:GetFailbackLaunchRequestedForDrs` - Check if failback launch requested
- `drs:GetSuggestedFailbackClientDeviceMappingForDrs` - Get device mapping suggestions
- `drs:UpdateFailbackClientDeviceMappingForDrs` - Update device mapping
- `drs:UpdateFailbackClientLastSeenForDrs` - Update failback client heartbeat

**Replication Server Operations:**
- `drs:DescribeReplicationServerAssociationsForDrs` - Describe replication server associations
- `drs:NotifyReplicationServerAuthenticationForDrs` - Replication server authentication
- `drs:UpdateReplicationCertificateForDrs` - Update replication certificate

### Required Dependent Service Permissions

**IMPORTANT: Cross-Account Architecture**

The unified orchestration role operates in a **shared orchestration account** and controls DRS in workload accounts via cross-account role assumption. The orchestration role does NOT need DRS service-linked role permissions because:

1. **DRS service roles** (AWSServiceRoleForElasticDisasterRecovery, AWSElasticDisasterRecoveryReplicationServerRole, etc.) are created automatically by DRS in workload accounts
2. **DRS service** assumes its own roles to perform EC2/EBS operations (RunInstances, CreateVolume, etc.)
3. **Orchestration Lambda** only calls DRS APIs - DRS handles the infrastructure operations

**Architecture Flow:**
```
Orchestration Account (Lambda with UnifiedOrchestrationRole)
    ↓ sts:AssumeRole (cross-account)
Workload Account (Cross-Account Role with DRS permissions)
    ↓ Calls DRS APIs (drs:StartRecovery, drs:DescribeJobs, etc.)
DRS Service in Workload Account
    ↓ Automatically assumes its own service roles
    - AWSServiceRoleForElasticDisasterRecovery
    - AWSElasticDisasterRecoveryReplicationServerRole
    - AWSElasticDisasterRecoveryConversionServerRole
    - AWSElasticDisasterRecoveryRecoveryInstanceRole
```

**EC2 Permissions (Orchestration Operations Only):**
- `ec2:DescribeInstances` - Query instances for orchestration decisions
- `ec2:DescribeInstanceStatus` - Check instance health
- `ec2:DescribeInstanceTypes` - Validate instance type availability
- `ec2:DescribeInstanceAttribute` - Get instance configuration
- `ec2:DescribeVolumes` - Query volume information
- `ec2:DescribeSnapshots` - Query snapshot information
- `ec2:DescribeImages` - Query AMI information
- `ec2:DescribeSecurityGroups` - Query security groups
- `ec2:DescribeSubnets` - Query subnet information
- `ec2:DescribeVpcs` - Query VPC information
- `ec2:DescribeAvailabilityZones` - List availability zones
- `ec2:DescribeAccountAttributes` - Get account limits
- `ec2:CreateTags` - Tag resources during orchestration
- `ec2:DescribeTags` - Query resource tags
- `ec2:CreateLaunchTemplateVersion` - Update launch templates (for pre-provisioned instances)
- `ec2:DescribeLaunchTemplates` - Query launch templates
- `ec2:DescribeLaunchTemplateVersions` - Query template versions
- `ec2:ModifyLaunchTemplate` - Modify launch templates

**Note:** EC2 operations like RunInstances, CreateVolume, AttachVolume, etc. are performed by DRS service roles, NOT by the orchestration role.

**IAM Permissions:**
- `iam:PassRole` - Pass IAM roles when needed (limited scope)
- `iam:GetInstanceProfile` - Get instance profile details
- `iam:ListInstanceProfiles` - List available instance profiles
- `iam:ListRoles` - List IAM roles

**Note:** The orchestration role does NOT create or manage DRS service roles. Those are created automatically by DRS during service initialization in workload accounts.

**KMS Permissions:**
- `kms:DescribeKey` - Describe KMS keys for encrypted volumes
- `kms:ListAliases` - List KMS key aliases
- `kms:CreateGrant` - Create grants for EBS encryption (when orchestration creates resources)

**CloudWatch Permissions:**
- `cloudwatch:PutMetricData` - Publish custom metrics
- `cloudwatch:GetMetricStatistics` - Query metrics for monitoring

**CloudFormation Permissions (Source Network Recovery):**
- `cloudformation:CreateStack` - Create CloudFormation stack
- `cloudformation:UpdateStack` - Update CloudFormation stack
- `cloudformation:DescribeStacks` - Describe stacks
- `cloudformation:DescribeStackResource` - Describe stack resources
- `cloudformation:ListStacks` - List stacks

**S3 Permissions (Source Network Recovery):**
- `s3:GetObject` - Read S3 objects
- `s3:PutObject` - Write S3 objects
- `s3:GetBucketLocation` - Get bucket location
- `s3:ListAllMyBuckets` - List all buckets

**SSM Permissions (Launch Actions):**
- `ssm:DescribeDocument` - Describe SSM document
- `ssm:DescribeInstanceInformation` - Describe managed instances
- `ssm:SendCommand` - Send command to instances
- `ssm:StartAutomationExecution` - Start automation
- `ssm:ListDocuments` - List SSM documents
- `ssm:ListCommandInvocations` - List command invocations
- `ssm:GetParameter` - Get parameter value
- `ssm:PutParameter` - Store parameter value
- `ssm:GetDocument` - Get document content
- `ssm:GetAutomationExecution` - Get automation execution status
- `ssm:CreateOpsItem` - Create OpsCenter item for tracking

**Step Functions Permissions:**
- `states:SendTaskHeartbeat` - Send heartbeat for long-running tasks

**Resource Groups Permissions:**
- `resource-groups:ListGroups` - List resource groups

**Elastic Load Balancing Permissions:**
- `elasticloadbalancing:DescribeLoadBalancers` - Describe load balancers

**License Manager Permissions:**
- `license-manager:ListLicenseConfigurations` - List license configurations

### Permission Categories by Use Case

**CRITICAL: Orchestration Role vs DRS Service Roles**

The unified orchestration role operates in a **shared orchestration account** and does NOT need DRS service-linked role permissions. Here's the separation of responsibilities:

**Orchestration Role Responsibilities (What We Need):**
- Call DRS APIs (drs:StartRecovery, drs:DescribeJobs, etc.)
- Query AWS resources for orchestration decisions (ec2:Describe*, drs:Describe*)
- Tag resources during orchestration (ec2:CreateTags, drs:TagResource)
- Update launch configurations (drs:UpdateLaunchConfiguration, ec2:CreateLaunchTemplateVersion)
- Manage orchestration state (DynamoDB, Step Functions, SNS)
- Cross-account role assumption (sts:AssumeRole)

**DRS Service Role Responsibilities (What DRS Handles Automatically):**
- Launch recovery instances (ec2:RunInstances)
- Create and attach EBS volumes (ec2:CreateVolume, ec2:AttachVolume)
- Create snapshots (ec2:CreateSnapshot)
- Manage replication servers (ec2:RunInstances for replication infrastructure)
- Manage conversion servers (ec2:RunInstances for conversion infrastructure)
- Create security groups (ec2:CreateSecurityGroup)
- Register AMIs (ec2:RegisterImage)
- All infrastructure operations during recovery

**DRS Service Roles (Created Automatically in Workload Accounts):**
1. **AWSServiceRoleForElasticDisasterRecovery** - Main service-linked role
2. **AWSElasticDisasterRecoveryReplicationServerRole** - For replication servers
3. **AWSElasticDisasterRecoveryConversionServerRole** - For conversion servers
4. **AWSElasticDisasterRecoveryRecoveryInstanceRole** - For recovery instances

**Orchestration Platform (Current Implementation):**
- All DRS Read operations (drs:Describe*, drs:Get*, drs:List*)
- Recovery operations: StartRecovery, TerminateRecoveryInstances
- Configuration: UpdateLaunchConfiguration, UpdateReplicationConfiguration
- EC2 query operations: DescribeInstances, DescribeVolumes, DescribeSnapshots
- EC2 tagging: CreateTags
- EC2 launch template updates: CreateLaunchTemplateVersion, ModifyLaunchTemplate
- IAM: PassRole (limited scope)
- Step Functions: SendTaskHeartbeat
- SSM: CreateOpsItem

**Agent Installation (Future Enhanced Features):**
- GetAgentInstallationAssetsForDrs
- IssueAgentCertificateForDrs
- CreateSourceServerForDrs
- SendClientLogsForDrs
- SendClientMetricsForDrs

**Failback Operations (Future Enhanced Features):**
- StartFailbackLaunch
- StopFailback
- ReverseReplication
- AssociateFailbackClientToRecoveryInstanceForDrs
- GetFailbackCommandForDrs
- UpdateFailbackClientDeviceMappingForDrs

**Source Network Recovery (Future Enhanced Features):**
- CreateSourceNetwork
- StartSourceNetworkRecovery
- AssociateSourceNetworkStack
- ExportSourceNetworkCfnTemplate
- CloudFormation: CreateStack, UpdateStack, DescribeStacks
- S3: GetObject, PutObject

### AWS Managed Policy References

**AWSElasticDisasterRecoveryAgentInstallationPolicy:**
- Used for: Installing DRS agent on source servers
- Key permissions: GetAgentInstallationAssetsForDrs, CreateSourceServerForDrs, IssueAgentCertificateForDrs

**AWSElasticDisasterRecoveryFailbackInstallationPolicy:**
- Used for: Installing failback client on recovery instances
- Key permissions: AssociateFailbackClientToRecoveryInstanceForDrs, GetSuggestedFailbackClientDeviceMappingForDrs

**AWSElasticDisasterRecoveryConsoleFullAccess_v2:**
- Used for: Full administrative access to DRS console
- Includes: All DRS actions, EC2 operations, IAM PassRole, SSM operations

**AWSElasticDisasterRecoveryEc2InstancePolicy:**
- Used for: EC2 instances running DRS agent (cross-region/cross-AZ recovery)
- Attached as: EC2 instance profile

### Research Sources

1. **AWS Service Authorization Reference**: https://docs.aws.amazon.com/service-authorization/latest/reference/list_awselasticdisasterrecovery.html
2. **AWS Managed Policies**: AWSElasticDisasterRecoveryAgentInstallationPolicy, AWSElasticDisasterRecoveryFailbackInstallationPolicy, AWSElasticDisasterRecoveryConsoleFullAccess_v2
3. **Implementation Documentation**: DRS_ALLOW_LAUNCHING_INTO_THIS_INSTANCE_RESEARCH.md, DRS_REPLICATION_SETTINGS_MANAGEMENT.md, DRS_IAM_AND_PERMISSIONS_REFERENCE.md
4. **Reference Code**: DRS-Settings-Tool, drs-tools, DR-FACTORY

### Notes

- **Permission-only actions** (marked with `[permission only]` in AWS docs) are internal DRS operations used by agents and cannot be called directly via AWS API
- **Dependent service permissions** are required because DRS orchestrates multiple AWS services during recovery operations
- **Resource-level permissions** should be applied where possible to follow principle of least privilege
- **Condition keys** (aws:RequestTag, aws:TagKeys, drs:CreateAction) provide additional security controls
