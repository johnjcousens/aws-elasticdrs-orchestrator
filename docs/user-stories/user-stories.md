# User Stories
## HealthEdge Disaster Recovery Implementation

**Document Version**: 1.0  
**Date**: December 5, 2025  
**Project**: gc-dr-implementation  
**Status**: Draft for Review

---

## Document Overview

This document contains comprehensive user stories for the HealthEdge Disaster Recovery orchestration solution. Stories are organized by epic, follow INVEST criteria, and include detailed acceptance criteria with Given/When/Then format.

**Document Version**: 1.3 (Updated post-feedback iteration 3)  
**Total Epics**: 13  
**Total User Stories**: 77 (5 new infrastructure stories added, US-071, US-074, and US-078 removed)  
**Estimated Story Points**: 413 (increased from 340 due to new infrastructure stories and sprint assignment corrections)

---

## Epic Overview

### Epic 1: DR Orchestration Foundation
Foundation for tag-driven disaster recovery orchestration with automated resource discovery and wave-based execution.

### Epic 2: DRS Integration and EC2 Recovery
Integration with AWS Elastic Disaster Recovery service for continuous replication and rapid recovery of critical EC2 workloads.

### Epic 3: Database Disaster Recovery
Orchestration of database failover operations for SQL Server, ElastiCache, and MongoDB with minimal data loss.

### Epic 4: Network and Load Balancer Failover
DNS-based traffic redirection and load balancer failover to DR region endpoints.

### Epic 5: Container and Kubernetes DR
Amazon EKS cluster failover with application deployment and DNS updates for containerized workloads.

### Epic 6: Storage and Data Replication
Cross-region replication and failover for S3, EFS, FSx, and Storage Gateway.

### Epic 7: Application Component Failover
Failover orchestration for application-specific components including Active Directory, SFTP, and Airflow.

### Epic 8: Testing and Validation
Comprehensive testing framework including isolated bubble tests, Game Day exercises, and DR readiness validation.

### Epic 9: Monitoring and Observability
Real-time monitoring, alerting, and reporting for DR orchestration operations and system health.

### Epic 10: Operational Management
Operational tools including approval workflows, runbook documentation, and configuration management.

### Epic 11: Security and Compliance
Security controls, encryption, audit logging, and compliance framework implementation.

### Epic 12: Performance and Scalability
Performance optimization and scalability enhancements to meet RTO/RPO targets at scale.

---

## Epic 1: DR Orchestration Foundation

### US-001: Update Existing Tag Documentation with DR Taxonomy
**As a** Cloud Infrastructure Architect  
**I want** existing tag documentation updated with standardized DR tagging taxonomy  
**So that** resources can be consistently tagged for automated DR orchestration with clearer semantics

#### Acceptance Criteria:
- **Given** existing tag documentation  
  **When** updating with DR taxonomy  
  **Then** standard DR tags are added: dr:enabled, dr:priority, dr:wave, dr:rto-target, dr:rpo-target, dr:recovery-strategy
- **Given** the DR tagging taxonomy  
  **When** documenting tag usage  
  **Then** documentation includes tag definitions, valid values, usage examples, and migration plan from existing DRS tags
- **Given** multi-tenant requirements  
  **When** designing the taxonomy  
  **Then** leverage existing Environment and Customer tags for scoping operations

#### Definition of Done:
- [ ] Existing tag documentation updated with DR tags
- [ ] Migration plan from existing DRS tags to new dr:x taxonomy documented
- [ ] Tag validation rules defined (valid values, required vs optional)
- [ ] Usage examples provided for common scenarios including Customer and Environment tags
- [ ] Documentation reviewed and approved by architecture team

#### Story Points: 3  
#### Dependencies: None

---

### US-002: Implement Tag Validation with SCPs and Tag Policies
**As a** Cloud Infrastructure Architect  
**I want** automated tag validation enforced via SCPs and tag policies  
**So that** resources are correctly tagged before DR orchestration

#### Acceptance Criteria:
- **Given** the DR tagging taxonomy  
  **When** implementing validation rules  
  **Then** tag policies validate required DR tags are present
- **Given** tagged resources  
  **When** tags have invalid values  
  **Then** SCPs prevent resource creation or modification
- **Given** non-compliant resource creation attempts  
  **When** detected by SCPs  
  **Then** operations are blocked and error messages guide users

#### Definition of Done:
- [ ] Tag policies deployed for DR tag validation
- [ ] SCPs configured to enforce tag requirements
- [ ] Tag policies and SCPs tested with compliant and non-compliant resources
- [ ] Error messages provide clear guidance for compliance
- [ ] Validation rules documented in runbooks

#### Story Points: 5  
#### Dependencies: US-001

---

### US-003: Develop Tag-Based Resource Discovery Using AWS Resource Explorer
**As a** DR Operations Engineer  
**I want** automated discovery of DR-enabled resources using AWS Resource Explorer APIs  
**So that** orchestration workflows efficiently discover tagged resources across accounts and regions without custom cross-account logic

#### Acceptance Criteria:
- **Given** resources tagged with dr:enabled=true  
  **When** running resource discovery  
  **Then** AWS Resource Explorer APIs query tagged resources across multiple accounts and regions
- **Given** multi-account LZA structure  
  **When** discovering resources  
  **Then** Resource Explorer Organizations integration provides cross-account discovery
- **Given** discovered resources  
  **When** generating inventory  
  **Then** inventory includes resource type, ID, tags (including Customer and Environment), account, and region
- **Given** resource type coverage  
  **When** validating discovery  
  **Then** all required resource types are supported: EC2, RDS, EKS, ECS, S3, EFS, FSx, ElastiCache, Route53, ALB/NLB, VPN, Transit Gateway

#### Definition of Done:
- [ ] AWS Resource Explorer configured with aggregator region for cross-region search
- [ ] Resource Explorer Organizations integration enabled for multi-account discovery
- [ ] Lambda function implements Resource Explorer API-based discovery
- [ ] Discovery supports all required resource types: EC2, RDS, EKS, ECS, S3, EFS, FSx, ElastiCache, Route53, ALB/NLB, VPN, Transit Gateway
- [ ] Resource type coverage validated and documented
- [ ] Inventory output format defined and documented
- [ ] Unit tests cover discovery logic for all resource types

#### Story Points: 8  
#### Dependencies: US-001, US-002

---

### US-004: Create Step Functions DR Orchestrator Workflow
**As a** DR Operations Engineer  
**I want** a Step Functions workflow that orchestrates complete DR operations  
**So that** failover, failback, and testing are automated and auditable

#### Acceptance Criteria:
- **Given** DR operation request (failover/failback/test)  
  **When** initiating the orchestrator workflow  
  **Then** workflow executes resource discovery, wave orchestration, and validation
- **Given** orchestrator execution  
  **When** errors occur  
  **Then** automatic retries with exponential backoff are attempted
- **Given** orchestrator execution  
  **When** manual intervention is required  
  **Then** workflow pauses and sends notification

#### Definition of Done:
- [ ] Step Functions state machine created for DR orchestrator
- [ ] Workflow supports failover, failback, and test modes
- [ ] Error handling and retry logic implemented
- [ ] Execution history and audit trail available
- [ ] Workflow tested with mock resources

#### Story Points: 13  
#### Dependencies: US-003

---

### US-005: Implement Wave-Based Orchestration Logic
**As a** DR Operations Engineer  
**I want** orchestration to execute in ordered waves based on dr:wave tags  
**So that** dependent systems recover in the correct sequence

#### Acceptance Criteria:
- **Given** resources tagged with dr:wave values  
  **When** orchestrating recovery  
  **Then** wave 1 executes first, then wave 2, etc.
- **Given** resources within the same wave  
  **When** orchestrating recovery  
  **Then** resources recover in parallel for efficiency
- **Given** a wave execution  
  **When** any resource in the wave fails  
  **Then** wave continues but failure is logged and reported

#### Definition of Done:
- [ ] Wave orchestration logic implemented in Step Functions
- [ ] Parallel execution within waves configured
- [ ] Wave completion criteria defined (all resources attempted)
- [ ] Error handling preserves wave ordering
- [ ] Integration tests validate wave sequencing

#### Story Points: 8  
#### Dependencies: US-004

---

### US-006: Implement Lifecycle Orchestration Workflow with Customer/Environment Scoping
**As a** DR Operations Engineer  
**I want** a lifecycle workflow that manages individual resource recovery with Customer and Environment scoping  
**So that** each resource type has appropriate recovery logic and operations can be scoped to specific customer environments

#### Acceptance Criteria:
- **Given** a resource to recover with Customer and Environment tags  
  **When** lifecycle workflow executes  
  **Then** appropriate recovery module is invoked based on resource type
- **Given** Customer and Environment scope parameters  
  **When** lifecycle workflow executes  
  **Then** only resources matching the specified scope are processed
- **Given** resource recovery  
  **When** recovery completes  
  **Then** resource health is validated before marking complete
- **Given** resource recovery failure  
  **When** retries are exhausted  
  **Then** failure is logged and parent workflow is notified

#### Definition of Done:
- [ ] Lifecycle Step Functions state machine created
- [ ] Customer and Environment scoping logic implemented
- [ ] Resource type routing logic implemented
- [ ] Health validation integrated
- [ ] Error propagation to parent workflow configured
- [ ] Integration tests with multiple resource types and scoping scenarios

#### Story Points: 8  
#### Dependencies: US-005

---

### US-007: Develop Module Factory Pattern
**As a** DR Operations Engineer  
**I want** a module factory that dynamically invokes resource-specific recovery modules  
**So that** new resource types can be added without changing core orchestration

#### Acceptance Criteria:
- **Given** a resource type (EC2, RDS, EKS, etc.)  
  **When** module factory is invoked  
  **Then** appropriate recovery module Lambda function is called
- **Given** a new resource type  
  **When** adding support  
  **Then** new module is registered without modifying factory logic
- **Given** module execution  
  **When** module completes  
  **Then** standardized response format is returned

#### Definition of Done:
- [ ] Module factory Lambda function implemented
- [ ] Module registry configuration created
- [ ] Standardized module interface defined
- [ ] Example modules implemented (EC2, RDS)
- [ ] Documentation for adding new modules

#### Story Points: 8  
#### Dependencies: US-006

---

### US-008: Implement CLI-Triggered DR Operations with Customer/Environment Scoping
**As a** DR Operations Engineer  
**I want** to initiate DR operations via CLI commands with Customer and Environment parameters  
**So that** operations integrate with existing runbooks and can be scoped to specific customer environments

#### Acceptance Criteria:
- **Given** AWS CLI access  
  **When** executing DR failover command  
  **Then** Step Functions orchestrator workflow is initiated
- **Given** CLI execution  
  **When** providing operation parameters (mode, scope, Customer, Environment, approval)  
  **Then** parameters including Customer, Environment, and dr:x tags are validated and passed to orchestrator workflow
- **Given** CLI execution with Customer and Environment scope  
  **When** workflow starts  
  **Then** only resources matching specified Customer, Environment, and dr:x tags are processed
- **Given** CLI execution  
  **When** workflow starts  
  **Then** execution ARN is returned for tracking

#### Definition of Done:
- [ ] CLI command examples documented with Customer, Environment, and dr:x tag parameters
- [ ] SSM document created for DR operations with scoping support
- [ ] Parameter validation implemented including Customer, Environment, and dr:x tags
- [ ] Execution tracking guidance provided
- [ ] Runbook includes CLI usage examples with scoping scenarios

#### Story Points: 5  
#### Dependencies: US-004

---

### US-009: Configure Cross-Account IAM Roles via LZA
**As a** Cloud Infrastructure Architect  
**I want** cross-account IAM roles configured for DR orchestration via LZA customizations-config.yaml  
**So that** central DR account can orchestrate resources in workload accounts

#### Acceptance Criteria:
- **Given** LZA multi-account structure  
  **When** configuring IAM roles  
  **Then** DR orchestration role is defined in LZA customizations-config.yaml for deployment to each workload account
- **Given** DR orchestration role  
  **When** defining permissions  
  **Then** least privilege access is granted for DR operations only
- **Given** cross-account access  
  **When** assuming roles  
  **Then** trust relationship validates source account and external ID

#### Definition of Done:
- [ ] IAM role defined in LZA customizations-config.yaml
- [ ] Role configuration includes all workload accounts
- [ ] Trust relationships configured and tested
- [ ] Permission policies follow least privilege
- [ ] Role assumption tested from DR account
- [ ] LZA deployment validated

#### Story Points: 5  
#### Dependencies: None

---

### US-010: Implement Resource Discovery Caching with Configurable TTL
**As a** DR Operations Engineer  
**I want** discovered resource inventory cached with configurable TTL  
**So that** orchestration workflows execute faster without repeated discovery

