# DRS Agent Deployer - Implementation Tasks

## Overview

This document tracks all implementation tasks for the DRS Agent Deployer feature. Tasks are organized into phases and should be completed in order.

**Status Legend:**
- ✅ Complete
- 🚧 In Progress
- 📋 Pending

---

## Phase 1: Core Lambda Implementation ✅ COMPLETE

**Status:** ✅ Complete

All tasks in this phase have been completed. The Lambda function is implemented in `lambda/drs-agent-deployer/index.py`.

- [x] 1.1 Implement `DRSAgentDeployer` class with cross-account support
- [x] 1.2 Implement `lambda_handler` with parameter parsing
- [x] 1.3 Implement `_assume_role` for cross-account access
- [x] 1.4 Implement `discover_instances` with DR tag filtering
- [x] 1.5 Implement `check_ssm_status` with wait logic
- [x] 1.6 Implement `deploy_agents` with SSM command execution
- [x] 1.7 Implement `_wait_for_command` with status monitoring
- [x] 1.8 Implement `_get_source_servers` for DRS verification
- [x] 1.9 Create test events (single-account, cross-account, multi-account)
- [x] 1.10 Add comprehensive logging and error handling
- [x] 1.11 Validate Python syntax and type hints

---

## Phase 1.5: Configurable Tag Filters Enhancement

**Status:** 📋 Pending

**Goal:** Make DR tag filters configurable via event parameters and environment variables.

### Task 1.5.1: Add configurable tag filters to Lambda function
- [ ] Add `tag_filters` parameter to event (dict of tag key-value pairs)
- [ ] Add `wave_tag_key` parameter (default: "dr:wave")
- [ ] Add `priority_tag_key` parameter (default: "dr:priority")
- [ ] Add environment variables for default tag configuration
- [ ] Update `discover_instances()` to use configurable filters
- [ ] Update `_print_instances_by_wave()` to use configurable wave tag
- [ ] Add tag filter validation logic
- [ ] Update docstrings and comments

### Task 1.5.2: Update test events with tag configuration
- [ ] Add tag_filters to single-account.json
- [ ] Add tag_filters to cross-account.json
- [ ] Create custom-tags.json test event

### Task 1.5.3: Update documentation
- [ ] Update requirements.md with US-13
- [ ] Update design.md with tag configuration
- [ ] Update reference docs with tag examples

### Task 1.5.4: Test tag configuration
- [ ] Test with default tags
- [ ] Test with custom tags
- [ ] Test with invalid tag configuration
- [ ] Verify error messages

---

## Phase 1.6: DynamoDB Persistence Implementation

**Status:** 📋 Pending

**Goal:** Add deployment history tracking to DynamoDB for status reporting and failure analysis.

### Task 1.6.1: Add DynamoDB client initialization
- [ ] Add `dynamodb_client` attribute to `DRSAgentDeployer` class
- [ ] Add `deployment_table` parameter to `__init__`
- [ ] Initialize DynamoDB client in orchestration account region
- [ ] Get table name from environment variable or parameter

### Task 1.6.2: Implement `_save_deployment_history()` method
- [ ] Generate deployment_id (UUID)
- [ ] Calculate success_rate percentage
- [ ] Determine status (success/partial/failed)
- [ ] Extract failed instance details
- [ ] Calculate TTL (90 days from now)
- [ ] Build DynamoDB item structure
- [ ] Write item to DynamoDB table
- [ ] Handle DynamoDB errors gracefully
- [ ] Log success/failure of persistence

### Task 1.6.3: Implement `_extract_failed_instances()` method
- [ ] Parse SSM command results for failures
- [ ] Match failed instances with discovered instance metadata
- [ ] Extract error codes and messages
- [ ] Include wave and priority information
- [ ] Return structured list of failed instances

### Task 1.6.4: Integrate persistence into `deploy_agents()` method
- [ ] Call `_save_deployment_history()` after deployment completes
- [ ] Include deployment_id in response
- [ ] Handle persistence errors without failing deployment
- [ ] Log persistence status

### Task 1.6.5: Add account name resolution
- [ ] Add method to get account alias/name from account ID
- [ ] Use Organizations API or fallback to account ID
- [ ] Cache account names for session duration
- [ ] Include account names in deployment history

### Task 1.6.6: Test DynamoDB persistence
- [ ] Test successful deployment record
- [ ] Test partial failure record
- [ ] Test complete failure record
- [ ] Verify failed_instance_details structure
- [ ] Verify TTL calculation
- [ ] Test with DynamoDB unavailable (graceful degradation)

