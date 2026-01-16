# Reference Architecture Repositories

## AWS DRS Orchestration Reference Materials

**Version**: 1.0  
**Date**: January 16, 2026  
**Purpose**: Catalog of reference architecture repositories used during AWS DRS Orchestration development

---

## Overview

This document catalogs the reference architecture repositories that provided design patterns, implementation examples, and best practices for disaster recovery orchestration.

### Project Relationships

**This Repository** (AWS DRS Orchestration):
- **Current Repository**: https://github.com/johnjcousens/aws-elasticdrs-orchestrator
- **Based On**: AWS DRS Tools (Official AWS Sample)
- **Purpose**: DRS-specific orchestration with Protection Groups, Recovery Plans, and wave-based execution
- **Scope**: AWS Elastic Disaster Recovery (DRS) service automation

**Greater DR Orchestration System** (HRP-DR-Orchestration):
- **Based On**: DR Orchestration Artifacts (Internal AWS Reference)
- **Purpose**: Multi-service DR orchestration including DRS, EKS, SQL AG, and managed services
- **Scope**: Tag-driven DR orchestration for 1,000+ servers across 20+ customer environments
- **Integration**: This DRS Orchestration project would be one component within the greater system

---

## Repository Catalog

### 🎯 PRIMARY TEMPLATE FOR GREATER HRP-DR-ORCHESTRATION SYSTEM: DR Orchestration Artifacts (Internal AWS Reference)

**Repository**: git@ssh.gitlab.aws.dev:bdesika/dr-orchestration-artifacts.git  
**Type**: Internal AWS Professional Services Reference  
**Access**: AWS Internal GitLab  
**Status**: ⭐ **FOUNDATIONAL TEMPLATE FOR GREATER HRP-DR-ORCHESTRATION SYSTEM**

#### Description
Multi-region disaster recovery orchestrator that automates DR lifecycle phases between two AWS regions. **This repository serves as the foundational template for the greater HRP-DR-Orchestration system** documented in `archive/HealthEdge/HRP-DR-Orchestration/DESIGN-DOCS`. The HRP system encompasses tag-driven DR orchestration for 1,000+ servers across 20+ customer environments, including DRS, EKS, SQL AG, and managed services recovery.

