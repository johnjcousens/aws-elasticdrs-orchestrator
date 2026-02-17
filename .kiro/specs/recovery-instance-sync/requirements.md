# Requirements Document

## Introduction

The Recovery Instance Sync feature addresses a critical performance bottleneck in the DR Orchestration Platform. Currently, the Recovery Plans page takes 20+ seconds to load because the `checkExistingRecoveryInstances()` function makes expensive synchronous API calls to AWS DRS and EC2 services on every page load. This feature implements a DynamoDB caching pattern with background synchronization to reduce page load time to under 3 seconds while maintaining data accuracy.

## Glossary

- **Recovery_Instance**: An EC2 instance created by AWS DRS during a recovery or drill operation
- **Source_Server**: A server protected by AWS DRS that can be recovered
- **Recovery_Plan**: A collection of waves that define the order and grouping of servers for recovery
- **Wave**: A group of servers within a recovery plan that are recovered together
- **DRS_API**: AWS Elastic Disaster Recovery service API
- **EC2_API**: AWS Elastic Compute Cloud service API
- **Recovery_Instance_Cache**: DynamoDB table storing recovery instance information
- **Background_Sync**: EventBridge-triggered Lambda function that periodically updates the cache
- **Wave_Completion**: The event when all servers in a wave have finished their recovery operation
- **Cross_Account**: Scenario where recovery instances exist in a different AWS account than the orchestration platform

## Requirements

### Requirement 1: DynamoDB Cache Table

**User Story:** As a system architect, I want a DynamoDB table to cache recovery instance information, so that the UI can query cached data instead of making expensive API calls.

#### Acceptance Criteria

1. THE Recovery_Instance_Cache SHALL store recovery instance records with sourceServerId as partition key
2. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include recoveryInstanceId, ec2InstanceId, ec2InstanceState, sourceServerName, name, privateIp, publicIp, instanceType, launchTime, region, accountId, sourceExecutionId, sourcePlanName, and lastSyncTime
3. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include replicationStagingAccountId to identify which account the DRS agent replicates to
4. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include source infrastructure configuration fields: sourceVpcId, sourceSubnetId, sourceSecurityGroupIds, and sourceInstanceProfile for failover and reverse replication scenarios
5. THE Recovery_Instance_Cache SHALL support queries by sourceServerId with O(1) lookup time
6. THE Recovery_Instance_Cache SHALL use on-demand billing mode to handle variable query patterns
7. THE Recovery_Instance_Cache SHALL enable point-in-time recovery for data protection

### Requirement 2: Wave Completion Sync

**User Story:** As a DR operator, when a wave completes execution, I want recovery instance information to be immediately available in the database, so that I can view instance details without delay.

#### Acceptance Criteria

1. WHEN a wave execution completes, THE Execution_Handler SHALL query DRS_API for recovery instances created during that wave
2. WHEN recovery instances are found, THE Execution_Handler SHALL enrich each instance with EC2_API details including Name tag, privateIp, publicIp, instanceType, and launchTime
3. WHEN recovery instance data is enriched, THE Execution_Handler SHALL write records to Recovery_Instance_Cache with all required fields
4. WHEN writing to Recovery_Instance_Cache, THE Execution_Handler SHALL update existing server information with ec2InstanceId, privateIp, and publicIp
5. IF DRS_API or EC2_API calls fail, THEN THE Execution_Handler SHALL log the error and continue wave completion without blocking

### Requirement 3: Background Sync Lambda

**User Story:** As a system administrator, I want recovery instance data to be automatically synced in the background, so that the cache stays current without manual intervention.

#### Acceptance Criteria

1. THE Background_Sync SHALL be triggered by EventBridge every 5 minutes
2. WHEN Background_Sync executes, THE Background_Sync SHALL query DRS_API describe_recovery_instances for all configured regions
3. WHEN recovery instances are found, THE Background_Sync SHALL enrich each instance with EC2_API details
4. WHEN enrichment completes, THE Background_Sync SHALL update Recovery_Instance_Cache with current data
5. WHEN Background_Sync encounters errors, THE Background_Sync SHALL log errors and continue processing remaining regions
6. THE Background_Sync SHALL complete execution within 5 minutes to avoid overlapping invocations
7. THE Background_Sync SHALL handle Cross_Account scenarios by assuming appropriate IAM roles

### Requirement 4: Optimized Query Function

**User Story:** As a DR operator, I want the Recovery Plans page to load in under 3 seconds, so that I can quickly view and manage recovery plans.

#### Acceptance Criteria