---

## Phase 2: CloudFormation Integration

**Status:** 📋 Pending (NEXT)

**Goal:** Deploy Lambda functions and DynamoDB table via CloudFormation.

### Task 2.1: Add DynamoDB table to `cfn/database-stack.yaml`
- [ ] Define `DRSAgentDeploymentsTable` resource
- [ ] Set partition key: `deployment_id` (String)
- [ ] Set sort key: `timestamp` (String)
- [ ] Add GSI: `AccountIndex` (source_account_id, timestamp)
- [ ] Add GSI: `StatusIndex` (status, timestamp)
- [ ] Add GSI: `PatternIndex` (deployment_pattern, timestamp)
- [ ] Configure TTL attribute: `ttl` (90 days)
- [ ] Set billing mode: PAY_PER_REQUEST
- [ ] Export table name and ARN

### Task 2.2: Add `DRSAgentDeployerFunction` to `cfn/lambda-stack.yaml`
- [ ] Define Lambda function resource
- [ ] Configure environment variables (include DEPLOYMENT_TABLE)
- [ ] Set timeout to 900 seconds (15 minutes)
- [ ] Set memory to 512 MB
- [ ] Reference `OrchestrationRoleArn` parameter
- [ ] Configure S3 code location
- [ ] Add DynamoDB permissions to execution role

### Task 2.3: Add `DRSAgentQueryFunction` to `cfn/lambda-stack.yaml`
- [ ] Define Lambda function for querying deployment history
- [ ] Configure environment variables
- [ ] Set timeout to 30 seconds
- [ ] Add DynamoDB read permissions

### Task 2.4: Add `DRSAgentDeployerLogGroup` to `cfn/lambda-stack.yaml`
- [ ] Create CloudWatch Logs group
- [ ] Set retention to 30 days

### Task 2.5: Add outputs to `cfn/lambda-stack.yaml`
- [ ] Export deployer function ARN
- [ ] Export deployer function name
- [ ] Export query function ARN
- [ ] Export query function name

### Task 2.6: Update `cfn/master-template.yaml` parameters (if needed)
- [ ] Add `TargetRegion` parameter (if not exists)
- [ ] Add `ExternalId` parameter (if not exists)

### Task 2.7: Package Lambda functions
- [ ] Run `package_lambda.py` for drs-agent-deployer
- [ ] Create drs-agent-query handler
- [ ] Verify ZIP files created

### Task 2.8: Deploy to dev environment
- [ ] Run `./scripts/deploy.sh dev --validate-only`
- [ ] Review CloudFormation changes
- [ ] Run `./scripts/deploy.sh dev`
- [ ] Verify DynamoDB table created
- [ ] Verify functions deployed successfully
- [ ] Check CloudWatch Logs groups created

### Task 2.9: Test Lambda function in dev
- [ ] Test with single-account event
- [ ] Test with cross-account event
- [ ] Verify CloudWatch Logs output
- [ ] Verify DRS source servers registered
- [ ] Verify deployment record in DynamoDB
- [ ] Test query function for history retrieval

---

## Phase 3: API Gateway Integration

**Status:** 📋 Pending

**Goal:** Add REST API endpoints for deployment, status, history, and export.

### Task 3.1: Create API Gateway resources in `cfn/api-gateway-operations-methods-stack.yaml`
- [ ] Add `/drs/agents/deploy` resource
- [ ] Add POST method for deployment
- [ ] Configure Lambda proxy integration
- [ ] Add Cognito authorizer
- [ ] Configure CORS

### Task 3.2: Add deployment status endpoint
- [ ] Add `/drs/agents/deploy/{deployment_id}` resource
- [ ] Add GET method for status
- [ ] Configure Lambda integration (query SSM)

### Task 3.3: Add deployment history endpoint
- [ ] Add `/drs/agents/deployments` resource
- [ ] Add GET method with query parameters
- [ ] Configure Lambda integration (query DynamoDB)
- [ ] Add pagination support

### Task 3.4: Add failures endpoint
- [ ] Add `/drs/agents/failures` resource
- [ ] Add GET method with filters
- [ ] Configure Lambda integration

### Task 3.5: Add export endpoint
- [ ] Add `/drs/agents/failures/export` resource
- [ ] Add GET method with format parameter
- [ ] Configure Lambda integration for CSV/JSON export
- [ ] Set proper Content-Type headers