#### Acceptance Criteria:
- **Given** resource discovery execution  
  **When** discovery completes  
  **Then** inventory is cached in DynamoDB with timestamp
- **Given** cached inventory  
  **When** cache age is less than configurable TTL  
  **Then** cached inventory is used instead of re-discovery
- **Given** cached inventory  
  **When** cache age exceeds configurable TTL  
  **Then** fresh discovery is performed and cache is updated
- **Given** TTL configuration  
  **When** updating TTL value  
  **Then** new TTL takes effect without code changes

#### Definition of Done:
- [ ] DynamoDB table created for inventory cache
- [ ] Cache read/write logic implemented
- [ ] Configurable TTL parameter in Systems Manager Parameter Store
- [ ] Cache invalidation mechanism implemented
- [ ] Performance improvement measured and documented

#### Story Points: 5  
#### Dependencies: US-003

---

### US-011: Create DR Orchestration Configuration Management
**As a** DR Operations Engineer  
**I want** centralized configuration management for DR orchestration parameters  
**So that** settings are consistent and easily updated

#### Acceptance Criteria:
- **Given** orchestration parameters (timeouts, retries, regions)  
  **When** storing configuration  
  **Then** parameters are stored in Systems Manager Parameter Store
- **Given** environment-specific settings  
  **When** retrieving configuration  
  **Then** correct environment parameters are loaded (dev/test/prod)
- **Given** configuration changes  
  **When** updating parameters  
  **Then** changes take effect without code deployment

#### Definition of Done:
- [ ] Parameter Store hierarchy defined
- [ ] Configuration parameters documented
- [ ] Environment-specific parameters created
- [ ] Configuration retrieval logic implemented
- [ ] Configuration validation implemented

#### Story Points: 5  
#### Dependencies: None

---

### US-012: Implement Approval Workflow for Production Failover
**As a** DR Operations Manager  
**I want** manual approval required for production failover operations  
**So that** accidental or unauthorized DR operations are prevented

#### Acceptance Criteria:
- **Given** production failover request  
  **When** orchestrator workflow reaches approval gate  
  **Then** workflow pauses and sends approval notification via SNS
- **Given** approval notification  
  **When** approver responds via CLI or Console  
  **Then** workflow resumes or cancels based on approval decision
- **Given** approval request  
  **When** timeout period expires without response  
  **Then** workflow cancels and sends timeout notification

#### Definition of Done:
- [ ] Approval gate integrated in Step Functions workflow
- [ ] SNS topic configured for approval notifications
- [ ] Approval response mechanism implemented
- [ ] Timeout handling configured (30 minutes default)
- [ ] Approval decisions logged with approver identity

#### Story Points: 8  
#### Dependencies: US-005

---

## Epic 2: DRS Integration and EC2 Recovery

### US-017: Integrate with AWS DRS Using AllowLaunchingIntoThisInstance
**As a** DR Operations Engineer  
**I want** integration with AWS DRS service using AllowLaunchingIntoThisInstance for failover and failback  
**So that** critical workloads achieve 15-30 minute RTO with pre-provisioned instances and preserved instance identity

#### Acceptance Criteria:
- **Given** EC2 instances tagged with dr:recovery-strategy=drs  
  **When** initiating recovery  
  **Then** DRS recovery jobs are created for tagged instances
- **Given** pre-provisioned DR region instances  
  **When** initiating failover  
  **Then** AllowLaunchingIntoThisInstance is used to launch into pre-provisioned instances
- **Given** primary-DR instance pairs  
  **When** identifying target instances  
  **Then** Name tags are matched between primary and DR region instances
- **Given** failback operation  
  **When** returning to primary region  
  **Then** AllowLaunchingIntoThisInstance is used to launch into original source instances
- **Given** DRS recovery job  
  **When** job is in progress  
  **Then** job status is monitored and reported
- **Given** DRS recovery completion  
  **When** instances are launched  
  **Then** instance IDs and status are captured for validation

#### Definition of Done:
- [ ] DRS API integration implemented with AllowLaunchingIntoThisInstance support
- [ ] Name tag matching logic for primary-DR instance pairs
- [ ] Recovery job creation logic for failover and failback
- [ ] Job status monitoring implemented
- [ ] Error handling for DRS API failures
- [ ] Integration tests with DRS service and pre-provisioned instances

#### Story Points: 8  
#### Dependencies: US-003, US-007

---

### US-018: Implement DRS Drill Mode for Testing
**As a** DR Operations Engineer  
**I want** DRS drill mode support for isolated testing  
**So that** DR capabilities are validated without impacting production

#### Acceptance Criteria:
- **Given** test operation request  
  **When** initiating DRS recovery  
  **Then** drill mode is used instead of recovery mode
- **Given** drill mode execution  
  **When** instances are launched  
  **Then** instances are launched in isolated test network
- **Given** drill completion  
  **When** test is finished  
  **Then** drill instances are automatically terminated

#### Definition of Done:
- [ ] Drill mode parameter added to recovery logic
- [ ] Isolated test network configuration defined
- [ ] Automatic cleanup logic implemented
- [ ] Drill mode tested end-to-end
- [ ] Drill mode documented in runbooks

#### Story Points: 5  
#### Dependencies: US-017

---

### US-019: Handle DRS API Rate Limits
**As a** DR Operations Engineer  
**I want** DRS API calls to handle rate limits gracefully  
**So that** large-scale recovery operations complete successfully

#### Acceptance Criteria:
- **Given** DRS API rate limit exceeded  
  **When** making API calls  
  **Then** exponential backoff retry logic is applied
- **Given** multiple concurrent recovery jobs  
  **When** creating jobs  
  **Then** job creation is throttled to stay within rate limits
- **Given** rate limit errors  
  **When** retries are exhausted  
  **Then** error is logged and escalated

#### Definition of Done:
- [ ] Exponential backoff logic implemented
- [ ] Rate limit detection and handling implemented
- [ ] Throttling mechanism for concurrent jobs
- [ ] Rate limit testing performed
- [ ] Monitoring for rate limit errors configured

#### Story Points: 5  
#### Dependencies: US-017

---

### US-020: Implement DRS Configuration Management (Simplified)
**As a** DR Operations Engineer  
**I want** DRS replication settings managed for source servers with simplified configuration given pre-provisioned instances  
**So that** configuration is consistent and recovery behavior is predictable

#### Acceptance Criteria:
- **Given** DRS replication settings template  
  **When** applying to source servers  
  **Then** settings are synchronized across all tagged servers
- **Given** pre-provisioned DR instances with AllowLaunchingIntoThisInstance  
  **When** configuring DRS  
  **Then** launch template synchronization may not be required
- **Given** primary-DR instance pairs  
  **When** validating configuration  
  **Then** Name tag matching is verified between regions
- **Given** configuration drift  
  **When** detected  
  **Then** drift is reported and remediation is triggered
- **Given** new source servers  
  **When** added to DRS  
  **Then** standard configuration is automatically applied

#### Definition of Done:
- [ ] Configuration template defined for pre-provisioned instance scenario
- [ ] Name tag matching validation implemented
- [ ] Synchronization logic implemented (simplified for pre-provisioned instances)
- [ ] Drift detection implemented
- [ ] Automatic remediation configured
- [ ] Configuration sync tested with multiple servers

#### Story Points: 5  
#### Dependencies: US-017

---

### US-021: Validate DRS Readiness for Pre-Provisioned Instances
**As a** DR Operations Engineer  
**I want** DRS readiness validated for pre-provisioned instances  
**So that** failover operations can proceed with confidence

#### Acceptance Criteria:
- **Given** pre-provisioned DR instances  
  **When** validating readiness  
  **Then** AllowLaunchingIntoThisInstance capability is verified
- **Given** primary-DR instance pairs  
  **When** validating configuration  
  **Then** Name tag matching is confirmed between regions
- **Given** DRS replication  
  **When** validating readiness  
  **Then** replication lag is within acceptable thresholds
- **Given** pre-provisioned instances  
  **When** validating state  
  **Then** instances are running without attached storage (cost optimization)

#### Definition of Done:
- [ ] AllowLaunchingIntoThisInstance validation logic implemented
- [ ] Name tag matching validation implemented
- [ ] Replication lag threshold checks implemented
- [ ] Pre-provisioned instance state validation implemented
- [ ] Readiness validation testing completed

#### Story Points: 5  
#### Dependencies: US-017

---

### US-022: Implement DRS Replication Monitoring
**As a** DR Operations Engineer  
**I want** comprehensive monitoring of DRS replication health  
**So that** replication issues are detected and resolved proactively

#### Acceptance Criteria:
- **Given** DRS source servers  
  **When** monitoring replication  
  **Then** replication lag is tracked for all servers
- **Given** replication lag threshold exceeded  
  **When** detected  
  **Then** CloudWatch alarm is triggered
- **Given** disconnected DRS agents  
  **When** detected  
  **Then** alert is sent to operations team

#### Definition of Done:
- [ ] CloudWatch metrics for DRS replication lag
- [ ] CloudWatch alarms for lag thresholds
- [ ] Agent connectivity monitoring implemented
- [ ] Dashboard created for DRS health
- [ ] Alert notifications configured

#### Story Points: 5  
#### Dependencies: US-017

---

### US-023: Create DRS Readiness Report
**As a** DR Operations Manager  
**I want** automated DRS readiness reports  
**So that** DR readiness status is visible to stakeholders

#### Acceptance Criteria:
- **Given** DRS source servers  
  **When** generating readiness report  
  **Then** report includes replication status, lag, and readiness for all servers
- **Given** readiness report  
  **When** servers are not ready  
  **Then** issues are highlighted with remediation guidance
- **Given** report generation  
  **When** scheduled daily  
  **Then** report is automatically generated and distributed

#### Definition of Done:
- [ ] Readiness report generation logic implemented
- [ ] Report format defined (HTML/PDF)
- [ ] Scheduled report generation configured
- [ ] Report distribution via email/S3 configured
- [ ] Sample reports reviewed and approved

#### Story Points: 5  
#### Dependencies: US-022

---

### US-013: Support AllowLaunchingIntoThisInstance Capability
**As a** DR Operations Engineer  
**I want** support for pre-provisioned DR instances with AllowLaunchingIntoThisInstance  
**So that** cost is optimized by pre-provisioning instances with minimal or no storage

#### Acceptance Criteria:
- **Given** pre-provisioned DR instances  
  **When** configuring DRS  
  **Then** AllowLaunchingIntoThisInstance capability is enabled
- **Given** DRS recovery  
  **When** launching into pre-provisioned instance  
  **Then** instance retains instance ID and network configuration
- **Given** pre-provisioned instances  
  **When** not in use  
  **Then** instances run with minimal or no attached storage (cost optimization)

#### Definition of Done:
- [ ] AllowLaunchingIntoThisInstance configuration implemented
- [ ] Pre-provisioned instance setup documented with minimal/no storage guidance
- [ ] Recovery into pre-provisioned instances tested
- [ ] Cost optimization validated
- [ ] Runbook includes pre-provisioning procedures

#### Story Points: 8  
#### Dependencies: US-017

---

## Epic 3: Database Disaster Recovery

### US-024: Orchestrate SQL Server Always On Failover with Bubble Test Cloning
**As a** Database Administrator  
**I want** automated SQL Server Always On Availability Group failover with support for cloning DR cluster nodes for bubble testing  
**So that** database services recover quickly with minimal data loss and can be tested in isolation

#### Acceptance Criteria:
- **Given** SQL Server AG with cross-region replica  
  **When** initiating failover  
  **Then** secondary replica is promoted to primary
- **Given** failover operation  
  **When** forced failover is required  
  **Then** forced failover with potential data loss is executed
- **Given** failover completion  
  **When** primary role changes  
  **Then** application connection strings are updated
- **Given** bubble test requirement  
  **When** initiating isolated test  
  **Then** DR cluster nodes are cloned into isolated network
- **Given** cloned DR nodes  
  **When** operating in test environment  
  **Then** clones operate independently without affecting production DR replicas

#### Definition of Done:
- [ ] SQL Server AG failover logic implemented
- [ ] Forced and planned failover modes supported
- [ ] Connection string update mechanism implemented
- [ ] DR cluster node cloning logic for bubble tests implemented
- [ ] Isolated network configuration for cloned nodes
- [ ] Failover tested with test AG
- [ ] Bubble test cloning tested and validated
- [ ] Runbook includes failover and bubble test procedures

#### Story Points: 13  
#### Dependencies: US-007, US-050

---

### US-025: Validate SQL Server Replication Status
**As a** Database Administrator  
**I want** SQL Server replication status validated before failover  
**So that** data loss is minimized and failover success is ensured

#### Acceptance Criteria:
- **Given** SQL Server AG  
  **When** validating replication  
  **Then** synchronization state and lag are checked
- **Given** replication lag exceeds threshold  
  **When** failover is requested  
  **Then** warning is issued and approval is required