1. WHEN checkExistingRecoveryInstances is called, THE Data_Management_Handler SHALL query Recovery_Instance_Cache instead of DRS_API
2. WHEN querying Recovery_Instance_Cache, THE Data_Management_Handler SHALL retrieve all recovery instance records for the plan's source servers
3. WHEN recovery instance records are found, THE Data_Management_Handler SHALL return the cached data in the same format as the original implementation
4. WHEN recovery instance records are not found, THE Data_Management_Handler SHALL return empty results without calling DRS_API
5. THE Data_Management_Handler SHALL complete checkExistingRecoveryInstances in under 3 seconds for plans with up to 100 servers
6. THE Data_Management_Handler SHALL maintain backward compatibility with existing frontend code
7. THE Data_Management_Handler SHALL support three invocation methods: Frontend with API, API Only, and Direct Lambda invocation
8. WHEN invoked from Frontend with API, THE Data_Management_Handler SHALL parse API Gateway event format
9. WHEN invoked from API Only, THE Data_Management_Handler SHALL parse direct API request format
10. WHEN invoked via Direct Lambda invocation, THE Data_Management_Handler SHALL parse direct function call format

### Requirement 5: Optimized Terminate Recovery Instances

**User Story:** As a DR operator, when I terminate recovery instances after a recovery plan ends or is cancelled, I want the operation to complete quickly without expensive API calls, so that cleanup happens efficiently.

#### Acceptance Criteria

1. WHEN terminateRecoveryInstances is called, THE Data_Management_Handler SHALL query Recovery_Instance_Cache to find instances belonging to the execution
2. WHEN querying Recovery_Instance_Cache for termination, THE Data_Management_Handler SHALL use Scan with FilterExpression on sourceExecutionId
3. WHEN recovery instances are found in cache, THE Data_Management_Handler SHALL group instances by region for efficient batch termination
4. WHEN terminating instances, THE Data_Management_Handler SHALL call drs:TerminateRecoveryInstances for each region with batch of instance IDs
5. WHEN instances are successfully terminated, THE Data_Management_Handler SHALL delete corresponding records from Recovery_Instance_Cache
6. WHEN cache deletion occurs, THE Data_Management_Handler SHALL use batch_writer for efficient deletion
7. IF termination fails for a region, THEN THE Data_Management_Handler SHALL log the error and continue with remaining regions
8. THE Data_Management_Handler SHALL reduce API calls to DRS_API by 100% compared to the original implementation that called describe_recovery_instances
9. THE Data_Management_Handler SHALL complete terminateRecoveryInstances in under 10 seconds for executions with up to 100 instances

### Requirement 6: CloudFormation Infrastructure

**User Story:** As a DevOps engineer, I want all infrastructure defined in CloudFormation, so that the feature can be deployed consistently across environments.

#### Acceptance Criteria

1. THE CloudFormation_Template SHALL create Recovery_Instance_Cache table with appropriate schema including replication and source infrastructure fields
2. THE CloudFormation_Template SHALL create EventBridge rule to trigger Background_Sync every 5 minutes
3. THE CloudFormation_Template SHALL grant Background_Sync Lambda permissions to call drs:DescribeRecoveryInstances
4. THE CloudFormation_Template SHALL grant Background_Sync Lambda permissions to call ec2:DescribeInstances
5. THE CloudFormation_Template SHALL grant Background_Sync Lambda permissions to write to Recovery_Instance_Cache
6. THE CloudFormation_Template SHALL grant Execution_Handler Lambda permissions to write to Recovery_Instance_Cache
7. THE CloudFormation_Template SHALL grant Data_Management_Handler Lambda permissions to read from Recovery_Instance_Cache
8. THE CloudFormation_Template SHALL grant Data_Management_Handler Lambda permissions to delete from Recovery_Instance_Cache for cleanup after termination
9. WHERE Cross_Account scenarios exist, THE CloudFormation_Template SHALL grant Background_Sync Lambda permissions to assume cross-account roles

### Requirement 7: Data Freshness and Accuracy

**User Story:** As a DR operator, I want recovery instance data to be accurate and current, so that I can make informed decisions about recovery operations.

#### Acceptance Criteria

1. WHEN a wave completes, THE Recovery_Instance_Cache SHALL contain recovery instance data within 30 seconds
2. WHEN Background_Sync runs, THE Recovery_Instance_Cache SHALL be updated with current data from DRS_API and EC2_API
3. WHEN recovery instances are terminated, THE Background_Sync SHALL update ec2InstanceState to reflect termination within 5 minutes
4. WHEN recovery instances are terminated via terminateRecoveryInstances, THE Data_Management_Handler SHALL immediately delete records from Recovery_Instance_Cache
5. THE Recovery_Instance_Cache SHALL include lastSyncTime timestamp for each record
6. WHEN querying Recovery_Instance_Cache, THE Data_Management_Handler SHALL return lastSyncTime to indicate data freshness

### Requirement 8: Error Handling and Resilience

**User Story:** As a system administrator, I want the feature to handle errors gracefully, so that temporary API failures don't break the UI or block recovery operations.

#### Acceptance Criteria

1. IF DRS_API calls fail during Background_Sync, THEN THE Background_Sync SHALL log the error and continue processing remaining regions
2. IF EC2_API calls fail during Background_Sync, THEN THE Background_Sync SHALL log the error and store partial data without EC2 details
3. IF Recovery_Instance_Cache writes fail, THEN THE Background_Sync SHALL log the error and continue processing
4. IF Recovery_Instance_Cache queries fail, THEN THE Data_Management_Handler SHALL return empty results and log the error
5. WHEN Cross_Account role assumption fails, THE Background_Sync SHALL log the error and skip that account
6. THE Background_Sync SHALL implement exponential backoff for retryable API errors
7. THE Background_Sync SHALL not retry non-retryable errors such as permission denied