### Task 3.6: Update API documentation
- [ ] Add endpoints to `docs/reference/API_ENDPOINTS_CURRENT.md`
- [ ] Document request/response schemas
- [ ] Add example requests and responses

### Task 3.7: Deploy API changes
- [ ] Run `./scripts/deploy.sh dev --validate-only`
- [ ] Review API Gateway changes
- [ ] Run `./scripts/deploy.sh dev`
- [ ] Verify endpoints created

### Task 3.8: Test API endpoints
- [ ] Test POST /drs/agents/deploy with cURL
- [ ] Test GET /drs/agents/deploy/{id} with cURL
- [ ] Test GET /drs/agents/deployments with filters
- [ ] Test GET /drs/agents/failures
- [ ] Test GET /drs/agents/failures/export (CSV)
- [ ] Test GET /drs/agents/failures/export (JSON)
- [ ] Verify authentication works
- [ ] Verify error responses

---

## Phase 4: Frontend Integration

**Status:** 📋 Pending

**Goal:** Create UI components for deployment, status tracking, and failure reporting.

### Task 4.1: Create TypeScript types in `frontend/src/types/drs-agent-deployment.ts`
- [ ] Define `DRSAgentDeploymentParams` interface
- [ ] Define `DRSAgentDeploymentResult` interface
- [ ] Define `DRSAgentDeploymentStatus` interface
- [ ] Define `DeploymentPattern` type
- [ ] Define `DeploymentHistory` interface
- [ ] Define `FailedInstance` interface

### Task 4.2: Add API service methods in `frontend/src/services/api.ts`
- [ ] Implement `deployDRSAgents()` function
- [ ] Implement `getDRSAgentDeploymentStatus()` function
- [ ] Implement `getDRSAgentDeploymentHistory()` function
- [ ] Implement `exportDRSAgentFailures()` function
- [ ] Add error handling

### Task 4.3: Create `DRSAgentDeployDialog` component
- [ ] Create component file `frontend/src/components/DRSAgentDeployDialog.tsx`
- [ ] Implement form with account/region selectors
- [ ] Add deployment pattern detection
- [ ] Implement deploy button with loading state
- [ ] Add error display
- [ ] Add success callback

### Task 4.4: Create `DRSAgentStatus` component
- [ ] Create component file `frontend/src/components/DRSAgentStatus.tsx`
- [ ] Display deployment pattern
- [ ] Display accounts and regions
- [ ] Display instance counts
- [ ] Display command status
- [ ] Display source servers
- [ ] Add auto-refresh option

### Task 4.5: Create `DRSAgentStatusCard` component
- [ ] Create component file `frontend/src/components/DRSAgentStatusCard.tsx`
- [ ] Implement summary stats section (total, success rate, failures)
- [ ] Implement per-account status grid with color indicators
- [ ] Implement failed instances table with expandable details
- [ ] Add date range filter
- [ ] Add account filter
- [ ] Add deployment pattern filter
- [ ] Add status filter (all/success/partial/failed)
- [ ] Implement auto-refresh functionality
- [ ] Add export button with CSV/JSON options

### Task 4.6: Create `DRSAgentFailureReport` component
- [ ] Create component file `frontend/src/components/DRSAgentFailureReport.tsx`
- [ ] Display failed instances grouped by account
- [ ] Show error categorization
- [ ] Add remediation suggestions per error type
- [ ] Implement timeline view
- [ ] Add export functionality

### Task 4.7: Integrate into Dashboard
- [ ] Add `DRSAgentStatusCard` to `Dashboard.tsx`
- [ ] Position card in appropriate section
- [ ] Configure default date range (last 24h)
- [ ] Add navigation to detailed failure report

### Task 4.8: Integrate into Protection Groups page
- [ ] Add "Deploy Agents" button to `ProtectionGroupsPage.tsx`
- [ ] Wire up dialog open/close
- [ ] Handle deployment success
- [ ] Show status in table
- [ ] Add link to deployment history

### Task 4.9: Write component tests
- [ ] Test `DRSAgentDeployDialog` rendering
- [ ] Test form validation
- [ ] Test deployment flow
- [ ] Test error handling
- [ ] Test `DRSAgentStatusCard` rendering
- [ ] Test filters and date range
- [ ] Test export functionality
- [ ] Test `DRSAgentFailureReport` rendering

### Task 4.10: Deploy frontend changes
- [ ] Run `./scripts/deploy.sh dev --frontend-only`
- [ ] Verify UI changes deployed