- **Given** secondary replica not synchronized  
  **When** failover is requested  
  **Then** failover is blocked and alert is sent

#### Definition of Done:
- [ ] Replication status check logic implemented
- [ ] Lag threshold configuration defined
- [ ] Validation integrated into failover workflow
- [ ] Blocking logic for unsynchronized replicas
- [ ] Validation testing completed

#### Story Points: 5  
#### Dependencies: US-024

---

### US-026: Implement SQL Server Failback
**As a** Database Administrator  
**I want** automated SQL Server failback to primary region  
**So that** normal operations are restored after DR event

#### Acceptance Criteria:
- **Given** SQL Server running in DR region  
  **When** initiating failback  
  **Then** primary region replica is promoted back to primary
- **Given** failback operation  
  **When** data synchronization is required  
  **Then** synchronization completes before role change
- **Given** failback completion  
  **When** primary role restored  
  **Then** application connection strings are updated back

#### Definition of Done:
- [ ] Failback logic implemented
- [ ] Data synchronization validation implemented
- [ ] Connection string restoration implemented
- [ ] Failback tested end-to-end
- [ ] Failback runbook created

#### Story Points: 8  
#### Dependencies: US-024

---

### US-027: Orchestrate Valkey Endpoint Failover via Route 53
**As a** DR Operations Engineer  
**I want** Valkey endpoint failover orchestrated via Route 53 DNS updates  
**So that** session data is handled by DR region cache infrastructure

#### Acceptance Criteria:
- **Given** Valkey CNAME in customer AD DNS pointing to Route 53 record  
  **When** initiating failover  
  **Then** Route 53 record is updated to point to DR region Valkey endpoint
- **Given** Valkey cache in DR region  
  **When** failover completes  
  **Then** cache starts empty and warms naturally with application traffic
- **Given** failback operation  
  **When** returning to primary region  
  **Then** Route 53 record is updated back to primary region endpoint
- **Given** Valkey infrastructure  
  **When** validating readiness  
  **Then** DR region Valkey cluster is verified as deployed and accessible

#### Definition of Done:
- [ ] Route 53 DNS update logic for Valkey endpoint implemented
- [ ] Customer AD DNS CNAME configuration documented
- [ ] DR region Valkey endpoint validation implemented
- [ ] DNS update tested for failover and failback
- [ ] No replication or data synchronization logic required
- [ ] Runbook includes DNS failover procedures

#### Story Points: 5  
#### Dependencies: US-007, US-031

---

### US-028: Validate Valkey Infrastructure Deployment
**As a** DR Operations Engineer  
**I want** Valkey infrastructure validated in DR region  
**So that** application can connect to cache services after failover

#### Acceptance Criteria:
- **Given** ElastiCache for Valkey in DR region  
  **When** validating infrastructure  
  **Then** Valkey cluster is verified as deployed and accessible
- **Given** Valkey endpoint  
  **When** validating connectivity  
  **Then** network connectivity and security group rules are confirmed
- **Given** Valkey infrastructure  
  **When** validating readiness  
  **Then** cluster health status is verified

#### Definition of Done:
- [ ] Valkey infrastructure validation logic implemented
- [ ] Connectivity validation implemented
- [ ] Health check validation implemented
- [ ] Validation tested with DR region Valkey cluster
- [ ] Documentation includes validation procedures

#### Story Points: 3  
#### Dependencies: US-027

---

### US-029: Recover MongoDB EC2 Instances Using DRS
**As a** Database Administrator  
**I want** MongoDB EC2 instances recovered using DRS replication  
**So that** MongoDB services recover with minimal data loss using instance-level replication

#### Acceptance Criteria:
- **Given** MongoDB EC2 instances tagged with dr:recovery-strategy=drs  
  **When** initiating failover  
  **Then** DRS recovery jobs are created for MongoDB instances
- **Given** MongoDB instances recovered in DR region  
  **When** recovery completes  
  **Then** application connection strings are updated to point to DR region instances
- **Given** failback operation  
  **When** returning to primary region  
  **Then** AllowLaunchingIntoThisInstance is used to launch into original instances
- **Given** MongoDB recovery  
  **When** validating readiness  
  **Then** MongoDB service health is verified before marking complete

#### Definition of Done:
- [ ] MongoDB EC2 instances tagged appropriately for DRS
- [ ] DRS recovery logic for MongoDB instances implemented
- [ ] Connection string update mechanism implemented
- [ ] Failback logic using AllowLaunchingIntoThisInstance implemented
- [ ] MongoDB service health validation implemented
- [ ] Recovery tested with test MongoDB instances
- [ ] Runbook includes MongoDB DRS recovery procedures

#### Story Points: 5  
#### Dependencies: US-017

---

### US-030: Validate MongoDB Service Health After Recovery
**As a** Database Administrator  
**I want** MongoDB service health validated after DRS recovery  
**So that** application can safely connect to recovered MongoDB instances

#### Acceptance Criteria:
- **Given** MongoDB instances recovered via DRS  
  **When** validating service health  
  **Then** MongoDB service is verified as running and accepting connections
- **Given** MongoDB service health check  
  **When** validating readiness  
  **Then** database connectivity and authentication are confirmed
- **Given** MongoDB recovery  
  **When** health validation passes  
  **Then** recovery is marked complete and application can connect

#### Definition of Done:
- [ ] MongoDB service health check logic implemented
- [ ] Connectivity validation implemented
- [ ] Authentication validation implemented
- [ ] Health validation tested with recovered instances
- [ ] Documentation includes health validation procedures

#### Story Points: 3  
#### Dependencies: US-029

---

## Epic 4: Network and Load Balancer Failover

### US-031: Orchestrate Route 53 DNS Failover
**As a** DR Operations Engineer  
**I want** automated Route 53 DNS failover to DR region endpoints  
**So that** traffic is redirected to DR region services during failover

#### Acceptance Criteria:
- **Given** Route 53 hosted zones with primary region records  
  **When** initiating failover  
  **Then** DNS records are updated to point to DR region endpoints
- **Given** multiple services requiring DNS updates  
  **When** orchestrating failover  
  **Then** all service DNS records are updated in parallel
- **Given** DNS record updates  
  **When** validating propagation  
  **Then** DNS resolution is verified to DR region endpoints
- **Given** failback operation  
  **When** returning to primary region  
  **Then** DNS records are updated back to primary region endpoints

#### Definition of Done:
- [ ] Route 53 DNS update logic implemented
- [ ] Parallel DNS update execution configured
- [ ] DNS propagation validation implemented
- [ ] Failback DNS update logic implemented
- [ ] DNS updates tested with test hosted zones
- [ ] Runbook includes DNS failover procedures

#### Story Points: 8  
#### Dependencies: US-007

---

### US-032: Update Route 53 Health Checks
**As a** DR Operations Engineer  
**I want** Route 53 health checks updated during failover  
**So that** health check monitoring points to DR region endpoints

#### Acceptance Criteria:
- **Given** Route 53 health checks for primary region  
  **When** initiating failover  
  **Then** health checks are updated to monitor DR region endpoints
- **Given** health check updates  
  **When** validating configuration  
  **Then** health checks are verified as monitoring correct endpoints
- **Given** failback operation  
  **When** returning to primary region  
  **Then** health checks are updated back to primary region endpoints

#### Definition of Done:
- [ ] Health check update logic implemented
- [ ] Health check validation implemented
- [ ] Failback health check update logic implemented
- [ ] Health check updates tested
- [ ] Runbook includes health check update procedures

#### Story Points: 5  
#### Dependencies: US-031

---

### US-033: Support Private Hosted Zone Failover
**As a** DR Operations Engineer  
**I want** private hosted zone DNS failover support  
**So that** internal service DNS is updated during failover

#### Acceptance Criteria:
- **Given** Route 53 private hosted zones  
  **When** initiating failover  
  **Then** private zone DNS records are updated to DR region endpoints
- **Given** VPC associations for private zones  
  **When** validating configuration  
  **Then** DR region VPC associations are verified
- **Given** private zone DNS updates  
  **When** validating resolution  
  **Then** DNS resolution from DR region VPCs is verified

#### Definition of Done:
- [ ] Private hosted zone DNS update logic implemented
- [ ] VPC association validation implemented
- [ ] DNS resolution validation from DR region VPCs implemented
- [ ] Private zone updates tested
- [ ] Runbook includes private zone failover procedures

#### Story Points: 5  
#### Dependencies: US-031

---

### US-034: Orchestrate ALB Failover
**As a** DR Operations Engineer  
**I want** ALB failover orchestrated via DNS updates  
**So that** application traffic is redirected to DR region load balancers

#### Acceptance Criteria:
- **Given** ALBs deployed in DR region  
  **When** initiating failover  
  **Then** Route 53 DNS records are updated to point to DR region ALB endpoints
- **Given** ALB target groups in DR region  
  **When** validating readiness  
  **Then** target health is verified before DNS update
- **Given** ALB failover  
  **When** validating traffic flow  
  **Then** traffic is confirmed routing to DR region targets
- **Given** failback operation  
  **When** returning to primary region  
  **Then** DNS records are updated back to primary region ALB endpoints

#### Definition of Done:
- [ ] ALB DNS update logic implemented
- [ ] Target health validation implemented
- [ ] Traffic flow validation implemented
- [ ] Failback DNS update logic implemented
- [ ] ALB failover tested with DR region ALBs
- [ ] Runbook includes ALB failover procedures

#### Story Points: 8  
#### Dependencies: US-031

---

### US-035: Deploy WAF Rules to Both Regions with CDK IaC
**As a** Security Engineer  
**I want** WAF rules deployed to both regions using CDK IaC  
**So that** security policies are consistent across regions and managed as code

#### Acceptance Criteria:
- **Given** WAF web ACL requirements  
  **When** deploying infrastructure  
  **Then** WAF web ACLs are deployed to both primary and DR regions using CDK
- **Given** WAF rule definitions in CDK  
  **When** deploying to both regions  
  **Then** identical rule sets are deployed to both regions
- **Given** DR region ALBs  
  **When** validating WAF association  
  **Then** web ACLs are verified as associated with DR region ALBs
- **Given** WAF rule updates  
  **When** updating CDK code  
  **Then** changes are deployed to both regions via CI/CD pipeline

#### Definition of Done:
- [ ] CDK code created for WAF web ACLs
- [ ] WAF rules deployed to both primary and DR regions
- [ ] WAF association with ALBs configured in both regions
- [ ] CI/CD pipeline configured for WAF deployments
- [ ] WAF deployment tested in both regions
- [ ] WAF IaC code documented

#### Story Points: 5  
#### Dependencies: US-034

### US-036: Document VPN Connectivity Validation (Manual Customer Failover)
**As a** DR Operations Engineer  
**I want** VPN connectivity validation procedures documented  
**So that** customers can manually validate VPN connectivity to DR region

#### Acceptance Criteria:
- **Given** global AWS Transit Gateway network in place  
  **When** documenting VPN procedures  
  **Then** connectivity validation steps are provided for customer use
- **Given** VPN connectivity to DR region  
  **When** validating readiness  
  **Then** TGW network connectivity is verified
- **Given** VPN failover requirement  
  **When** DR event occurs  
  **Then** customers perform manual VPN failover using documented procedures
- **Given** VPN connectivity  
  **When** monitoring status  
  **Then** operational awareness is maintained without automated orchestration

#### Definition of Done:
- [ ] VPN connectivity validation procedures documented
- [ ] Manual failover procedures provided for customers
- [ ] TGW network connectivity validation steps documented
- [ ] No automated routing updates or BGP changes implemented
- [ ] Monitoring for operational awareness configured
- [ ] Documentation reviewed and approved

#### Story Points: 3  
#### Dependencies: None

---

## Epic 5: Container and Kubernetes DR

### US-038: Orchestrate EKS Cluster Scale-Up
**As a** DR Operations Engineer  
**I want** automated scale-up of pre-deployed DR region EKS clusters  
**So that** containerized workloads can handle production traffic after failover

#### Acceptance Criteria:
- **Given** pre-deployed EKS 1.32 cluster in DR region (scaled down)  
  **When** initiating failover  
  **Then** DR region EKS cluster health and readiness are validated (private control plane)
- **Given** DR region EKS cluster  
  **When** scaling up  
  **Then** node groups are scaled up OR HPA and Cluster Autoscaler accommodate load increase gracefully
- **Given** EKS cluster scale-up  
  **When** nodes are ready  
  **Then** pod health and readiness are validated before completing failover
- **Given** EKS cluster failover  
  **When** validating workloads  
  **Then** application workloads deployed by existing CI/CD pipelines are verified
- **Given** EKS services  
  **When** coordinating with ALB  
  **Then** ALB Controller provisions load balancers for services

