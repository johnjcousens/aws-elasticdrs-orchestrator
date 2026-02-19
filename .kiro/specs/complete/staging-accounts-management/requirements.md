# Requirements Document: Staging Accounts Management

## Introduction

The Staging Accounts Management feature enables users to extend DRS replication capacity beyond the 300-server limit of a single target account by adding staging accounts. Each staging account provides an additional 300 servers of replication capacity. The system tracks capacity across all accounts (target + staging), displays combined metrics with per-account breakdowns, validates staging account access before adding, and provides warnings when approaching capacity limits.

## Glossary

- **Target_Account**: The primary AWS account where DRS recovery operations are performed and where recovered instances are launched
- **Staging_Account**: An additional AWS account configured to provide extended DRS replication capacity for the target account
- **Replication_Capacity**: The number of source servers that can actively replicate to an account (300 per account hard limit, 250 operational limit)
- **Recovery_Capacity**: The number of instances that can be recovered in the target account (4,000 instance limit)
- **Combined_Capacity**: The aggregate replication capacity across target account and all configured staging accounts
- **Operational_Limit**: The recommended safe capacity threshold of 250 servers per account (leaves 50-server safety buffer)
- **Hard_Limit**: The AWS-enforced maximum of 300 servers per account
- **DRS_System**: AWS Elastic Disaster Recovery service that replicates source servers
- **Capacity_Dashboard**: UI component displaying combined and per-account capacity metrics with status indicators
- **Validation_Process**: Pre-flight check that verifies staging account access and DRS initialization before adding

## Requirements

### Requirement 1: Add Staging Accounts

**User Story:** As a DR administrator, I want to add staging accounts to my target account, so that I can extend replication capacity beyond 300 servers.

#### Acceptance Criteria

1. WHEN a user opens the target account settings modal, THE System SHALL display a list of currently configured staging accounts with their status and server counts
2. WHEN a user clicks "Add Staging Account", THE System SHALL open a modal dialog with input fields for account ID, account name, role ARN, external ID, and region
3. WHEN a user provides staging account details and clicks "Validate Access", THE System SHALL attempt to assume the role and query DRS capacity in the staging account
4. WHEN validation succeeds, THE System SHALL display validation results showing role accessibility, DRS initialization status, current server counts, and capacity impact
5. WHEN validation fails, THE System SHALL display an error message explaining the failure reason
6. WHEN a user clicks "Add Account" after successful validation, THE System SHALL save the staging account configuration to the Target Accounts DynamoDB table
7. WHEN a staging account is added, THE System SHALL update the capacity dashboard to include the new account in combined metrics

### Requirement 2: Remove Staging Accounts

**User Story:** As a DR administrator, I want to remove staging accounts from my target account, so that I can adjust capacity configuration when staging accounts are no longer needed.

#### Acceptance Criteria

1. WHEN a user clicks "Remove" on a staging account in the settings modal, THE System SHALL prompt for confirmation before removal
2. WHEN removal is confirmed, THE System SHALL delete the staging account configuration from the Target Accounts DynamoDB table
3. WHEN a staging account is removed, THE System SHALL update the capacity dashboard to exclude the removed account from combined metrics
4. WHEN a staging account with active replicating servers is removed, THE System SHALL display a warning about the capacity impact

### Requirement 3: Validate Staging Account Access

**User Story:** As a DR administrator, I want to validate staging account access before adding it, so that I can ensure the account is properly configured and accessible.

#### Acceptance Criteria

1. WHEN validation is initiated, THE System SHALL attempt to assume the provided role ARN using the external ID
2. WHEN role assumption succeeds, THE System SHALL query DRS service in the specified region to check initialization status
3. WHEN DRS is initialized, THE System SHALL count total and replicating servers in the staging account
4. WHEN validation completes, THE System SHALL return results including role accessibility status, DRS initialization status, current server counts, and projected combined capacity
5. WHEN role assumption fails, THE System SHALL return an error indicating the role is not accessible
6. WHEN DRS is not initialized, THE System SHALL return an error indicating DRS must be initialized in the staging account

### Requirement 4: Display Combined Capacity Metrics

**User Story:** As a DR administrator, I want to see combined capacity across all accounts, so that I can understand total replication capacity and utilization.

#### Acceptance Criteria

1. WHEN the capacity dashboard loads, THE System SHALL query DRS capacity for the target account and all configured staging accounts
2. WHEN capacity data is retrieved, THE System SHALL calculate combined replicating servers as the sum across all accounts
3. WHEN displaying combined capacity, THE System SHALL show total replicating servers, maximum capacity (number of accounts × 300), percentage used, and available slots
4. WHEN combined capacity exceeds operational limits, THE System SHALL display appropriate status indicators (OK, INFO, WARNING, CRITICAL, HYPER-CRITICAL)
5. WHEN displaying capacity, THE System SHALL show a progress bar visualizing percentage used against operational and hard limits