### Task 4.11: Manual UI testing
- [ ] Test same-account deployment via UI
- [ ] Test cross-account deployment via UI
- [ ] Test error scenarios
- [ ] Test status display
- [ ] Test dashboard status card
- [ ] Test filters and date range selection
- [ ] Test export to CSV
- [ ] Test export to JSON
- [ ] Test failure report view
- [ ] Verify color indicators (green/yellow/red)

---

## Phase 5: Cross-Account Role Setup

**Status:** 📋 Pending

**Goal:** Deploy IAM roles to source and staging accounts for cross-account access.

### Task 5.1: Create cross-account role CloudFormation template
- [ ] Define `DRSOrchestrationRole` resource
- [ ] Add trust policy with external ID
- [ ] Add EC2 describe permissions
- [ ] Add SSM command permissions
- [ ] Add DRS read permissions
- [ ] Add outputs for role ARN

### Task 5.2: Deploy role to source account (160885257264)
- [ ] Run CloudFormation deploy
- [ ] Verify role created
- [ ] Test role assumption from orchestration account

### Task 5.3: Deploy role to staging account (664418995426)
- [ ] Run CloudFormation deploy
- [ ] Verify role created
- [ ] Test role assumption from orchestration account

### Task 5.4: Initialize DRS in staging account
- [ ] Run `aws drs initialize-service`
- [ ] Create replication configuration template
- [ ] Verify DRS service ready

### Task 5.5: Tag EC2 instances in source account
- [ ] Add `dr:enabled=true` tag
- [ ] Add `dr:recovery-strategy=drs` tag
- [ ] Add `dr:wave` tag
- [ ] Verify SSM agents online

---

## Phase 6: Documentation

**Status:** 🚧 In Progress

**Goal:** Complete all documentation for the feature.

### Task 6.1: Core specification documents
- [x] Create requirements document
- [x] Create design document
- [x] Create tasks document

### Task 6.2: Move existing docs to spec folder
- [ ] Move `docs/guides/DRS_AGENT_DEPLOYMENT_GUIDE.md` to `reference/`
- [ ] Move `docs/guides/DRS_CROSS_ACCOUNT_REPLICATION.md` to `reference/`
- [ ] Move `docs/DRS_CROSS_ACCOUNT_ORCHESTRATION.md` to `reference/`
- [ ] Move `docs/guides/DRS_AGENT_DEPLOYMENT_FRONTEND_INTEGRATION.md` to `reference/`
- [ ] Update all internal links

### Task 6.3: Create API specification
- [ ] Document POST /drs/agents/deploy
- [ ] Document GET /drs/agents/deploy/{id}
- [ ] Document GET /drs/agents/deployments
- [ ] Document GET /drs/agents/failures
- [ ] Document GET /drs/agents/failures/export
- [ ] Add request/response examples
- [ ] Document error codes

### Task 6.4: Create testing guide
- [ ] Document unit testing procedures
- [ ] Document integration testing procedures
- [ ] Document manual testing checklist
- [ ] Add troubleshooting section

### Task 6.5: Update main README
- [ ] Add DRS Agent Deployer section
- [ ] Link to spec documentation
- [ ] Add quick start guide

---

## Phase 7: Testing & Validation

**Status:** 📋 Pending

**Goal:** Comprehensive testing of all components.

### Task 7.1: Unit tests
- [ ] Test role assumption logic
- [ ] Test instance discovery
- [ ] Test SSM status checking
- [ ] Test deployment pattern detection
- [ ] Test error handling
- [ ] Test DynamoDB persistence
- [ ] Test failed instance extraction

### Task 7.2: Integration tests
- [ ] Test same-account deployment end-to-end
- [ ] Test cross-account deployment end-to-end
- [ ] Test multi-account deployment
- [ ] Test error scenarios
- [ ] Test DynamoDB query operations

### Task 7.3: Manual testing in dev
- [ ] Deploy agents to dev account
- [ ] Verify agents installed
- [ ] Verify DRS source servers registered
- [ ] Verify replication working
- [ ] Verify deployment history in DynamoDB

### Task 7.4: Cross-account testing
- [ ] Deploy agents from source to staging
- [ ] Verify agents in source account
- [ ] Verify source servers in staging account
- [ ] Verify replication to staging
- [ ] Verify deployment record persisted

### Task 7.5: UI testing
- [ ] Test deployment dialog
- [ ] Test status display
- [ ] Test error handling
- [ ] Test integration with Protection Groups
- [ ] Test dashboard status card
- [ ] Test failure report
- [ ] Test export functionality