#### Definition of Done:
- [ ] EKS cluster health validation logic implemented (private control plane)
- [ ] Node group scale-up logic implemented OR HPA/CA accommodation documented
- [ ] Pod health and readiness validation implemented
- [ ] CI/CD pipeline integration verification implemented
- [ ] ALB Controller coordination logic implemented
- [ ] Scale-up tested with DR region EKS cluster
- [ ] Runbook includes EKS scale-up procedures

#### Story Points: 13  
#### Dependencies: US-031

### US-039: Verify CI/CD Pipeline Deployment to DR EKS Cluster and ECR
**As a** DR Operations Engineer  
**I want** verification that existing CI/CD pipelines deploy to DR region EKS clusters and ECR repositories  
**So that** application workloads and container images are current and ready for failover

#### Acceptance Criteria:
- **Given** existing CI/CD pipelines  
  **When** validating deployment  
  **Then** pipelines are verified to deploy to both primary and DR region EKS clusters
- **Given** container image builds  
  **When** validating image replication  
  **Then** images are confirmed as pushed to DR region ECR repositories
- **Given** DR region EKS cluster  
  **When** validating workloads  
  **Then** current application versions are confirmed as deployed
- **Given** CI/CD pipeline integration  
  **When** documenting procedures  
  **Then** integration points for DR operations are documented
- **Given** DR orchestration  
  **When** executing failover  
  **Then** focus is on cluster scale-up and DNS failover, not application deployment

#### Definition of Done:
- [ ] CI/CD pipeline deployment verification logic implemented
- [ ] ECR image replication verification implemented
- [ ] Application version validation implemented
- [ ] CI/CD integration points documented
- [ ] Verification tested with DR region EKS cluster and ECR
- [ ] Documentation clarifies DR orchestration scope (no manifest management)

#### Story Points: 5  
#### Dependencies: US-038

### US-040: Update EKS Ingress DNS Records
**As a** DR Operations Engineer  
**I want** Route 53 DNS records updated to point to DR region EKS ingress endpoints  
**So that** traffic is redirected to DR region containerized workloads

#### Acceptance Criteria:
- **Given** EKS cluster scaled up in DR region  
  **When** updating DNS records  
  **Then** Route 53 records are updated to point to DR region EKS ingress endpoints
- **Given** internal and external services  
  **When** updating DNS  
  **Then** both internal (private hosted zones) and external (public hosted zones) records are updated
- **Given** DNS updates  
  **When** validating propagation  
  **Then** DNS resolution is verified to DR region endpoints
- **Given** failback operation  
  **When** returning to primary region  
  **Then** DNS records are updated back to primary region endpoints

#### Definition of Done:
- [ ] Route 53 DNS update logic implemented for EKS ingress
- [ ] Internal and external DNS update support implemented
- [ ] DNS propagation validation implemented
- [ ] Failback DNS update logic implemented
- [ ] DNS updates tested with DR region EKS cluster
- [ ] Runbook includes DNS update procedures

#### Story Points: 5  
#### Dependencies: US-038, US-031

---

## Epic 6: Storage and Data Replication

### US-042: Validate S3 Bi-Directional Replication and Synchronization
**As a** DR Operations Engineer  
**I want** S3 bi-directional replication validated with synchronized state verification  
**So that** document storage and backups are consistent between regions for failover and failback

#### Acceptance Criteria:
- **Given** S3 buckets with bi-directional CRR configured  
  **When** validating replication  
  **Then** replication configuration is verified in both directions
- **Given** bi-directional replication  
  **When** validating synchronized state  
  **Then** replication metrics confirm data consistency between regions
- **Given** replication monitoring  
  **When** detecting issues  
  **Then** alerts are triggered for replication failures or excessive lag
- **Given** failover or failback operation  
  **When** validating readiness  
  **Then** synchronized state is confirmed before proceeding

#### Definition of Done:
- [ ] Bi-directional CRR validation logic implemented
- [ ] Synchronized state validation logic implemented
- [ ] Replication lag monitoring implemented in both directions
- [ ] Alert configuration for replication issues
- [ ] Validation tested with bi-directional S3 buckets
- [ ] Runbook includes replication validation procedures

#### Story Points: 5  
#### Dependencies: US-007

### US-043: Orchestrate FSx for ONTAP SnapMirror Failover
**As a** DR Operations Engineer  
**I want** FSx for ONTAP SnapMirror failover orchestrated to pre-configured DR instances  
**So that** application data is available in DR region with minimal data loss

#### Acceptance Criteria:
- **Given** FSx for ONTAP with SnapMirror to DR region  
  **When** initiating failover  
  **Then** SnapMirror failover is orchestrated to DR region FSx instance
- **Given** SnapMirror failover  
  **When** validating readiness  
  **Then** synchronization status is verified before proceeding
- **Given** failover completion  
  **When** updating application configuration  
  **Then** mount points are updated to DR region FSx for ONTAP
- **Given** failback operation  
  **When** returning to primary region  
  **Then** SnapMirror failback is orchestrated to primary region instance
- **Given** EFS used by EKS clusters  
  **When** validating readiness  
  **Then** EFS is assumed already mounted by DR clusters (no orchestration required)

#### Definition of Done:
- [ ] FSx for ONTAP SnapMirror failover logic implemented
- [ ] SnapMirror synchronization validation implemented
- [ ] Application mount point update mechanism implemented
- [ ] Failback logic implemented
- [ ] EFS validation confirms pre-mounted state (no orchestration)
- [ ] Failover tested with FSx for ONTAP instances
- [ ] Runbook includes FSx failover procedures

#### Story Points: 8  
#### Dependencies: US-007

### US-044: Validate EFS Pre-Mounted State for EKS Clusters
**As a** DR Operations Engineer  
**I want** EFS pre-mounted state validated for DR region EKS clusters  
**So that** containerized workloads have access to shared file storage after failover

#### Acceptance Criteria:
- **Given** EFS used by EKS clusters  
  **When** validating readiness  
  **Then** EFS is verified as already mounted by DR region EKS clusters
- **Given** EFS mount validation  
  **When** checking configuration  
  **Then** persistent volume claims and storage classes are confirmed
- **Given** EFS accessibility  
  **When** validating connectivity  
  **Then** network connectivity and security group rules are verified

#### Definition of Done:
- [ ] EFS pre-mounted state validation logic implemented
- [ ] PVC and storage class validation implemented
- [ ] Connectivity validation implemented
- [ ] Validation tested with DR region EKS clusters
- [ ] Documentation clarifies no EFS orchestration required

#### Story Points: 3  
#### Dependencies: US-038

### US-045: Validate Storage Gateway Pre-Deployment and S3 Replication
**As a** DR Operations Engineer  
**I want** Storage Gateway pre-deployment and S3 replication validated  
**So that** hybrid storage connectivity is ready for DR operations

#### Acceptance Criteria:
- **Given** Storage Gateways deployed in DR region by IaC  
  **When** validating infrastructure  
  **Then** DR region gateways are verified as deployed and accessible
- **Given** Storage Gateway backing S3 buckets  
  **When** validating replication  
  **Then** bi-directional S3 replication is confirmed
- **Given** Storage Gateway readiness  
  **When** monitoring status  
  **Then** operational awareness is maintained without failover orchestration

#### Definition of Done:
- [ ] Storage Gateway deployment validation logic implemented
- [ ] S3 bi-directional replication validation for backing buckets
- [ ] Connectivity validation implemented
- [ ] Validation tested with DR region Storage Gateways
- [ ] Documentation clarifies no failover orchestration required

#### Story Points: 3  
#### Dependencies: US-042

---

## Epic 7: Application Component Failover

### US-046: Validate Active Directory Multi-Region Availability
**As a** DR Operations Engineer  
**I want** Active Directory multi-region availability validated  
**So that** authentication and DNS services are confirmed ready for DR operations

#### Acceptance Criteria:
- **Given** Active Directory deployed in all regions  
  **When** validating infrastructure  
  **Then** domain controllers are verified as available in all regions
- **Given** Route 53 forwarder configurations  
  **When** validating DNS resolution  
  **Then** forwarder configurations are confirmed for AD DNS resolution
- **Given** AD replication  
  **When** monitoring status  
  **Then** replication status is tracked for operational awareness
- **Given** AD availability  
  **When** DR operations execute  
  **Then** no failover orchestration is required (AD already multi-region)

#### Definition of Done:
- [ ] AD domain controller availability validation logic implemented
- [ ] Route 53 forwarder configuration validation implemented
- [ ] AD replication status monitoring implemented
- [ ] Validation tested with multi-region AD infrastructure
- [ ] Documentation clarifies no AD failover orchestration required

#### Story Points: 3  
#### Dependencies: None

### US-046A: Automate AD DNS Record Registration for Linux Servers
**As a** DR Operations Engineer  
**I want** automated AD DNS record registration for Linux servers after recovery  
**So that** all recovered servers are properly registered in Active Directory DNS

#### Acceptance Criteria:
- **Given** Linux server recovered via DRS  
  **When** server is running in DR region  
  **Then** AD DNS A and PTR records are automatically created/updated
- **Given** Windows server recovered via DRS  
  **When** server is running in DR region  
  **Then** verify automatic AD DNS registration occurred
- **Given** DNS record registration  
  **When** registration completes  
  **Then** validate DNS resolution works for recovered server

#### Definition of Done:
- [ ] AD DNS record registration automation implemented for Linux servers
- [ ] Windows server automatic registration verification implemented
- [ ] A and PTR record creation/update logic implemented
- [ ] DNS resolution validation implemented
- [ ] Registration tested with recovered Linux and Windows servers
- [ ] Runbook includes AD DNS registration procedures

#### Story Points: 8  
#### Dependencies: US-017

### US-047: Monitor AD Replication Health
**As a** DR Operations Engineer  
**I want** AD replication health monitored across regions  
**So that** authentication services are confirmed operational during DR events

#### Acceptance Criteria:
- **Given** AD replication between regions  
  **When** monitoring health  
  **Then** replication lag and status are tracked
- **Given** replication issues  
  **When** detected  
  **Then** alerts are triggered for operational awareness
- **Given** AD health monitoring  
  **When** validating readiness  
  **Then** replication status is included in DR readiness reports

#### Definition of Done:
- [ ] AD replication health monitoring logic implemented
- [ ] Replication lag tracking implemented
- [ ] Alert configuration for replication issues
- [ ] Health metrics included in readiness reports
- [ ] Monitoring tested with multi-region AD infrastructure

#### Story Points: 3  
#### Dependencies: US-046

### US-048: Orchestrate SFTP Server Failover with Route 53
**As a** DR Operations Engineer  
**I want** SFTP server failover orchestrated using Route 53 DNS updates  
**So that** file transfer services redirect to DR region endpoints

#### Acceptance Criteria:
- **Given** SFTP server deployed in DR region  
  **When** initiating failover  
  **Then** Route 53 DNS records are updated to point to DR region SFTP endpoint
- **Given** SFTP failover  
  **When** validating readiness  
  **Then** SFTP connectivity and authentication are verified in DR region
- **Given** S3 backend buckets  
  **When** validating accessibility  
  **Then** bi-directional replication ensures data availability
- **Given** failback operation  
  **When** returning to primary region  
  **Then** DNS records are updated back to primary region endpoint

#### Definition of Done:
- [ ] Route 53 DNS update logic for SFTP implemented
- [ ] SFTP connectivity and authentication validation implemented
- [ ] S3 backend bucket accessibility validation implemented
- [ ] Failback DNS update logic implemented
- [ ] Failover tested with DR region SFTP server
- [ ] Runbook includes SFTP failover procedures with Route 53 emphasis

#### Story Points: 5  
#### Dependencies: US-031, US-042

### US-049: Recover Airflow EC2 Instances Using DRS
**As a** DR Operations Engineer  
**I want** Airflow and database EC2 instances recovered using DRS replication  
**So that** workflow orchestration services recover with minimal data loss

#### Acceptance Criteria:
- **Given** Airflow EC2 instances tagged with dr:recovery-strategy=drs  
  **When** initiating failover  
  **Then** DRS recovery jobs are created for Airflow instances
- **Given** Airflow database servers tagged with dr:recovery-strategy=drs  
  **When** initiating failover  
  **Then** DRS recovery jobs are created for database instances
- **Given** Airflow instances recovered in DR region  
  **When** recovery completes  
  **Then** DNS records or application configuration are updated to point to DR region instances
- **Given** failback operation  
  **When** returning to primary region  
  **Then** AllowLaunchingIntoThisInstance is used to launch into original instances

#### Definition of Done:
- [ ] Airflow EC2 instances tagged appropriately for DRS
- [ ] Airflow database instances tagged appropriately for DRS
- [ ] DRS recovery logic for Airflow instances implemented
- [ ] DNS or configuration update mechanism implemented
- [ ] Failback logic using AllowLaunchingIntoThisInstance implemented
- [ ] Recovery tested with test Airflow instances
- [ ] Runbook includes Airflow DRS recovery procedures