### Requirement 9: Cross-Account Support

**User Story:** As a DR operator managing multiple AWS accounts, I want recovery instance sync to work across accounts, so that I can view instances from all protected accounts.

#### Acceptance Criteria

1. WHEN Background_Sync processes recovery instances, THE Background_Sync SHALL identify Cross_Account scenarios from protection group configuration
2. WHEN Cross_Account scenario is detected, THE Background_Sync SHALL assume the appropriate IAM role in the target account
3. WHEN assuming cross-account role, THE Background_Sync SHALL use externalId from target account configuration
4. WHEN cross-account role is assumed, THE Background_Sync SHALL query DRS_API and EC2_API in the target account
5. WHEN storing cross-account recovery instances, THE Recovery_Instance_Cache SHALL include accountId field
6. IF cross-account role assumption fails, THEN THE Background_Sync SHALL log the error and continue with remaining accounts

### Requirement 10: Monitoring and Observability

**User Story:** As a system administrator, I want visibility into sync operations, so that I can troubleshoot issues and monitor system health.

#### Acceptance Criteria

1. THE Background_Sync SHALL log the number of recovery instances processed in each sync operation
2. THE Background_Sync SHALL log the duration of each sync operation
3. THE Background_Sync SHALL log errors with sufficient context for troubleshooting
4. THE Background_Sync SHALL emit CloudWatch metrics for sync duration
5. THE Background_Sync SHALL emit CloudWatch metrics for sync success/failure count
6. THE Background_Sync SHALL emit CloudWatch metrics for API call counts
7. WHEN Background_Sync exceeds 4 minutes duration, THE Background_Sync SHALL emit a warning metric

### Requirement 11: Performance Optimization

**User Story:** As a DR operator, I want the Recovery Plans page to load quickly, so that I can respond rapidly during disaster recovery scenarios.

#### Acceptance Criteria

1. THE Data_Management_Handler SHALL complete checkExistingRecoveryInstances in under 3 seconds for plans with up to 100 servers
2. THE Data_Management_Handler SHALL reduce API calls to DRS_API by 100% compared to the original implementation
3. THE Data_Management_Handler SHALL reduce API calls to EC2_API by 100% compared to the original implementation
4. THE Background_Sync SHALL process up to 1000 recovery instances per sync operation
5. THE Background_Sync SHALL use pagination efficiently to minimize API calls
6. THE Recovery_Instance_Cache SHALL use efficient query patterns to minimize read latency

### Requirement 12: Manual Sync Operation

**User Story:** As a DR operator, I want to manually trigger a sync of recovery instance data, so that I can get the latest information on demand.

#### Acceptance Criteria

1. THE Data_Management_Handler SHALL provide a manual sync operation for recovery instances
2. THE Manual_Sync_Operation SHALL support three invocation methods: Frontend with API, API Only, and Direct Lambda invocation
3. WHEN invoked from Frontend with API, THE Manual_Sync_Operation SHALL parse API Gateway event format
4. WHEN invoked from API Only, THE Manual_Sync_Operation SHALL parse direct API request format
5. WHEN invoked via Direct Lambda invocation, THE Manual_Sync_Operation SHALL parse direct function call format
6. WHEN Manual_Sync_Operation executes, THE Manual_Sync_Operation SHALL query DRS_API and EC2_API for current recovery instance data
7. WHEN Manual_Sync_Operation completes, THE Manual_Sync_Operation SHALL update Recovery_Instance_Cache with fresh data
8. THE Manual_Sync_Operation SHALL return sync status including number of instances processed and any errors
9. THE Manual_Sync_Operation SHALL complete within 30 seconds for up to 100 recovery instances


### Requirement 13: Replication Configuration Support

**User Story:** As a DR operator planning failover or reverse replication, I want recovery instance records to include replication staging account and source infrastructure configuration, so that I can configure reverse replication after failover.

#### Acceptance Criteria

1. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include replicationStagingAccountId field
2. WHEN replicationStagingAccountId is populated, THE Recovery_Instance_Cache SHALL store the AWS account ID where the DRS agent replicates to
3. WHEN a DRS agent is installed to replicate to a target account, THE Recovery_Instance_Cache SHALL list the target account as the replicationStagingAccountId
4. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include sourceVpcId field for the source VPC
5. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include sourceSubnetId field for the source subnet
6. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include sourceSecurityGroupIds field as a list of source security group IDs
7. WHEN a recovery instance record is created, THE Recovery_Instance_Cache SHALL include sourceInstanceProfile field for the source IAM instance profile ARN
8. WHEN source infrastructure fields are not available, THE Recovery_Instance_Cache SHALL store null values for those fields
9. WHEN querying Recovery_Instance_Cache, THE Data_Management_Handler SHALL return replication and source infrastructure fields in the response