### Task 7.6: Performance testing
- [ ] Test with 10 instances
- [ ] Test with 50 instances
- [ ] Test with 100 instances
- [ ] Measure deployment duration
- [ ] Verify DynamoDB query performance

### Task 7.7: Security testing
- [ ] Verify role assumption requires external ID
- [ ] Verify least privilege permissions
- [ ] Verify no credentials logged
- [ ] Verify CloudTrail logging
- [ ] Test unauthorized access scenarios

---

## Phase 8: Production Rollout

**Status:** 📋 Pending

**Goal:** Deploy to test and production environments.

### Task 8.1: Deploy to test environment
- [ ] Run `./scripts/deploy.sh test --validate-only`
- [ ] Review changes
- [ ] Run `./scripts/deploy.sh test`
- [ ] Verify all components deployed
- [ ] Run smoke tests

### Task 8.2: Perform DR drill in test
- [ ] Deploy agents
- [ ] Verify replication
- [ ] Launch recovery instances
- [ ] Verify recovery successful
- [ ] Document results

### Task 8.3: Deploy to production
- [ ] Get approval from stakeholders
- [ ] Schedule maintenance window
- [ ] Run `./scripts/deploy.sh prod --validate-only`
- [ ] Review changes
- [ ] Run `./scripts/deploy.sh prod`
- [ ] Verify deployment successful

### Task 8.4: Monitor production
- [ ] Set up CloudWatch alarms
- [ ] Monitor deployment success rate
- [ ] Monitor agent registration rate
- [ ] Monitor performance metrics
- [ ] Monitor DynamoDB usage

### Task 8.5: Create runbook
- [ ] Document deployment procedures
- [ ] Document troubleshooting steps
- [ ] Document rollback procedures
- [ ] Document escalation paths

---

## Phase 9: Optimization & Monitoring

**Status:** 📋 Pending

**Goal:** Set up monitoring and optimize performance.

### Task 9.1: Set up CloudWatch dashboards
- [ ] Create deployment metrics dashboard
- [ ] Create agent health dashboard
- [ ] Create cost dashboard
- [ ] Add DynamoDB metrics

### Task 9.2: Implement CloudWatch alarms
- [ ] Deployment failure rate alarm
- [ ] Deployment duration alarm
- [ ] Agent registration rate alarm
- [ ] Lambda error alarm
- [ ] DynamoDB throttling alarm

### Task 9.3: Optimize performance
- [ ] Analyze deployment duration metrics
- [ ] Optimize instance discovery
- [ ] Optimize SSM command execution
- [ ] Implement caching where appropriate
- [ ] Optimize DynamoDB queries

### Task 9.4: Cost optimization
- [ ] Analyze Lambda costs
- [ ] Analyze DRS costs
- [ ] Analyze DynamoDB costs
- [ ] Implement cost-saving measures
- [ ] Document cost optimization recommendations

---

## Notes

- **Phase 1** is complete - Lambda function implemented and tested locally
- **Phase 1.5** adds configurable tag filters (not yet implemented)
- **Phase 1.6** adds DynamoDB persistence (not yet implemented)
- **Phases 2-4** are the critical path for full integration
- **Phase 5** is required for cross-account testing
- **Phases 6-9** are ongoing and can be done in parallel with other phases
- All tasks should be completed in order within each phase
- Each task should be tested before marking complete
- Update this document as tasks are completed

## Progress Tracking

| Phase | Status | Tasks Complete | Total Tasks |
|-------|--------|----------------|-------------|
| Phase 1 | ✅ Complete | 11 | 11 |
| Phase 1.5 | 📋 Pending | 0 | 4 |
| Phase 1.6 | 📋 Pending | 0 | 6 |
| Phase 2 | 📋 Pending | 0 | 9 |
| Phase 3 | 📋 Pending | 0 | 8 |
| Phase 4 | 📋 Pending | 0 | 11 |
| Phase 5 | 📋 Pending | 0 | 5 |
| Phase 6 | 🚧 In Progress | 3 | 5 |
| Phase 7 | 📋 Pending | 0 | 7 |
| Phase 8 | 📋 Pending | 0 | 5 |
| Phase 9 | 📋 Pending | 0 | 4 |
| **Total** | **~5% Complete** | **14** | **75** |


---

## Phase 1.7: Extended Source Server Automation

**Status:** 📋 Pending

**Goal:** Automatically extend source servers to target account after agent installation for capacity scaling.