#### Story Points: 5  
#### Dependencies: US-017

---

## Epic 8: Testing and Validation

### US-050: Implement Isolated Bubble Test with AD Controller Cloning
**As a** DR Operations Engineer  
**I want** isolated bubble test drills with dedicated AD controller cloning and DNS resolution  
**So that** DR capabilities are validated without impacting production systems with complete isolation

#### Acceptance Criteria:
- **Given** bubble test requirement  
  **When** executing DR workflows  
  **Then** workflows execute in isolated test environment within DR region
- **Given** EC2 instance recovery testing  
  **When** using DRS  
  **Then** drill mode is used for isolated testing
- **Given** Active Directory requirement  
  **When** initiating bubble test  
  **Then** AD domain controllers are cloned into isolated test network
- **Given** cloned AD controllers  
  **When** configuring DNS resolution  
  **Then** DNS points to cloned AD servers (not AWS .2 resolver forwarding to live DCs)
- **Given** test environment  
  **When** deploying instances  
  **Then** instances are deployed in isolated VPC or subnets
- **Given** application functionality  
  **When** validating in test environment  
  **Then** functionality is verified with isolated AD infrastructure
- **Given** test completion  
  **When** cleaning up resources  
  **Then** test resources including cloned AD controllers are removed

#### Definition of Done:
- [ ] Isolated test environment configuration implemented
- [ ] DRS drill mode integration implemented
- [ ] AD controller cloning logic implemented
- [ ] DNS resolution to cloned AD servers configured
- [ ] Isolated VPC/subnet deployment logic implemented
- [ ] Application functionality validation implemented
- [ ] Cleanup logic for test resources including AD controllers
- [ ] Bubble test tested end-to-end with AD cloning
- [ ] Runbook includes bubble test procedures with AD cloning

#### Story Points: 13  
#### Dependencies: US-005, US-018

### US-051: Automate Test Resource Cleanup Including AD Controllers and DB Servers
**As a** DR Operations Engineer  
**I want** automated cleanup of test resources including cloned AD controllers and database servers  
**So that** bubble tests don't leave orphaned resources

#### Acceptance Criteria:
- **Given** bubble test completion  
  **When** cleanup executes  
  **Then** all test instances are terminated including cloned AD controllers and database servers
- **Given** test network resources  
  **When** cleanup executes  
  **Then** isolated VPC/subnet resources are removed
- **Given** cloned AD controllers  
  **When** cleanup executes  
  **Then** AD controller clones are properly decommissioned
- **Given** cloned database servers  
  **When** cleanup executes  
  **Then** database server clones are properly terminated and storage cleaned up
- **Given** cleanup failures  
  **When** detected  
  **Then** alerts are sent and manual cleanup procedures are provided

#### Definition of Done:
- [ ] Automated cleanup logic for test instances implemented
- [ ] AD controller clone decommissioning logic implemented
- [ ] Database server clone cleanup logic implemented
- [ ] Network resource cleanup logic implemented
- [ ] Cleanup failure detection and alerting implemented
- [ ] Manual cleanup procedures documented
- [ ] Cleanup tested with bubble test resources including AD and DB servers

#### Story Points: 5  
#### Dependencies: US-050

### US-052: Generate Bubble Test Report with AD Isolation Validation
**As a** DR Operations Engineer  
**I want** bubble test reports generated with AD isolation validation results  
**So that** test outcomes and AD isolation are documented for compliance

#### Acceptance Criteria:
- **Given** bubble test execution  
  **When** generating report  
  **Then** report includes test results, validation outcomes, and AD isolation status
- **Given** AD controller cloning  
  **When** generating report  
  **Then** report confirms DNS resolution to cloned AD servers
- **Given** test report  
  **When** documenting results  
  **Then** report includes RTO/RPO measurements and success/failure status
- **Given** test report  
  **When** distributing  
  **Then** report is stored in S3 and sent to stakeholders

#### Definition of Done:
- [ ] Test report generation logic implemented
- [ ] AD isolation validation results included in report
- [ ] DNS resolution validation included in report
- [ ] RTO/RPO measurement included in report
- [ ] Report storage and distribution implemented
- [ ] Report format reviewed and approved

#### Story Points: 5  
#### Dependencies: US-050

### US-053: Create Customer-Scoped Game Day Test Scenarios
**As a** DR Operations Engineer  
**I want** customer-scoped Game Day test scenarios created  
**So that** specific customer environments can be tested end-to-end

#### Acceptance Criteria:
- **Given** customer-requested Game Day  
  **When** creating test scenario  
  **Then** scenario is scoped to specific customer environment using Customer and Environment tags
- **Given** test scenario  
  **When** defining scope  
  **Then** scenario includes complete failover workflow for customer environment
- **Given** test scenario  
  **When** documenting procedures  
  **Then** scenario includes validation steps and success criteria for customer
- **Given** test scenario  
  **When** isolating testing  
  **Then** scenario ensures no impact to other customers

#### Definition of Done:
- [ ] Customer-scoped test scenario templates created
- [ ] Customer and Environment tag scoping logic implemented
- [ ] Complete failover workflow scenarios documented
- [ ] Validation steps and success criteria defined
- [ ] Isolation procedures documented
- [ ] Scenarios reviewed and approved

#### Story Points: 8  
#### Dependencies: US-050

### US-054: Execute Customer-Scoped Game Day Test Framework
**As a** DR Operations Engineer  
**I want** customer-scoped Game Day tests executed  
**So that** end-to-end DR capabilities are validated for specific customer environments

#### Acceptance Criteria:
- **Given** customer-requested Game Day  
  **When** executing test  
  **Then** complete failover workflow is executed for specified customer environment
- **Given** customer environment failover  
  **When** validating functionality  
  **Then** application functionality is verified for customer in DR region
- **Given** test execution  
  **When** tracking progress  
  **Then** progress and results are tracked for customer environment
- **Given** test completion  
  **When** generating report  
  **Then** report includes RTO/RPO measurements for customer environment
- **Given** test completion  
  **When** performing failback  
  **Then** customer environment is restored to primary region

#### Definition of Done:
- [ ] Customer-scoped Game Day execution logic implemented
- [ ] Complete failover workflow for customer environment tested
- [ ] Application functionality validation implemented
- [ ] Progress tracking for customer environment implemented
- [ ] RTO/RPO measurement for customer environment implemented
- [ ] Failback logic for customer environment implemented
- [ ] Game Day tested end-to-end with customer scope
- [ ] Runbook includes customer-scoped Game Day procedures

#### Story Points: 8  
#### Dependencies: US-053

### US-055: Implement DR Readiness Validation
**As a** DR Operations Engineer  
**I want** comprehensive DR readiness validation across all components  
**So that** DR capabilities are verified before actual failover events

#### Acceptance Criteria:
- **Given** DR infrastructure deployed  
  **When** running readiness validation  
  **Then** all critical components are validated: DRS replication, database replication, network connectivity, storage replication
- **Given** readiness validation execution  
  **When** checking DRS status  
  **Then** replication lag and readiness are verified for all source servers
- **Given** readiness validation execution  
  **When** checking database replication  
  **Then** SQL Server AG synchronization status is verified
- **Given** readiness validation execution  
  **When** checking network readiness  
  **Then** Route 53 configurations and VPN connectivity are verified
- **Given** readiness validation failures  
  **When** detected  
  **Then** failures are reported with remediation guidance

#### Definition of Done:
- [ ] Readiness validation logic implemented for all components
- [ ] DRS replication validation implemented
- [ ] Database replication validation implemented
- [ ] Network readiness validation implemented
- [ ] Storage replication validation implemented
- [ ] Failure reporting with remediation guidance implemented
- [ ] Validation tested end-to-end

#### Story Points: 8  
#### Dependencies: US-022, US-025

---

### US-056: Generate DR Readiness Report
**As a** DR Operations Manager  
**I want** automated DR readiness reports generated  
**So that** DR readiness status is visible to stakeholders

#### Acceptance Criteria:
- **Given** readiness validation execution  
  **When** generating report  
  **Then** report includes status of all components: DRS, databases, network, storage, EKS
- **Given** readiness report  
  **When** components are not ready  
  **Then** issues are highlighted with remediation guidance
- **Given** report generation  
  **When** scheduled daily  
  **Then** report is automatically generated and distributed
- **Given** readiness report  
  **When** reviewing status  
  **Then** report includes RTO/RPO readiness assessment

#### Definition of Done:
- [ ] Readiness report generation logic implemented
- [ ] Report format defined (HTML/PDF)
- [ ] Scheduled report generation configured
- [ ] Report distribution via email/S3 configured
- [ ] RTO/RPO readiness assessment included
- [ ] Sample reports reviewed and approved

#### Story Points: 5  
#### Dependencies: US-055

---

## Epic 9: Monitoring and Observability

### US-057: Implement Orchestration Monitoring
**As a** DR Operations Engineer  
**I want** comprehensive monitoring of DR orchestration operations  
**So that** orchestration health and progress are visible in real-time

#### Acceptance Criteria:
- **Given** DR orchestration execution  
  **When** workflows are running  
  **Then** execution metrics are published to CloudWatch
- **Given** orchestration metrics  
  **When** monitoring execution  
  **Then** metrics include: execution duration, success/failure rates, resource counts, wave progress
- **Given** orchestration failures  
  **When** errors occur  
  **Then** error details are logged with context for troubleshooting
- **Given** long-running operations  
  **When** monitoring progress  
  **Then** progress indicators show completion percentage

#### Definition of Done:
- [ ] CloudWatch metrics published for all orchestration operations
- [ ] Metrics include execution duration, success/failure rates, resource counts, wave progress
- [ ] Error logging with context implemented
- [ ] Progress indicators implemented for long-running operations
- [ ] Monitoring tested with orchestration workflows
- [ ] Metrics documented

#### Story Points: 8  
#### Dependencies: US-004

---

### US-058: Create CloudWatch Dashboards
**As a** DR Operations Manager  
**I want** CloudWatch dashboards for DR operations  
**So that** operational status is visible at a glance

#### Acceptance Criteria:
- **Given** DR orchestration metrics  
  **When** creating dashboards  
  **Then** dashboards display key metrics: execution status, RTO/RPO, resource health, replication status
- **Given** dashboard widgets  
  **When** organizing layout  
  **Then** critical metrics are prominently displayed
- **Given** dashboard access  
  **When** operations team views dashboards  
  **Then** dashboards are accessible via CloudWatch console
- **Given** dashboard updates  
  **When** metrics change  
  **Then** dashboards refresh automatically

#### Definition of Done:
- [ ] CloudWatch dashboards created for DR operations
- [ ] Dashboards include key metrics: execution status, RTO/RPO, resource health, replication status
- [ ] Dashboard layout optimized for operations team
- [ ] Dashboard access configured
- [ ] Auto-refresh configured
- [ ] Dashboard usage documented

#### Story Points: 5  
#### Dependencies: US-057

---

### US-059: Implement RTO/RPO Measurement
**As a** DR Operations Manager  
**I want** automated RTO/RPO measurement during DR operations  
**So that** recovery objectives are tracked and reported

#### Acceptance Criteria:
- **Given** DR failover operation  
  **When** operation starts  
  **Then** start timestamp is recorded
- **Given** DR failover operation  
  **When** operation completes  
  **Then** end timestamp is recorded and RTO is calculated
- **Given** DRS replication  
  **When** measuring RPO  
  **Then** replication lag is measured and reported as RPO
- **Given** RTO/RPO measurements  
  **When** operation completes  
  **Then** measurements are published to CloudWatch and included in reports

#### Definition of Done:
- [ ] RTO measurement logic implemented (start to completion)
- [ ] RPO measurement logic implemented (replication lag)
- [ ] Measurements published to CloudWatch
- [ ] Measurements included in operation reports
- [ ] Measurement accuracy validated
- [ ] Measurement documentation created

#### Story Points: 8  
#### Dependencies: US-057

---

### US-060: Implement Audit Logging
**As a** Security Engineer  
**I want** comprehensive audit logging for DR operations  
**So that** all actions are traceable for compliance and troubleshooting

#### Acceptance Criteria:
- **Given** DR orchestration operations  
  **When** executing actions  
  **Then** all actions are logged with timestamp, user, operation, and outcome
- **Given** audit logs  
  **When** storing logs  
  **Then** logs are stored in CloudWatch Logs with retention policy
- **Given** audit log entries  
  **When** logging actions  
  **Then** entries include: timestamp, user identity, operation type, resource IDs, outcome, error details
- **Given** audit log access  
  **When** reviewing logs  
  **Then** logs are searchable and filterable