**Relationship to This Repository**: This AWS DRS Orchestration project (https://github.com/johnjcousens/aws-elasticdrs-orchestrator) serves as the **DRS recovery component** that would be invoked by the greater HRP-DR-Orchestration system.

#### DR Lifecycle Phases

##### 1. Instantiate
- **Purpose**: Prewarm infrastructure in secondary region
- **Actions**: Deploy stacks, scale ECS/EKS clusters
- **Timing**: Before DR event

##### 2. Activate
- **Purpose**: Activate secondary region as primary
- **Actions**: Failover databases, switch DNS
- **Timing**: During DR event

##### 3. Cleanup
- **Purpose**: Remove resources from old primary region
- **Actions**: Delete stacks, clean up resources
- **Timing**: After old primary region recovers

##### 4. Replicate
- **Purpose**: Re-establish replication to old primary (now secondary)
- **Actions**: Configure replication, restore standby state
- **Timing**: After cleanup completes

#### Architecture Components
- **Orchestration**: AWS Step Functions with nested state machines
- **Execution**: Lambda functions for control logic
- **Configuration**: S3-based manifest files (JSON)
- **Approval**: SNS-based approval workflow
- **Monitoring**: CloudWatch dashboard for failure tracking
- **Cross-Account**: IAM roles for multi-account support

#### State Machine Hierarchy
1. **DR Orchestrator**: Top-level orchestration
2. **Lifecycle**: Phase-specific orchestration (Instantiate/Activate/Cleanup/Replicate)
3. **Module Factory**: Resource-specific operations

#### Manifest Structure
- **Product Manifest**: High-level DR plan
- **Application Manifest**: Resource-specific configuration
- **Layer-Based Execution**: Sequential processing with dependencies
- **Parameter Support**: CloudFormation exports, SSM parameters

#### Key Features
- **Approval Workflow**: Email-based approval before execution
- **Dependency Management**: Layer-based resource ordering
- **Multi-Application**: Support for multiple applications per product
- **Failure Tracking**: CloudWatch dashboard for troubleshooting
- **Flexible Configuration**: JSON-based manifest files

#### Influence on Greater HRP-DR-Orchestration System
This repository provided the foundational architecture for the greater DR orchestration system:

**Core Concepts for HRP System**:
- ✅ **Step Functions orchestration**: Multi-service recovery coordination
- ✅ **Lifecycle phases**: Instantiate → Activate → Cleanup → Replicate
- ✅ **Approval workflow**: Human-in-the-loop for critical operations
- ✅ **Manifest-based configuration**: Tag-driven resource discovery
- ✅ **Layer-based dependencies**: Wave-based execution across services
- ✅ **CloudWatch monitoring**: System-wide observability

**HRP System Architecture**:
- Tag-driven discovery using AWS Resource Explorer
- CLI-triggered automation via Step Functions
- Multi-service recovery modules: DRS, EKS DNS, SQL AG, Managed Services
- Pre-cached resource inventory for primary region failures
- Cross-account access patterns
- Performance targets: 4-hour RTO, 30-minute critical workload recovery

**Integration Point**: This AWS DRS Orchestration project implements the DRS recovery module that would be invoked by the greater HRP-DR-Orchestration system's Step Functions workflow.

---

### 🔧 COMPONENT TEMPLATE: AWS DRS Tools (Official AWS Sample)

**Repository**: https://github.com/aws-samples/drs-tools  
**Type**: Official AWS Sample Repository  
**License**: Apache 2.0  
**Status**: ⭐ **TEMPLATE FOR THIS DRS ORCHESTRATION COMPONENT**

#### Description
Collection of solutions and tools for AWS Elastic Disaster Recovery (DRS) service. **This repository served as the template for this specific DRS Orchestration component** (https://github.com/johnjcousens/aws-elasticdrs-orchestrator), which handles DRS-specific recovery operations within the greater HRP-DR-Orchestration system.

#### Key Components

##### DRS Plan Automation
- **Purpose**: Automated, sequential approach for DRS drills and recoveries
- **Features**:
  - React-based protected UI with Amazon Cognito authentication
  - Tag-based server organization in ordered waves
  - PreWave and PostWave automation using SSM Automation runbooks
  - Step Functions orchestration with DynamoDB data storage
  - Optional AWS WAF for IP-based access control
- **Architecture**: API Gateway → Lambda → Step Functions → DynamoDB
- **Use Case**: Multi-application recovery with dependency management and sequenced automation

##### DRS Configuration Synchronizer
- **Purpose**: Flexible, configuration-based synchronization of launch templates and replication settings
- **Features**:
  - Bulk configuration management across DRS servers
  - Server-specific overrides with default settings
  - Multi-account DRS deployment support
- **Use Case**: Standardizing DRS configurations across large deployments

##### DRS Synch EC2 Tags and Instance Type
- **Purpose**: Synchronize EC2 instance tags and types to DRS source servers
- **Features**:
  - Tag replication from EC2 to DRS source servers
  - Launch template updates to match EC2 instance types
  - Single and multi-account support
- **Use Case**: Maintaining consistency between EC2 instances and DRS source servers

##### DRS Template Manager
- **Purpose**: Batch management of DRS launch templates
- **Features**:
  - Single baseline template for multiple source servers
  - Tag-based template application
  - Batch editing capabilities
- **Use Case**: Managing launch templates at scale

##### DRS Observability
- **Purpose**: Logging and monitoring for DRS deployments
- **Features**:
  - CloudWatch dashboards
  - CloudWatch logging configuration
  - Health monitoring
- **Use Case**: Establishing observability for DRS deployments

#### Direct Influence on This AWS DRS Orchestration Project

**Core Concepts Adopted**:
- ✅ **Wave-based recovery pattern**: Became our Protection Groups and Recovery Plans design
- ✅ **Step Functions orchestration**: Direct implementation for execution workflow
- ✅ **Tag-based organization**: Implemented as tag-based server selection feature
- ✅ **React + CloudScape UI**: Adopted for AWS Console-consistent user experience
- ✅ **PreWave/PostWave automation**: Evolved into pause-before-wave functionality
- ✅ **DynamoDB state management**: Used for Protection Groups, Recovery Plans, and Execution History
- ✅ **API Gateway + Lambda pattern**: Core serverless API architecture
- ✅ **Cognito authentication**: User authentication and RBAC integration

**Architectural Patterns Inherited**:
- Multi-wave execution with dependencies
- Real-time execution monitoring
- CloudWatch observability
- Multi-account support with cross-account roles
- Configuration-based server management

**Current Implementation** (https://github.com/johnjcousens/aws-elasticdrs-orchestrator):
- 7 Lambda functions for DRS orchestration
- 15+ CloudFormation nested stacks
- React 19 + CloudScape 3.0 frontend
- 47+ REST API endpoints
- Protection Groups and Recovery Plans data model
- Wave-based execution with pause/resume capability

---

## Supporting Reference Repositories

### 2. DRS Settings Tool (Official AWS Labs)

**Repository**: https://github.com/awslabs/DRS-Settings-Tool  
**Type**: Official AWS Labs Tool  
**License**: Apache 2.0

#### Description
Python-based tool for bulk management of DRS source server settings. Enables changing settings for multiple servers simultaneously using CSV files.

#### Key Features
- **Bulk Settings Management**: Edit multiple DRS source servers via CSV
- **Settings Coverage**:
  - Launch configuration (right sizing, instance type, AMI, network settings)
  - Replication configuration (bandwidth throttling, staging disk settings)
  - Target instance settings (tags, IAM roles, disk encryption)
- **Multi-Account Support**: Extended account configurations with cross-account roles
- **Validation**: Comparison of current vs. desired settings to minimize API calls

#### Technical Implementation
- **Language**: Python 3.12+
- **AWS Services**: DRS, EC2, IAM, KMS
- **Authentication**: AWS credentials file with profile-based configuration
- **Output**: CSV files for editing, log files for troubleshooting

#### Relevance to AWS DRS Orchestration
- **Bulk operations pattern**: Informed our multi-server management approach
- **CSV-based configuration**: Validated our configuration export/import feature design
- **Settings validation**: Influenced our conflict detection and validation logic
- **Multi-account patterns**: Guided our cross-account role implementation

---

### 3. Cloud Migration Factory on AWS (Official AWS Solution)

**Repository**: https://github.com/aws-solutions/cloud-migration-factory-on-aws  
**Type**: Official AWS Solutions Implementation  
**Version**: 4.5.1  
**License**: Apache 2.0

#### Description
AWS Solutions Implementation for migrating large numbers of servers using CloudEndure Migration (predecessor to DRS). Automates manual, time-consuming migration tasks at enterprise scale.

#### Key Features
- **Automated Migration Workflows**: Prerequisite checks, software installation/uninstallation
- **Web-Based UI**: React frontend with CloudFront, API Gateway, Lambda backend
- **Data Management**: DynamoDB for migration tracking, Cognito for authentication
- **Automation Framework**: Remote automation for source and target machines
- **Credential Management**: Secure credential storage and management
- **Migration Tracking**: Progress monitoring and reporting
- **Replatform Support**: Migration strategy flexibility

#### Architecture Components
- **Frontend**: React + CloudFront + S3
- **Backend**: API Gateway + Lambda + DynamoDB
- **Authentication**: Amazon Cognito
- **Automation**: SSM, Lambda
- **Optional**: AWS WAF for security

#### Technical Stack
- **Frontend**: React, TypeScript, Jest
- **Backend**: Python, Lambda Layers
- **IaC**: CloudFormation nested stacks
- **CI/CD**: CodePipeline, CodeBuild
- **Testing**: Jest (frontend), Python unittest (backend)
- **Security**: cfn-nag validation, SonarQube integration

#### Relevance to AWS DRS Orchestration
- **React + CloudScape UI pattern**: Validated our frontend technology choice
- **Nested CloudFormation stacks**: Informed our 15+ stack architecture
- **Cognito authentication**: Guided our authentication implementation
- **API Gateway + Lambda pattern**: Validated our serverless API design
- **Migration tracking in DynamoDB**: Influenced our execution history design
- **Automation framework**: Inspired our orchestration approach

---

### 4. DR Factory (Internal Migration Factory Customization)

**Repository**: git@ssh.gitlab.aws.dev:wwco-proserve-gcci/rehost/competencies/migrations/cmf-customisation-for-partners-testings.git  
**Type**: Internal AWS Professional Services Customization  
**Access**: AWS Internal GitLab

#### Description
Customization of Cloud Migration Factory for partner testing and DR scenarios. Provides scripted automation for DRS operations.

#### Key Components

##### DR Factory Scripts (Version 4.0.1)
1. **0-DRS-Prerequisite-Check**: Validates prerequisites before DRS operations
2. **1-Install-DRS-Agent**: Automates DRS agent installation
3. **2-DRS_Copy_Post_Launch_Scripts**: Manages post-launch automation
4. **3-verify-replication-status**: Monitors replication health
5. **4-Initiate-Drill-Failover**: Triggers drill or failover operations

#### Supporting Materials
- **DR Factory Guidance**: Implementation documentation
- **IAM Policy**: Required permissions for DRS operations
- **Sample Intake Form**: Template for DR planning

#### Relevance to AWS DRS Orchestration
- **Scripted automation pattern**: Validated our Lambda-based automation approach
- **Prerequisite checking**: Informed our validation logic
- **Replication monitoring**: Guided our DRS status polling design
- **Drill/failover workflows**: Influenced our execution type handling

---

## Key Patterns and Learnings

### Architecture Patterns
1. **Step Functions Orchestration**: Validated for complex, multi-step workflows
2. **Nested CloudFormation Stacks**: Effective for large-scale infrastructure
3. **React + CloudScape UI**: AWS Console-consistent user experience
4. **API Gateway + Lambda**: Serverless API pattern
5. **DynamoDB for State**: Execution tracking and configuration storage

### Security Patterns
1. **Cognito Authentication**: User authentication and authorization
2. **IAM Cross-Account Roles**: Multi-account access patterns
3. **AWS WAF**: IP-based access control
4. **Secrets Manager**: Credential management
5. **cfn-nag Validation**: Infrastructure security scanning

### Automation Patterns
1. **Tag-Based Organization**: Server grouping and selection
2. **Wave-Based Execution**: Sequential recovery with dependencies
3. **Approval Workflows**: Human-in-the-loop for critical operations
4. **Manifest-Based Configuration**: Declarative infrastructure management
5. **PreWave/PostWave Actions**: Extensible automation framework

### Operational Patterns
1. **CloudWatch Monitoring**: Execution tracking and troubleshooting
2. **S3-Based Artifacts**: Configuration and template storage
3. **CodePipeline CI/CD**: Automated deployment pipelines
4. **Multi-Region Support**: Primary/secondary region patterns
5. **Failure Recovery**: Rollback and retry mechanisms

---

## Implementation Influence

### Direct Implementations
- **Wave-based recovery**: From drs-tools DRS Plan Automation
- **Step Functions orchestration**: From dr-orchestration-artifacts
- **React + CloudScape UI**: From cloud-migration-factory-on-aws
- **Nested CloudFormation**: From dr-automation and cloud-migration-factory
- **Tag-based selection**: From drs-tools and drs-synch-ec2-tags

### Adapted Patterns
- **Pause-before-wave**: Adapted from approval workflow patterns
- **Protection Groups**: Simplified from application manifest patterns
- **Execution tracking**: Enhanced from migration tracking patterns
- **Configuration export/import**: Inspired by DRS Settings Tool CSV approach
- **Multi-account support**: Adapted from multiple reference implementations

### Enhanced Features
- **Real-time polling**: Enhanced beyond reference implementations
- **CloudScape Design System**: Full AWS Console consistency
- **RBAC integration**: Enterprise-grade permission management
- **Account context switching**: Multi-account user experience
- **Execution history**: Comprehensive audit trail

---

## Related Documentation

- [Product Requirements Document](../requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md)
- [Software Requirements Specification](../requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md)
- [Architecture Documentation](../architecture/ARCHITECTURE.md)
- [Project Essentials](.kiro/steering/project-essentials.md)

---

## Maintenance Notes

**Last Updated**: January 16, 2026  
**Maintained By**: AWS DRS Orchestration Team  
**Update Frequency**: As needed when new reference materials are added