### Requirement 5: Display Per-Account Capacity Breakdown

**User Story:** As a DR administrator, I want to see capacity breakdown for each account, so that I can identify which accounts are approaching limits.

#### Acceptance Criteria

1. WHEN the capacity dashboard displays account breakdown, THE System SHALL list all accounts (target + staging) with their individual metrics
2. WHEN displaying per-account metrics, THE System SHALL show account ID, account name, account type (target/staging), replicating servers, maximum capacity, percentage used, and status
3. WHEN an account exceeds 200 servers (67%), THE System SHALL display INFO status
4. WHEN an account exceeds 225 servers (75%), THE System SHALL display WARNING status
5. WHEN an account exceeds 250 servers (83%), THE System SHALL display CRITICAL status
6. WHEN an account exceeds 280 servers (93%), THE System SHALL display HYPER-CRITICAL status
7. WHEN displaying account details, THE System SHALL show regional breakdown of servers for each account

### Requirement 6: Display Capacity Warnings

**User Story:** As a DR administrator, I want to receive warnings when approaching capacity limits, so that I can take action before reaching hard limits.

#### Acceptance Criteria

1. WHEN any account reaches 200-225 servers (67-75%), THE System SHALL display an INFO warning to monitor capacity
2. WHEN any account reaches 225-250 servers (75-83%), THE System SHALL display a WARNING to plan adding a staging account
3. WHEN any account reaches 250-280 servers (83-93%), THE System SHALL display a CRITICAL warning to add a staging account immediately
4. WHEN any account reaches 280-300 servers (93-100%), THE System SHALL display a HYPER-CRITICAL warning indicating immediate action required
5. WHEN combined capacity exceeds operational limits, THE System SHALL display warnings with recommended actions
6. WHEN warnings are present, THE System SHALL display them prominently in the capacity dashboard with actionable guidance

### Requirement 7: CLI Management Operations

**User Story:** As a DevOps engineer, I want to manage staging accounts via CLI scripts, so that I can automate staging account configuration.

#### Acceptance Criteria

1. WHEN a CLI script invokes the data management Lambda with "add_staging_account" operation, THE System SHALL add the staging account to the target account configuration
2. WHEN a CLI script invokes the data management Lambda with "remove_staging_account" operation, THE System SHALL remove the staging account from the target account configuration
3. WHEN a CLI script invokes the query Lambda with "validate_staging_account" operation, THE System SHALL validate the staging account access and return validation results
4. WHEN a CLI script invokes the query Lambda with "get_target_account" operation, THE System SHALL return the target account configuration including all staging accounts
5. WHEN CLI operations complete, THE System SHALL return structured JSON responses with success/error status and relevant data

### Requirement 8: Persist Staging Account Configuration

**User Story:** As a system, I want to persist staging account configurations in DynamoDB, so that staging accounts are retained across sessions and available for capacity queries.

#### Acceptance Criteria

1. WHEN a staging account is added, THE System SHALL store the staging account configuration in the Target Accounts table under a "stagingAccounts" attribute
2. WHEN storing staging accounts, THE System SHALL include account ID, account name, role ARN, and external ID for each staging account
3. WHEN a target account is queried, THE System SHALL retrieve the staging accounts list from the "stagingAccounts" attribute
4. WHEN a staging account is removed, THE System SHALL update the "stagingAccounts" attribute to exclude the removed account
5. WHEN the "stagingAccounts" attribute does not exist, THE System SHALL treat it as an empty list

### Requirement 9: Query Multi-Account DRS Capacity

**User Story:** As a system, I want to query DRS capacity across multiple accounts concurrently, so that capacity metrics are retrieved efficiently.

#### Acceptance Criteria

1. WHEN querying combined capacity, THE System SHALL query the target account and all staging accounts in parallel
2. WHEN querying each account, THE System SHALL assume the appropriate role using the stored role ARN and external ID
3. WHEN querying DRS capacity, THE System SHALL query all DRS-enabled regions concurrently for each account
4. WHEN DRS is not initialized in a region, THE System SHALL treat that region as having zero servers
5. WHEN role assumption fails for a staging account, THE System SHALL mark that account as inaccessible and continue querying other accounts
6. WHEN all queries complete, THE System SHALL aggregate results and calculate combined metrics

### Requirement 10: Display Recovery Capacity

**User Story:** As a DR administrator, I want to see recovery capacity metrics, so that I can understand how many instances can be recovered in the target account.

#### Acceptance Criteria

1. WHEN the capacity dashboard displays recovery capacity, THE System SHALL show current servers, maximum recovery instances (4,000), percentage used, and available slots
2. WHEN recovery capacity is below 80%, THE System SHALL display OK status
3. WHEN recovery capacity exceeds 80%, THE System SHALL display WARNING status
4. WHEN recovery capacity exceeds 90%, THE System SHALL display CRITICAL status
5. THE System SHALL calculate recovery capacity based only on the target account (not staging accounts)