#### Definition of Done:
- [ ] Audit logging implemented for all DR operations
- [ ] Log entries include required fields: timestamp, user, operation, resources, outcome
- [ ] Logs stored in CloudWatch Logs with retention policy
- [ ] Log search and filtering capabilities validated
- [ ] Audit logging tested with all operation types
- [ ] Audit log format documented

#### Story Points: 8  
#### Dependencies: US-004

---

### US-061: Configure CloudWatch Alarms
**As a** DR Operations Engineer  
**I want** CloudWatch alarms configured for DR operations  
**So that** issues are detected and escalated automatically

#### Acceptance Criteria:
- **Given** DR orchestration metrics  
  **When** configuring alarms  
  **Then** alarms are created for critical conditions: execution failures, replication lag, resource health
- **Given** alarm thresholds  
  **When** defining thresholds  
  **Then** thresholds are based on operational requirements and SLAs
- **Given** alarm state changes  
  **When** alarms trigger  
  **Then** alarm notifications are sent to SNS topics
- **Given** alarm configuration  
  **When** validating alarms  
  **Then** alarms trigger correctly for test conditions

#### Definition of Done:
- [ ] CloudWatch alarms configured for critical conditions
- [ ] Alarm thresholds defined based on requirements
- [ ] SNS topics configured for alarm notifications
- [ ] Alarms tested with simulated conditions
- [ ] Alarm configuration documented
- [ ] Alarm response procedures documented

#### Story Points: 5  
#### Dependencies: US-057

---

### US-062: Implement Alert Routing
**As a** DR Operations Manager  
**I want** alert routing configured for different severity levels  
**So that** alerts reach the appropriate teams

#### Acceptance Criteria:
- **Given** CloudWatch alarms  
  **When** alarms trigger  
  **Then** alerts are routed based on severity: critical, warning, informational
- **Given** alert routing rules  
  **When** configuring routing  
  **Then** critical alerts go to on-call team, warnings to operations team, info to monitoring dashboards
- **Given** alert delivery  
  **When** sending alerts  
  **Then** alerts are delivered via multiple channels: email, SMS, Slack/Teams
- **Given** alert escalation  
  **When** alerts are not acknowledged  
  **Then** escalation procedures are triggered

#### Definition of Done:
- [ ] Alert routing configured by severity level
- [ ] Multiple delivery channels configured: email, SMS, Slack/Teams
- [ ] Escalation procedures implemented
- [ ] Alert routing tested with test alarms
- [ ] Alert routing configuration documented
- [ ] Team contact information maintained

#### Story Points: 5  
#### Dependencies: US-061

---

## Epic 10: Operational Management

### US-063: Create Failover Runbook
**As a** DR Operations Engineer  
**I want** comprehensive failover runbook documentation  
**So that** failover operations can be executed consistently and reliably

#### Acceptance Criteria:
- **Given** failover procedures  
  **When** documenting runbook  
  **Then** runbook includes step-by-step instructions for all failover scenarios
- **Given** failover runbook  
  **When** documenting CLI commands  
  **Then** all required CLI commands with parameters are documented
- **Given** failover runbook  
  **When** documenting validation steps  
  **Then** validation procedures for each component are included
- **Given** failover runbook  
  **When** documenting troubleshooting  
  **Then** common issues and resolutions are documented

#### Definition of Done:
- [ ] Failover runbook created with complete procedures
- [ ] CLI commands documented with examples
- [ ] Validation steps documented for all components
- [ ] Troubleshooting section included
- [ ] Runbook reviewed and approved by operations team
- [ ] Runbook tested during Game Day exercise

#### Story Points: 5  
#### Dependencies: All operational FRs

---

### US-064: Create Failback Runbook
**As a** DR Operations Engineer  
**I want** comprehensive failback runbook documentation  
**So that** failback operations can be executed consistently and reliably

#### Acceptance Criteria:
- **Given** failback procedures  
  **When** documenting runbook  
  **Then** runbook includes step-by-step instructions for all failback scenarios
- **Given** failback runbook  
  **When** documenting prerequisites  
  **Then** primary region readiness validation steps are documented
- **Given** failback runbook  
  **When** documenting CLI commands  
  **Then** all required CLI commands with parameters are documented
- **Given** failback runbook  
  **When** documenting validation steps  
  **Then** validation procedures for each component are included

#### Definition of Done:
- [ ] Failback runbook created with complete procedures
- [ ] Primary region readiness validation documented
- [ ] CLI commands documented with examples
- [ ] Validation steps documented for all components
- [ ] Runbook reviewed and approved by operations team
- [ ] Runbook tested during failback exercise

#### Story Points: 5  
#### Dependencies: All operational FRs

---

### US-065: Create Testing Runbook
**As a** DR Operations Engineer  
**I want** comprehensive testing runbook documentation  
**So that** DR testing can be executed consistently and safely

#### Acceptance Criteria:
- **Given** testing procedures  
  **When** documenting runbook  
  **Then** runbook includes procedures for bubble tests and Game Day exercises
- **Given** testing runbook  
  **When** documenting bubble tests  
  **Then** isolated test environment setup and cleanup procedures are documented
- **Given** testing runbook  
  **When** documenting Game Day exercises  
  **Then** customer-scoped test scenarios and validation steps are documented
- **Given** testing runbook  
  **When** documenting safety measures  
  **Then** isolation procedures to prevent production impact are documented

#### Definition of Done:
- [ ] Testing runbook created with complete procedures
- [ ] Bubble test procedures documented
- [ ] Game Day exercise procedures documented
- [ ] Safety and isolation measures documented
- [ ] Runbook reviewed and approved by operations team
- [ ] Runbook tested during test exercises

#### Story Points: 5  
#### Dependencies: US-050, US-053

---

### US-066: Document Troubleshooting Procedures
**As a** DR Operations Engineer  
**I want** comprehensive troubleshooting documentation  
**So that** common issues can be resolved quickly during DR operations

#### Acceptance Criteria:
- **Given** common DR operation issues  
  **When** documenting troubleshooting  
  **Then** issue symptoms, root causes, and resolutions are documented
- **Given** troubleshooting documentation  
  **When** organizing content  
  **Then** issues are organized by component: DRS, databases, network, storage, EKS
- **Given** troubleshooting documentation  
  **When** documenting resolutions  
  **Then** step-by-step resolution procedures are provided
- **Given** troubleshooting documentation  
  **When** documenting escalation  
  **Then** escalation procedures and contact information are included

#### Definition of Done:
- [ ] Troubleshooting documentation created
- [ ] Issues organized by component
- [ ] Resolution procedures documented
- [ ] Escalation procedures documented
- [ ] Documentation reviewed and approved by operations team
- [ ] Documentation updated based on actual DR operations

#### Story Points: 5  
#### Dependencies: All operational FRs

---

## Epic 11: Security and Compliance

### US-067: Leverage IAM Identity Center - Okta Integration for MFA
**As a** Security Engineer  
**I want** MFA leveraged from existing IAM Identity Center - Okta integration  
**So that** production DR operations require multi-factor authentication

#### Acceptance Criteria:
- **Given** existing IAM Identity Center - Okta integration  
  **When** accessing DR operations  
  **Then** MFA is enforced through existing integration
- **Given** production DR operations  
  **When** initiating operations  
  **Then** user authentication includes MFA verification
- **Given** MFA enforcement  
  **When** monitoring access  
  **Then** access logs include MFA verification status

#### Definition of Done:
- [ ] IAM Identity Center - Okta integration verified for DR operations
- [ ] MFA enforcement validated for production operations
- [ ] Access logging with MFA status implemented
- [ ] MFA requirements documented in runbooks

#### Story Points: 3  
#### Dependencies: US-009

### US-068: Leverage LZA-Deployed KMS CMKs for Encryption
**As a** Security Engineer  
**I want** encryption at rest using existing LZA-deployed KMS CMKs  
**So that** data is protected with customer-managed keys

#### Acceptance Criteria:
- **Given** existing LZA-deployed KMS CMKs  
  **When** configuring encryption  
  **Then** CMKs are used for all data encryption at rest (not just KMS)
- **Given** DR resources  
  **When** deploying in DR region  
  **Then** DR region CMKs are used for encryption
- **Given** cross-region replication  
  **When** replicating encrypted data  
  **Then** appropriate CMKs are used in each region
- **Given** encryption configuration  
  **When** validating compliance  
  **Then** all resources use CMKs (not AWS-managed keys)

#### Definition of Done:
- [ ] LZA-deployed CMK usage verified for all DR resources
- [ ] DR region CMK configuration validated
- [ ] Cross-region encryption configuration tested
- [ ] Encryption compliance validation implemented
- [ ] CMK usage documented in architecture

#### Story Points: 5  
#### Dependencies: None

### US-069: Configure Encryption in Transit
**As a** Security Engineer  
**I want** encryption in transit configured for all DR communications  
**So that** data is protected during transmission

#### Acceptance Criteria:
- **Given** DR orchestration communications  
  **When** configuring encryption  
  **Then** TLS 1.2+ is enforced for all API communications
- **Given** database replication  
  **When** configuring encryption  
  **Then** replication traffic is encrypted in transit
- **Given** DRS replication  
  **When** configuring encryption  
  **Then** replication traffic uses encrypted channels
- **Given** application traffic  
  **When** configuring load balancers  
  **Then** HTTPS listeners with valid certificates are configured

#### Definition of Done:
- [ ] TLS 1.2+ enforced for all API communications
- [ ] Database replication encryption configured
- [ ] DRS replication encryption verified
- [ ] Load balancer HTTPS listeners configured
- [ ] Certificate management documented
- [ ] Encryption in transit validated

#### Story Points: 5  
#### Dependencies: None

---

### US-070: Implement Secrets Management
**As a** Security Engineer  
**I want** secrets managed securely using AWS Secrets Manager  
**So that** credentials and sensitive data are protected

#### Acceptance Criteria:
- **Given** database credentials  
  **When** storing secrets  
  **Then** credentials are stored in AWS Secrets Manager
- **Given** API keys and tokens  
  **When** storing secrets  
  **Then** secrets are encrypted with KMS CMKs
- **Given** DR orchestration workflows  
  **When** accessing secrets  
  **Then** secrets are retrieved securely from Secrets Manager
- **Given** secret rotation  
  **When** credentials change  
  **Then** automatic rotation is configured where supported

#### Definition of Done:
- [ ] Secrets Manager configured for all credentials
- [ ] KMS CMK encryption configured
- [ ] Secret retrieval logic implemented in workflows
- [ ] Automatic rotation configured where supported
- [ ] Secret access logging configured
- [ ] Secrets management documented

#### Story Points: 8  
#### Dependencies: US-011

---

### US-072: Implement Security Group Rules with CDK IaC
**As a** Security Engineer  
**I want** security group rules created for DR resources using CDK IaC  
**So that** network access is restricted to authorized sources and managed as code

#### Acceptance Criteria:
- **Given** DR region resources  
  **When** deploying infrastructure with CDK  
  **Then** security groups are created with least privilege access rules
- **Given** cross-region communication requirements  
  **When** defining security groups in CDK  
  **Then** only required ports and protocols are allowed
- **Given** security group rules in CDK  
  **When** documenting configuration  
  **Then** rule purposes and sources are documented in code comments
- **Given** security group changes  
  **When** updating CDK code  
  **Then** changes are reviewed and deployed via CI/CD pipeline

#### Definition of Done:
- [ ] CDK code created for all DR resource security groups
- [ ] Least privilege rules implemented in CDK
- [ ] Cross-region communication rules configured
- [ ] Rule documentation in code comments
- [ ] CI/CD pipeline configured for security group deployments
- [ ] Security groups validated in both regions
- [ ] Security group IaC code documented

#### Story Points: 8  
#### Dependencies: None

---

### US-073: Configure VPC Endpoints
**As a** Security Engineer  
**I want** VPC endpoints configured for AWS services  
**So that** traffic remains within AWS network

#### Acceptance Criteria:
- **Given** DR region VPCs  
  **When** configuring VPC endpoints  
  **Then** endpoints are created for all required AWS services
- **Given** VPC endpoints  
  **When** configuring security  
  **Then** endpoint policies restrict access appropriately
- **Given** DR orchestration workflows  
  **When** accessing AWS services  
  **Then** traffic routes through VPC endpoints
- **Given** VPC endpoint configuration  
  **When** validating connectivity  
  **Then** service connectivity through endpoints is verified

#### Definition of Done:
- [ ] VPC endpoints configured for required services
- [ ] Endpoint policies configured
- [ ] Traffic routing through endpoints validated
- [ ] Connectivity testing completed
- [ ] VPC endpoint configuration documented

#### Story Points: 5  
#### Dependencies: None
**As a** Compliance Engineer  
**I want** AWS Config rules leveraged from existing LZA deployment  
**So that** DR resources comply with organizational standards