### Task 1.7.1: Add configuration parameters
- [ ] Add `target_account_id` parameter to event schema
- [ ] Add `auto_extend_source_servers` boolean flag (default: false)
- [ ] Add `extension_config` object with retry settings
- [ ] Add environment variable for default target account
- [ ] Update `__init__` to accept extension parameters
- [ ] Validate extension configuration

### Task 1.7.2: Implement `_verify_target_account_access()` method
- [ ] Assume role in target account
- [ ] Check DRS service initialization
- [ ] Verify service-linked role exists
- [ ] Check cross-account trust configuration
- [ ] Return boolean with detailed error messages
- [ ] Log verification results

### Task 1.7.3: Implement `_get_extensible_source_servers()` method
- [ ] Call `list-extensible-source-servers` API
- [ ] Filter by staging account ID
- [ ] Extract ARN, hostname, tags
- [ ] Handle pagination if needed
- [ ] Return structured list
- [ ] Handle API errors gracefully

### Task 1.7.4: Implement `_extend_source_servers()` method
- [ ] Verify target account access first
- [ ] Get list of extensible source servers
- [ ] Initialize counters (extended, failed, already_extended)
- [ ] Loop through each source server:
  - [ ] Call `create-extended-source-server` API
  - [ ] Apply tags (Name, ExtendedFrom, DeploymentID)
  - [ ] Handle ConflictException (already extended)
  - [ ] Handle other errors with retry logic
  - [ ] Log each extension attempt
- [ ] Verify extensions in target account
- [ ] Return extension summary

### Task 1.7.5: Implement `_check_capacity_limits()` method
- [ ] Get current source server count in target account
- [ ] Calculate new total after extension
- [ ] Check against 300 server limit
- [ ] Calculate utilization percentage
- [ ] Return capacity status
- [ ] Log warnings at 80%, 90% capacity

### Task 1.7.6: Integrate extension into `deploy_agents()` method
- [ ] Check `auto_extend_source_servers` flag
- [ ] Wait for source servers to register (add delay if needed)
- [ ] Call `_extend_source_servers()` after successful deployment
- [ ] Include extension results in response
- [ ] Continue even if extension fails (log warning)
- [ ] Update deployment history with extension status

### Task 1.7.7: Add IAM permissions
- [ ] Update target account role with extension permissions
- [ ] Add `drs:CreateExtendedSourceServer` permission
- [ ] Add `drs:ListExtensibleSourceServers` permission
- [ ] Add `drs:TagResource` permission
- [ ] Update CloudFormation template
- [ ] Document permission requirements

### Task 1.7.8: Add error handling and retry logic
- [ ] Implement exponential backoff for retries
- [ ] Handle ConflictException (skip, log info)
- [ ] Handle AccessDeniedException (fail with message)
- [ ] Handle ResourceNotFoundException (fail with setup instructions)
- [ ] Handle ThrottlingException (retry with backoff)
- [ ] Handle ValidationException (log error, skip server)
- [ ] Handle network timeouts (retry up to 3 times)
- [ ] Log all error scenarios

### Task 1.7.9: Add monitoring and metrics
- [ ] Add CloudWatch metric: ExtendedSourceServers
- [ ] Add CloudWatch metric: ExtensionFailures
- [ ] Add CloudWatch metric: ExtensionDuration
- [ ] Add CloudWatch metric: AlreadyExtendedCount
- [ ] Log structured events (extension_started, server_extended, extension_complete)
- [ ] Include extension metrics in deployment summary

### Task 1.7.10: Create test events
- [ ] Create extension-enabled.json test event
- [ ] Create extension-disabled.json test event
- [ ] Create extension-already-extended.json test event
- [ ] Create extension-capacity-limit.json test event
- [ ] Document test scenarios

### Task 1.7.11: Update documentation
- [ ] Update requirements.md with US-15
- [ ] Update design.md with extension architecture
- [ ] Add extension configuration examples
- [ ] Document IAM permission requirements
- [ ] Add troubleshooting guide for extension failures
- [ ] Update capacity scaling architecture docs

### Task 1.7.12: Testing
- [ ] Unit test: _verify_target_account_access()
- [ ] Unit test: _get_extensible_source_servers()
- [ ] Unit test: _extend_source_servers()
- [ ] Unit test: _check_capacity_limits()
- [ ] Integration test: End-to-end extension flow
- [ ] Integration test: Already extended servers
- [ ] Integration test: Extension failures
- [ ] Integration test: Capacity limit warnings
- [ ] Test with real staging and target accounts