#### Acceptance Criteria:
- **Given** existing LZA-deployed Config rules  
  **When** deploying DR resources  
  **Then** resources are validated against existing Config rules
- **Given** Config rule violations  
  **When** detected  
  **Then** violations are reported and remediation is triggered
- **Given** DR-specific compliance requirements  
  **When** additional rules are needed  
  **Then** rules are added to LZA configuration

#### Definition of Done:
- [ ] LZA-deployed Config rules verified for DR resources
- [ ] Config rule compliance validation implemented
- [ ] Violation reporting and remediation configured
- [ ] DR-specific Config rules identified and documented
- [ ] Config rule coverage documented

#### Story Points: 3  
#### Dependencies: US-002

---

## Epic 12: Performance and Scalability

### US-075: Optimize Resource Discovery Performance for 500-1500 Servers
**As a** DR Operations Engineer  
**I want** resource discovery optimized for 500 current and 1500 future servers  
**So that** discovery completes within acceptable timeframes at scale

#### Acceptance Criteria:
- **Given** 500 servers currently deployed  
  **When** running resource discovery  
  **Then** discovery completes within 5 minutes
- **Given** future scale of 1500 servers  
  **When** running resource discovery  
  **Then** discovery architecture supports scale without performance degradation
- **Given** AWS Resource Explorer APIs  
  **When** querying resources  
  **Then** pagination and filtering optimize query performance
- **Given** cached inventory  
  **When** cache is valid  
  **Then** cached results are used to reduce discovery time

#### Definition of Done:
- [ ] Resource discovery optimized for 500 current servers
- [ ] Architecture validated for 1500 future servers
- [ ] AWS Resource Explorer pagination and filtering implemented
- [ ] Caching strategy optimized for scale
- [ ] Performance testing completed at current and future scale
- [ ] Performance metrics documented

#### Story Points: 8  
#### Dependencies: US-003, US-010

### US-076: Implement Parallel Wave Execution with Alternative Instance Types
**As a** DR Operations Engineer  
**I want** parallel wave execution with support for alternative instance types  
**So that** recovery operations complete efficiently even when preferred instance types are unavailable

#### Acceptance Criteria:
- **Given** resources within the same wave  
  **When** orchestrating recovery  
  **Then** resources recover in parallel for efficiency
- **Given** preferred instance type unavailable  
  **When** recovering instances  
  **Then** alternative instance types are used based on predefined mappings
- **Given** parallel execution  
  **When** monitoring progress  
  **Then** wave-level progress is tracked and reported
- **Given** alternative instance types  
  **When** used for recovery  
  **Then** instance type substitutions are logged and reported

#### Definition of Done:
- [ ] Parallel execution within waves implemented
- [ ] Alternative instance type mapping defined
- [ ] Instance type substitution logic implemented
- [ ] Wave-level progress tracking implemented
- [ ] Alternative instance type usage logging implemented
- [ ] Parallel execution tested with multiple waves
- [ ] Alternative instance type testing completed

#### Story Points: 8  
#### Dependencies: US-004

### US-077: Optimize Step Functions Execution
**As a** DR Operations Engineer  
**I want** Step Functions execution optimized for performance  
**So that** orchestration overhead is minimized

#### Acceptance Criteria:
- **Given** Step Functions workflows  
  **When** optimizing execution  
  **Then** parallel execution is maximized where possible
- **Given** workflow state transitions  
  **When** optimizing performance  
  **Then** unnecessary state transitions are eliminated
- **Given** workflow execution  
  **When** measuring overhead  
  **Then** Step Functions overhead is less than 10% of total RTO
- **Given** large-scale operations  
  **When** executing workflows  
  **Then** workflows handle 500+ resources efficiently

#### Definition of Done:
- [ ] Parallel execution maximized in workflows
- [ ] Unnecessary state transitions eliminated
- [ ] Performance overhead measured and documented
- [ ] Large-scale execution tested (500+ resources)
- [ ] Optimization recommendations documented

#### Story Points: 5  
#### Dependencies: US-004

---

### US-079: Conduct Scale Testing for 1500 Servers and 100 Customer Environments
**As a** DR Operations Engineer  
**I want** scale testing conducted for 1500 servers across 100 customer environments  
**So that** DR orchestration is validated at future production scale

#### Acceptance Criteria:
- **Given** future scale of 1500 servers  
  **When** conducting scale testing  
  **Then** orchestration completes successfully for all servers
- **Given** 100 customer environments  
  **When** testing customer-scoped operations  
  **Then** customer isolation and scoping work correctly at scale
- **Given** scale testing  
  **When** measuring performance  
  **Then** RTO/RPO targets are met at scale
- **Given** scale testing  
  **When** monitoring resource usage  
  **Then** AWS service limits are not exceeded

#### Definition of Done:
- [ ] Scale testing plan created for 1500 servers
- [ ] Scale testing plan includes 100 customer environments
- [ ] Test environment configured for scale testing
- [ ] Scale testing executed successfully
- [ ] RTO/RPO measurements at scale documented
- [ ] Service limit usage at scale documented
- [ ] Performance bottlenecks identified and addressed
- [ ] Scale testing results reviewed and approved

#### Story Points: 13  
#### Dependencies: All core FRs

---

## Story Prioritization and Sprint Planning

### Sprint 1: Foundation and Infrastructure (Weeks 1-2) - 44 points
**Priority: Critical - Core infrastructure and orchestration foundation**
- US-001: Update Existing Tag Documentation with DR Taxonomy (3 points)
- US-002: Implement Tag Validation with SCPs and Tag Policies (5 points)
- US-009: Configure Cross-Account IAM Roles via LZA (5 points)
- US-011: Create DR Orchestration Configuration Management (5 points)
- US-080: Deploy DR Region FSx ONTAP File Systems (8 points)
- US-081: Deploy DR Region EKS Clusters (13 points)
- US-084: Vend DR Accounts for DRS Scale (8 points)

### Sprint 2: Infrastructure and Discovery (Weeks 3-4) - 34 points
**Priority: Critical - Complete infrastructure and resource discovery**
- US-003: Develop Tag-Based Resource Discovery Using AWS Resource Explorer (8 points)
- US-010: Implement Resource Discovery Caching with Configurable TTL (5 points)
- US-068: Leverage LZA-Deployed KMS CMKs for Encryption (5 points)
- US-082: Deploy DR Region EFS File Systems (5 points)
- US-083: Deploy DR Region ECR Repositories (5 points)
- US-069: Configure Encryption in Transit (5 points)
- US-073: Configure VPC Endpoints (5 points)

### Sprint 3: Orchestration Engine (Weeks 5-6) - 50 points
**Priority: Critical - Core orchestration workflows**
- US-004: Create Step Functions DR Orchestrator Workflow (13 points)
- US-005: Implement Wave-Based Orchestration Logic (8 points)
- US-006: Implement Lifecycle Orchestration Workflow with Customer/Environment Scoping (8 points)
- US-007: Develop Module Factory Pattern (8 points)
- US-008: Implement CLI-Triggered DR Operations with Customer/Environment Scoping (5 points)
- US-012: Implement Approval Workflow for Production Failover (8 points)

### Sprint 4: Core Recovery Modules (Weeks 7-8) - 61 points
**Priority: High - Critical workload recovery**
- US-017: Integrate with AWS DRS Using AllowLaunchingIntoThisInstance (8 points)
- US-013: Support AllowLaunchingIntoThisInstance Capability (8 points)
- US-019: Handle DRS API Rate Limits (5 points)
- US-024: Orchestrate SQL Server Always On Failover with Bubble Test Cloning (13 points)
- US-027: Orchestrate Valkey Endpoint Failover via Route 53 (5 points)
- US-031: Orchestrate Route 53 DNS Failover (8 points)
- US-032: Update Route 53 Health Checks (5 points)
- US-034: Orchestrate ALB Failover (8 points)
- US-046A: Automate AD DNS Record Registration for Linux Servers (8 points)

### Sprint 5: Extended Recovery and Monitoring (Weeks 9-10) - 49 points
**Priority: High - Extended recovery capabilities**
- US-020: Implement DRS Configuration Management (Simplified) (5 points)
- US-021: Validate DRS Readiness for Pre-Provisioned Instances (5 points)
- US-022: Implement DRS Replication Monitoring (5 points)
- US-029: Recover MongoDB EC2 Instances Using DRS (5 points)
- US-038: Orchestrate EKS Cluster Scale-Up (13 points)
- US-043: Orchestrate FSx for ONTAP SnapMirror Failover (8 points)
- US-057: Implement Orchestration Monitoring (8 points)
- US-060: Implement Audit Logging (8 points)

### Sprint 6: Testing and Validation (Weeks 11-12) - 49 points
**Priority: High - DR testing capabilities**
- US-018: Implement DRS Drill Mode for Testing (5 points)
- US-050: Implement Isolated Bubble Test with AD Controller Cloning (13 points)
- US-051: Automate Test Resource Cleanup Including AD Controllers and DB Servers (5 points)
- US-053: Create Customer-Scoped Game Day Test Scenarios (8 points)
- US-055: Implement DR Readiness Validation (8 points)
- US-059: Implement RTO/RPO Measurement (8 points)
- US-070: Implement Secrets Management (8 points)

### Sprint 7: Documentation and Optimization (Weeks 13-14) - 46 points
**Priority: Medium - Operational readiness**
- US-023: Create DRS Readiness Report (5 points)
- US-054: Execute Customer-Scoped Game Day Test Framework (8 points)
- US-063: Create Failover Runbook (5 points)
- US-064: Create Failback Runbook (5 points)
- US-065: Create Testing Runbook (5 points)
- US-075: Optimize Resource Discovery Performance for 500-1500 Servers (8 points)
- US-076: Implement Parallel Wave Execution with Alternative Instance Types (8 points)
- US-077: Optimize Step Functions Execution (5 points)

### Sprint 8: Additional Components and Security (Weeks 15-16) - 38 points
**Priority: Medium - Additional components and security hardening**
- US-033: Support Private Hosted Zone Failover (5 points)
- US-035: Synchronize WAF Rules to DR Region (5 points)
- US-039: Verify CI/CD Pipeline Deployment to DR EKS Cluster and ECR (5 points)
- US-040: Update EKS Ingress DNS Records (5 points)
- US-042: Validate S3 Bi-Directional Replication and Synchronization (5 points)
- US-048: Orchestrate SFTP Server Failover with Route 53 (5 points)
- US-072: Implement Security Group Rules (8 points)

### Future Backlog (Post-MVP)
**Priority: Low - Enhancements and additional components**
- US-025: Validate SQL Server Replication Status (5 points)
- US-026: Implement SQL Server Failback (8 points)
- US-028: Validate Valkey Infrastructure Deployment (3 points)
- US-030: Validate MongoDB Service Health After Recovery (3 points)
- US-036: Document VPN Connectivity Validation (3 points) - manual customer failover
- US-044: Validate EFS Pre-Mounted State for EKS Clusters (3 points)
- US-045: Validate Storage Gateway Pre-Deployment and S3 Replication (3 points)
- US-046: Validate Active Directory Multi-Region Availability (3 points)
- US-047: Monitor AD Replication Health (3 points)
- US-049: Recover Airflow EC2 Instances Using DRS (5 points)
- US-052: Generate Bubble Test Report with AD Isolation Validation (5 points)
- US-056: Generate DR Readiness Report (5 points)
- US-058: Create CloudWatch Dashboards (5 points)
- US-061: Configure CloudWatch Alarms (5 points)
- US-062: Implement Alert Routing (5 points)
- US-066: Document Troubleshooting Procedures (5 points)
- US-067: Leverage IAM Identity Center - Okta Integration for MFA (3 points)
- US-079: Conduct Scale Testing for 1500 Servers and 100 Customer Environments (13 points)

---

## Epic 13: DR Infrastructure Deployment

### US-080: Deploy DR Region FSx ONTAP File Systems
**As a** Cloud Infrastructure Architect  
**I want** FSx for ONTAP file systems deployed in DR region  
**So that** application data storage is available for DR operations

#### Acceptance Criteria:
- **Given** primary region FSx ONTAP file systems  
  **When** deploying DR infrastructure  
  **Then** equivalent FSx ONTAP file systems are deployed in DR region
- **Given** DR region FSx ONTAP deployment  
  **When** configuring SnapMirror  
  **Then** SnapMirror replication is configured from primary to DR region
- **Given** FSx ONTAP file systems  
  **When** validating deployment  
  **Then** file systems are accessible and SnapMirror is operational
- **Given** application mount points  
  **When** documenting configuration  
  **Then** DR region mount points are documented for failover

#### Definition of Done:
- [ ] FSx ONTAP file systems deployed in DR region
- [ ] SnapMirror replication configured
- [ ] File system accessibility validated
- [ ] Mount points documented
- [ ] Deployment automated via IaC
- [ ] Deployment tested and validated

#### Story Points: 8  
#### Dependencies: None

---

### US-081: Deploy DR Region EKS Clusters
**As a** Cloud Infrastructure Architect  
**I want** EKS clusters deployed in DR region  
**So that** containerized workloads can run in DR region

#### Acceptance Criteria:
- **Given** primary region EKS clusters  
  **When** deploying DR infrastructure  
  **Then** equivalent EKS 1.32 clusters are deployed in DR region with private control planes
- **Given** DR region EKS deployment  
  **When** configuring node groups  
  **Then** node groups are configured to scale from minimal to production capacity
- **Given** EKS cluster deployment  
  **When** configuring networking  
  **Then** private subnets and security groups are configured
- **Given** EKS cluster deployment  
  **When** configuring add-ons  
  **Then** required add-ons are installed: ALB Controller, EBS CSI Driver, EFS CSI Driver
- **Given** EKS cluster deployment  
  **When** validating deployment  
  **Then** cluster is accessible and ready for workload deployment

#### Definition of Done:
- [ ] EKS 1.32 clusters deployed in DR region with private control planes
- [ ] Node groups configured with scaling capability
- [ ] Networking configured (private subnets, security groups)
- [ ] Required add-ons installed
- [ ] Cluster accessibility validated
- [ ] Deployment automated via IaC
- [ ] Deployment tested and validated

#### Story Points: 13  
#### Dependencies: None

---

### US-082: Deploy DR Region EFS File Systems
**As a** Cloud Infrastructure Architect  
**I want** EFS file systems deployed in DR region  
**So that** shared file storage is available for EKS workloads

#### Acceptance Criteria:
- **Given** primary region EFS file systems  
  **When** deploying DR infrastructure  
  **Then** equivalent EFS file systems are deployed in DR region
- **Given** DR region EFS deployment  
  **When** configuring mount targets  
  **Then** mount targets are created in DR region subnets
- **Given** EFS file systems  
  **When** configuring access  
  **Then** security groups allow access from EKS node groups
- **Given** EFS deployment  
  **When** validating deployment  
  **Then** file systems are accessible from EKS clusters

#### Definition of Done:
- [ ] EFS file systems deployed in DR region
- [ ] Mount targets configured
- [ ] Security groups configured
- [ ] Accessibility from EKS validated
- [ ] Deployment automated via IaC
- [ ] Deployment tested and validated

#### Story Points: 5  
#### Dependencies: US-081

---

### US-083: Deploy DR Region ECR Repositories
**As a** Cloud Infrastructure Architect  
**I want** ECR repositories deployed in DR region  
**So that** container images are available for EKS workloads

#### Acceptance Criteria:
- **Given** primary region ECR repositories  
  **When** deploying DR infrastructure  
  **Then** equivalent ECR repositories are created in DR region
- **Given** DR region ECR deployment  
  **When** configuring replication  
  **Then** cross-region replication is configured from primary to DR region
- **Given** ECR repositories  
  **When** configuring access  
  **Then** IAM policies allow EKS clusters to pull images
- **Given** ECR deployment  
  **When** validating deployment  
  **Then** repositories are accessible and replication is operational

#### Definition of Done:
- [ ] ECR repositories created in DR region
- [ ] Cross-region replication configured
- [ ] IAM policies configured
- [ ] Repository accessibility validated
- [ ] Replication operational
- [ ] Deployment automated via IaC
- [ ] Deployment tested and validated

#### Story Points: 5  
#### Dependencies: US-081

---

### US-084: Vend DR Accounts for DRS Scale
**As a** Cloud Infrastructure Architect  
**I want** multiple DR accounts vended to support DRS scale requirements  
**So that** 500-1500 servers can be protected within DRS service quotas

#### Acceptance Criteria:
- **Given** DRS service quotas (300 replicating servers per account, 500 servers in all jobs per account)  
  **When** planning for 500-1500 servers  
  **Then** multiple DR accounts are vended to distribute DRS load
- **Given** multiple DR accounts  
  **When** configuring account structure  
  **Then** accounts are organized by customer or environment for isolation
- **Given** DR account vending  
  **When** configuring cross-account access  
  **Then** orchestration account can assume roles in all DR accounts
- **Given** DR accounts  
  **When** validating deployment  
  **Then** DRS is initialized in each account and ready for source server registration

#### Definition of Done:
- [ ] DR account vending strategy documented based on DRS quotas
- [ ] Multiple DR accounts vended via LZA or Control Tower
- [ ] Account organization by customer/environment documented
- [ ] Cross-account IAM roles configured
- [ ] DRS initialized in each account
- [ ] Account structure validated
- [ ] Documentation includes account mapping and quota distribution

#### Story Points: 8  
#### Dependencies: US-009

---

## Acceptance Criteria Summary

### Definition of Ready Checklist
- [ ] User story follows INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable)
- [ ] Acceptance criteria are specific and testable with Given/When/Then format
- [ ] Dependencies are identified and prerequisite stories are complete or planned
- [ ] Story points estimated by team using planning poker
- [ ] Business value clearly articulated in story description
- [ ] Technical feasibility validated by architecture team

### Definition of Done Checklist
- [ ] All acceptance criteria met and validated
- [ ] Code review completed and approved by peer
- [ ] Unit tests written with >80% coverage
- [ ] Integration testing completed successfully
- [ ] Documentation updated (runbooks, architecture docs, API docs)
- [ ] Security review completed for security-sensitive changes
- [ ] Performance requirements met and validated
- [ ] CloudWatch monitoring and alarms configured
- [ ] Stakeholder demo completed and accepted

---

## Traceability to Requirements

### Functional Requirements Coverage
- FR-001 → US-001, US-002, US-003
- FR-002 → US-001, US-002
- FR-003 → US-003, US-010
- FR-004 → US-004, US-005, US-076
- FR-005 → US-004, US-006, US-007, US-077
- FR-006 → US-008
- FR-007 → US-009
- FR-008 → US-017, US-018, US-019, US-084
- FR-009 → US-020, US-021
- FR-010 → US-022, US-023
- FR-011 → US-024, US-025, US-026
- FR-012 → US-027, US-028
- FR-013 → US-029, US-030
- FR-014 → US-031, US-032, US-033
- FR-015 → US-034, US-035
- FR-016 → US-036
- FR-017 → US-038, US-039, US-040, US-081, US-082, US-083
- FR-018 → US-040
- FR-019 → US-042
- FR-020 → US-043, US-044, US-080
- FR-021 → US-045
- FR-022 → US-046, US-046A, US-047
- FR-023 → US-048
- FR-024 → US-049
- FR-025 → US-050, US-051, US-052
- FR-026 → US-053, US-054
- FR-027 → US-055, US-056
- FR-028 → US-057, US-058
- FR-029 → US-059
- FR-030 → US-060
- FR-031 → US-012
- FR-032 → US-063, US-064, US-065, US-066
- FR-033 → US-011

### Non-Functional Requirements Coverage
- NFR-001 (RTO) → US-017, US-013, US-027, US-031, US-059
- NFR-002 (RPO) → US-017, US-013, US-027, US-059
- NFR-003 (Response Time) → US-075, US-076, US-077
- NFR-004 (Orchestration Time) → US-075, US-076, US-077
- NFR-006 (Server Scale) → US-075, US-079, US-084
- NFR-007 (Multi-Tenant) → US-003, US-009, US-084
- NFR-008 (Regional Scale) → US-009, US-031, US-080, US-081, US-082, US-083
- NFR-010 (Uptime SLA) → All recovery stories
- NFR-011 (DR Reliability) → US-004, US-012, US-055
- NFR-014 (Authentication) → US-009, US-067
- NFR-015 (Encryption) → US-068, US-069
- NFR-016 (Network Security) → US-072, US-073
- NFR-017 (Secrets) → US-070
- NFR-018 (Audit Logging) → US-060
- NFR-022 (Monitoring) → US-057, US-058, US-061, US-062
- NFR-027 (Operational Simplicity) → US-008, US-063, US-064, US-065
- NFR-028 (Documentation) → US-063, US-064, US-065, US-066
- NFR-029 (Automation) → All orchestration stories
- NFR-032 (LZA Integration) → US-009, US-072, US-073, US-080, US-081, US-082, US-083, US-084
- NFR-035 (Test Coverage) → All stories (DoD requirement)
- NFR-036 (DR Testing) → US-050, US-053, US-054

---

## Success Metrics

### User Experience Metrics
- DR operation initiation time < 2 minutes (from CLI command to workflow start)
- Approval response time < 30 minutes (average time for approval decisions)
- Runbook clarity score > 4.5/5 (operations team feedback)

### Technical Performance Metrics
- Resource discovery time < 5 minutes for 1,000 servers
- Wave orchestration overhead < 2 minutes per wave
- Step Functions execution time < 10% of total RTO
- DRS recovery job success rate > 99%
- Database failover success rate > 99%

### Business Success Metrics
- Actual RTO < 4 hours (contractual requirement)
- Actual RPO < 30 minutes (contractual requirement)
- DR test success rate > 95% (bubble tests and Game Days)
- SLA penalty reduction > 90% (compared to pre-DR implementation)
- Operations team training completion < 2 days

---

---

## Update Summary (Post-Feedback Iteration 2)

**Changes from Iteration 1**:
- **Total Stories**: Increased from 75 to 84 stories (net +9 stories: +5 new infrastructure, -2 removed, +6 completed missing content)
- **Total Story Points**: Increased from 340 to 405 points (net +65 points)
- **Key Updates Based on Feedback**:
  - US-001: Changed to update existing tag documentation instead of creating new
  - US-002: Changed to use SCPs and tag policies instead of Config rules
  - US-003: Removed fallback logic, added validation for all resource types
  - US-004/US-005: Swapped order (orchestrator workflow before wave logic)
  - US-008: Added dr:x tag validation to parameter validation
  - US-009: Changed to deploy roles via LZA customizations-config.yaml
  - US-010: Made cache TTL configurable
  - US-013: Clarified "minimal or no storage" for pre-provisioned instances
  - US-027: Changed to Route 53 DNS failover for Valkey endpoint (from configuration update)
  - US-031-035: Added complete content (was missing)
  - US-039: Added ECR image build verification
  - US-051: Added DB server cleanup
  - US-055-056, US-063-066, US-069-073, US-077: Added complete content (was missing)
  - US-074: Removed (Config rules)
  - US-078: Removed (service limit monitoring)
- **New Infrastructure Deployment Stories**:
  - US-080: Deploy DR Region FSx ONTAP File Systems (8 points)
  - US-081: Deploy DR Region EKS Clusters (13 points)
  - US-082: Deploy DR Region EFS File Systems (5 points)
  - US-083: Deploy DR Region ECR Repositories (5 points)
  - US-084: Vend DR Accounts for DRS Scale (8 points)
- **Sprint Planning Updates**:
  - Extended from 6 sprints to 8 sprints (12 weeks to 16 weeks)
  - Added Sprint 1-2 focus on infrastructure deployment
  - Reorganized sprints to accommodate infrastructure and complete stories
  - Added Sprint 8 for additional components and security hardening

**Impact on Delivery**:
- MVP timeline extended to 16 weeks (8 sprints) due to infrastructure deployment
- Infrastructure deployment in early sprints enables parallel development
- Complete story content reduces ambiguity and implementation risk
- DRS multi-account strategy addresses service quota constraints

---

**Document Status**: Updated Post-Feedback Iteration 3 - Ready for Architecture Generation (Stage 3)

**Total Story Points**: 400 points across 83 user stories  
**Estimated Duration**: 16 weeks (8 sprints) for MVP, additional time for enhancements

**Key Changes in Iteration 3**:
- US-035: Changed to deploy WAF rules to both regions with CDK IaC
- US-071: Removed (CloudTrail already implemented in Landing Zone)
- US-072: Updated to note security groups should be created using CDK IaC

**Key Changes in Iteration 2**:
- Updated US-001 to update existing tag documentation instead of creating new
- Updated US-002 to use SCPs and tag policies instead of Config rules
- Updated US-003 to remove fallback logic and validate all resource types
- Swapped US-004 and US-005 order
- Updated US-008 to include dr:x tag validation
- Updated US-009 to deploy roles via LZA customizations-config.yaml
- Updated US-010 to make TTL configurable
- Updated US-013 to clarify "minimal or no storage"
- Updated US-027 to use Route 53 DNS failover for Valkey endpoint
- Added complete content for US-031 through US-035
- Updated US-039 to include ECR image build verification
- Updated US-051 to include DB server cleanup
- Added complete content for US-055, US-056, US-063-066, US-069-073, US-077
- Removed US-074 (Config rules) and US-078 (service limit monitoring)
- Added 5 new infrastructure deployment stories: US-080 through US-084
- Updated sprint planning to reflect 8 sprints with infrastructure deployment in Sprint 1-2
