# AWS DRS Orchestration Solution

Enterprise-grade disaster recovery orchestration for AWS Elastic Disaster Recovery (DRS) with wave-based execution, dependency management, and automated health checks.

[![AWS](https://img.shields.io/badge/AWS-DRS-FF9900?logo=amazonaws)](https://aws.amazon.com/disaster-recovery/)
[![CloudFormation](https://img.shields.io/badge/IaC-CloudFormation-232F3E?logo=amazonaws)](cfn/)
[![React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?logo=react)](frontend/)
[![Python](https://img.shields.io/badge/Backend-Python%203.12-3776AB?logo=python)](lambda/)
[![GitHub](https://img.shields.io/badge/Repository-GitHub-181717?logo=github)](https://github.com/johnjcousens/aws-elasticdrs-orchestrator)
[![Release](https://img.shields.io/badge/Release-v1.4.6%20RBAC%20Complete-green)](https://github.com/johnjcousens/aws-elasticdrs-orchestrator/releases/tag/v1.4.6)

## 🚀 **Latest Release: v1.4.6 - RBAC Complete Coverage**

**Latest Version**: v1.4.6 (January 7, 2026) - Complete RBAC coverage for all 47+ API endpoints with 308 automated tests.

**Previous Version**: v1.4.5 (January 7, 2026) - Comprehensive RBAC test suite expansion with path normalization bug fix.

**[View Complete Release Notes →](CHANGELOG.md#146---january-7-2026)**

## Overview

AWS DRS Orchestration enables organizations to orchestrate complex multi-tier application recovery with wave-based execution, dependency management, and automated health checks using AWS-native serverless services.

### Key Capabilities

- **Cost-Effective**: $12-40/month operational cost with pay-per-use serverless pricing
- **Unlimited Waves**: Flexible wave-based orchestration with no artificial constraints
- **Platform Agnostic**: Supports any source platform (physical servers, cloud instances, virtual machines)
- **Sub-Second RPO**: Leverages AWS DRS continuous replication capabilities
- **Fully Serverless**: No infrastructure to manage, scales automatically

## Critical Architectural Solutions

The solution addresses three fundamental challenges in enterprise disaster recovery orchestration through innovative AWS-native implementations:

### 🌊 **Wave-Based Orchestration with Step Functions**

**The Challenge**: Enterprise applications require coordinated recovery across multiple tiers (database → application → web) with manual validation points and dependency management.

**Our Solution**: Step Functions state machine with `waitForTaskToken` callback pattern enables sophisticated orchestration:

```python
# Step Functions orchestration with pause/resume capability
{
  "Type": "Task",
  "Resource": "arn:aws:states:::lambda:invoke.waitForTaskToken",
  "Parameters": {
    "FunctionName": "orchestration-stepfunctions",
    "Payload": {
      "taskToken.$": "$$.Task.Token",
      "executionId.$": "$.executionId",
      "waveNumber.$": "$.currentWave"
    }
  }
}
```

**Why Critical**:
- **Manual Validation**: Pause execution before critical waves for human approval
- **Dependency Management**: Waves only start after dependencies complete successfully
- **Long-Running Operations**: Task tokens support up to 1-year execution timeouts
- **Real-Time Control**: Resume, cancel, or terminate operations at any point
- **Audit Trail**: Complete execution history with wave-by-wave progress tracking

### 🏷️ **Dynamic Tag Synchronization**

**The Challenge**: DRS source servers lose EC2 tags during replication, breaking tag-based protection group filtering and recovery automation.

**Our Solution**: EventBridge-scheduled tag synchronization with multi-layer security validation:

```python
# Automated tag sync with security validation
def sync_tags_across_regions(account_id: str) -> dict:
    """Sync EC2 tags to DRS source servers across all regions."""
    results = {}
    for region in DRS_SUPPORTED_REGIONS:
        # Get EC2 instances and their tags
        ec2_tags = get_ec2_instance_tags(region, account_id)
        
        # Get corresponding DRS source servers
        drs_servers = get_drs_source_servers(region, account_id)
        
        # Sync tags with conflict resolution
        for server in drs_servers:
            if server['sourceServerID'] in ec2_tags:
                sync_server_tags(server, ec2_tags[server['sourceServerID']])
    
    return results
```

**Why Critical**:
- **Dynamic Server Selection**: Protection groups automatically include/exclude servers based on current tags
- **Operational Flexibility**: Change server assignments without modifying recovery plans
- **Multi-Region Support**: Synchronizes across all 30 AWS DRS regions automatically
- **Security Validation**: EventBridge rules include IP validation and request structure validation
- **Scheduled Automation**: Configurable intervals (15min to 24hr) with manual override capability

### ⚙️ **Advanced DRS Launch Settings Management**

**The Challenge**: DRS launch settings (instance types, subnets, security groups) must be configured per server but managed at scale across protection groups.

**Our Solution**: Hierarchical launch configuration with inheritance and override patterns:

```python
# Protection Group launch configuration inheritance
class LaunchConfigManager:
    def resolve_launch_config(self, server_id: str, protection_group: dict) -> dict:
        """Resolve launch configuration with inheritance hierarchy."""
        config = {}
        
        # 1. Start with DRS service defaults
        config.update(self.get_drs_defaults())
        
        # 2. Apply Protection Group settings
        if protection_group.get('launchConfig'):
            config.update(protection_group['launchConfig'])
        
        # 3. Apply server-specific overrides
        server_config = self.get_server_launch_config(server_id)
        if server_config:
            config.update(server_config)
        
        return self.validate_launch_config(config)
```

**Why Critical**:
- **Consistent Recovery Environment**: Ensures servers launch with appropriate network and security settings
- **Right-Sizing**: Automatic instance type selection based on source server characteristics
- **Network Isolation**: Configurable subnet and security group assignments for recovery VPCs
- **Compliance**: Maintains security policies and compliance requirements during recovery
- **Cost Optimization**: Prevents over-provisioning during drill operations

### 🔄 **Protection Groups & Recovery Plans Architecture**

**Our Implementation**: Two-tier abstraction that separates server grouping from recovery orchestration:

**Protection Groups** (Server Organization):
- **Tag-Based Selection**: Servers automatically included based on tag criteria
- **Explicit Selection**: Manual server assignment for precise control
- **Conflict Detection**: Prevents servers from being assigned to multiple groups
- **Launch Configuration**: Inherited settings applied to all group servers

**Recovery Plans** (Orchestration Logic):
- **Multi-Wave Sequences**: Unlimited waves with dependency management
- **Multi-Protection-Group Waves**: Single wave can include multiple protection groups
- **Pause Points**: Manual validation between waves
- **Execution Types**: Drill vs Recovery mode with different behaviors

```python
# Recovery plan execution with wave dependencies
class RecoveryPlanExecutor:
    def execute_wave(self, wave: dict, execution_context: dict):
        """Execute a recovery wave with dependency validation."""
        # Validate wave dependencies are complete
        self.validate_wave_dependencies(wave, execution_context)
        
        # Check for pause requirement
        if wave.get('pauseBeforeWave') and wave['waveNumber'] > 0:
            return self.pause_for_manual_validation(wave, execution_context)
        
        # Resolve servers from multiple protection groups
        servers = self.resolve_wave_servers(wave['protectionGroupIds'])
        
        # Execute DRS recovery with parallel launch + delays
        return self.launch_servers_with_delays(servers, execution_context)
```

**Why This Architecture is Critical**:
- **Separation of Concerns**: Server grouping logic separate from orchestration logic
- **Reusability**: Protection groups can be used across multiple recovery plans
- **Flexibility**: Tag-based groups automatically adapt to infrastructure changes
- **Scalability**: Supports enterprise environments with hundreds of servers
- **Maintainability**: Changes to server assignments don't require recovery plan updates

## Key Features

### Wave-Based Orchestration Engine
- **Step Functions Integration**: `waitForTaskToken` pattern enables pause/resume with up to 1-year timeouts
- **Dependency Management**: Waves execute only after dependencies complete successfully
- **Manual Validation Points**: Pause before critical waves for human approval
- **Real-Time Control**: Resume, cancel, or terminate operations during execution
- **Parallel Execution**: Servers within waves launch in parallel with DRS-safe 15-second delays

### Dynamic Tag Synchronization
- **EventBridge Scheduling**: Automated EC2 → DRS tag sync with configurable intervals (15min-24hr)
- **Multi-Region Support**: Synchronizes across all 30 AWS DRS regions automatically
- **Security Validation**: Multi-layer EventBridge security with IP and request validation
- **Manual Override**: Immediate sync capability regardless of schedule settings
- **Conflict Resolution**: Handles tag conflicts and server state changes gracefully

### Advanced DRS Launch Settings
- **Hierarchical Configuration**: Protection Group → Server-specific override inheritance
- **Right-Sizing**: Automatic instance type selection based on source characteristics
- **Network Isolation**: Configurable subnet and security group assignments
- **Compliance Enforcement**: Maintains security policies during recovery operations
- **Cost Optimization**: Prevents over-provisioning during drill operations

### Protection Groups & Recovery Plans
- **Tag-Based Selection**: Servers automatically included/excluded based on current tags
- **Multi-Protection-Group Waves**: Single wave can orchestrate multiple protection groups
- **Conflict Detection**: Prevents servers from being assigned to multiple groups globally
- **Launch Configuration Inheritance**: Group-level settings applied to all member servers
- **Dynamic Server Resolution**: Server lists resolved at execution time, not plan creation

### Comprehensive REST API
- **47+ API Endpoints**: Complete REST API across 12 categories with RBAC security
- **Cross-Account Operations**: Manage DRS across multiple AWS accounts
- **Direct Lambda Invocation**: Bypass API Gateway for AWS-native automation
- **Configuration Export/Import**: Complete backup and restore capabilities

### Execution Monitoring
- **Real-Time Dashboard**: Live execution progress with auto-refresh
- **Enhanced History Management**: Selective deletion and comprehensive filtering
- **Instance Termination**: Clean up recovery instances after testing
- **CloudWatch Integration**: Deep-link to logs for troubleshooting

## Architecture

![AWS DRS Orchestration Architecture](docs/architecture/AWS-DRS-Orchestration-Architecture.png)

*Updated architecture diagrams available in [docs/architecture/](docs/architecture/) reflecting current 6-nested-stack API Gateway architecture with 42+ endpoints*

*[View/Edit Source Diagram](docs/architecture/AWS-DRS-Orchestration-Architecture.drawio)*

The solution follows a serverless, event-driven architecture with clear separation between frontend, API, compute, data, and DRS integration layers. Users access the React frontend via CloudFront, authenticate through Cognito, and interact with the REST API backed by Lambda functions. The API Gateway is implemented as 6 nested CloudFormation stacks for maintainability and CloudFormation size compliance. 

**Step Functions orchestrates wave-based recovery execution** using the `waitForTaskToken` callback pattern, enabling pause/resume functionality with task tokens that can persist up to 1 year. **EventBridge schedules automated tag synchronization** across all DRS regions, ensuring protection groups dynamically adapt to infrastructure changes. **DRS launch settings are managed hierarchically** with Protection Group defaults and server-specific overrides, ensuring consistent recovery environments while maintaining operational flexibility.

### Technology Stack

| Layer      | Technology                                               |
| ---------- | -------------------------------------------------------- |
| Frontend   | React 19.1, TypeScript 5.9, CloudScape Design System 3.0 |
| API        | Amazon API Gateway (REST), Amazon Cognito                |
| Compute    | AWS Lambda (Python 3.12), AWS Step Functions             |
| Database   | Amazon DynamoDB (4 tables with GSI)                      |
| Hosting    | Amazon S3, Amazon CloudFront                             |
| DR Service | AWS Elastic Disaster Recovery (DRS)                      |

## Python Virtual Environment

The repository includes a pre-configured Python 3.12.11 virtual environment (`venv/`) for Lambda development and testing:

### Environment Details
- **Python Version**: 3.12.11 (matches AWS Lambda runtime)
- **Package Count**: 76+ packages installed
- **Testing Framework**: pytest, moto, hypothesis for comprehensive testing
- **AWS Integration**: boto3, crhelper for Lambda development
- **Status**: ✅ Up-to-date with deployed codebase

### Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run Lambda unit tests
cd tests/python
pytest unit/ -v

# Run integration tests with AWS mocking
pytest integration/ -v

# Generate coverage report
pytest --cov=lambda

# Deactivate when done
deactivate
```

### Key Packages
- **Testing**: pytest 7.4.3, moto 4.2.9, hypothesis 6.92.1
- **AWS SDK**: boto3 1.34.0, botocore 1.34.0
- **Lambda Helper**: crhelper 2.0.11
- **Utilities**: freezegun 1.4.0, python-dateutil 2.8.2

The virtual environment is maintained to match the exact versions used in production Lambda functions and testing infrastructure.

## AWS DRS Regional Availability

The solution orchestrates disaster recovery in all **30 AWS regions** where Elastic Disaster Recovery (DRS) is available:

| Region Group                   | Count | Regions                                                                                                    |
| ------------------------------ | ----- | ---------------------------------------------------------------------------------------------------------- |
| **Americas**             | 6     | US East (N. Virginia, Ohio), US West (Oregon, N. California), Canada (Central), South America (São Paulo) |
| **Europe**               | 8     | Ireland, London, Frankfurt, Paris, Stockholm, Milan, Spain, Zurich                                         |
| **Asia Pacific**         | 10    | Tokyo, Seoul, Osaka, Singapore, Sydney, Mumbai, Hyderabad, Jakarta, Melbourne, Hong Kong                   |
| **Middle East & Africa** | 4     | Bahrain, UAE, Cape Town, Tel Aviv                                                                          |
| **GovCloud**             | 2     | US-East, US-West                                                                                           |

*Regional availability determined by AWS DRS service. As AWS expands DRS, the solution automatically supports new regions.*

## Quick Start

### Prerequisites

- AWS Account with DRS configured and source servers replicating
- AWS CLI v2 configured with appropriate permissions
- S3 bucket for deployment artifacts

### Deploy with CloudFormation

```bash
# Deploy the complete solution
aws cloudformation deploy \
  --template-url https://your-bucket.s3.us-east-1.amazonaws.com/cfn/master-template.yaml \
  --stack-name aws-elasticdrs-orchestrator \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=prod \
    SourceBucket=your-bucket \
    AdminEmail=admin@yourcompany.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Deployment takes approximately 20-30 minutes and provides:
- **Complete REST API** with 47+ endpoints across 12 categories
- **Role-Based Access Control** with 5 granular roles
- **Cross-Account Operations** for enterprise environments
- **Tag-Based Server Selection** with automated synchronization
- **Wave-Based Execution** with pause/resume capabilities

### Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator \
  --query 'Stacks[0].Outputs' \
  --output table
```

| Output           | Description              |
| ---------------- | ------------------------ |
| CloudFrontURL    | Frontend application URL |
| ApiEndpoint      | REST API endpoint        |
| UserPoolId       | Cognito User Pool ID     |
| UserPoolClientId | Cognito App Client ID    |

### Create Admin User

```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name aws-elasticdrs-orchestrator \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --user-attributes Name=email,Value=admin@yourcompany.com Name=email_verified,Value=true \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@yourcompany.com \
  --password "YourSecurePassword123!" \
  --permanent
```

## Usage Guide

### Creating a Protection Group

1. Navigate to **Protection Groups** in the sidebar
2. Click **Create Protection Group**
3. Enter a unique name and select the AWS region
4. Select source servers from the discovery list (green = available, red = assigned)
5. Click **Create**

### Creating a Recovery Plan

1. Navigate to **Recovery Plans** in the sidebar
2. Click **Create Recovery Plan**
3. Enter plan name and configure waves:

| Wave | Tier        | Protection Groups        | Depends On |
| ---- | ----------- | ------------------------ | ---------- |
| 1    | Database    | DB-Primary, DB-Secondary | -          |
| 2    | Application | App-Servers              | Wave 1     |
| 3    | Web         | Web-Servers              | Wave 2     |

4. Configure optional pre/post-wave automation
5. Click **Create**

### Executing a Recovery

1. Navigate to **Recovery Plans**
2. Select a plan and click **Execute**
3. Choose execution type:
   - **Drill**: Test recovery without production impact
   - **Recovery**: Full disaster recovery execution
4. Monitor progress in **Executions** page
5. **Control execution**:
   - **Pause**: Stop between waves for validation
   - **Resume**: Continue paused execution
   - **Cancel**: Stop execution and cleanup
   - **Terminate Instances**: Remove recovery instances after testing

## Infrastructure

### CloudFormation Stacks

The solution uses a modular nested stack architecture for maintainability:

| Stack                         | Purpose             | Key Resources                     |
| ----------------------------- | ------------------- | --------------------------------- |
| `master-template.yaml`      | Root orchestrator   | Parameter propagation, outputs    |
| `database-stack.yaml`       | Data persistence    | 4 DynamoDB tables with encryption |
| `lambda-stack.yaml`         | Compute layer       | 7 Lambda functions, IAM roles     |
| `api-auth-stack.yaml`       | Authentication      | Cognito User Pool, Identity Pool, SNS |
| `api-gateway-core-stack.yaml` | API Gateway Core   | REST API, authorizer, validator   |
| `api-gateway-resources-stack.yaml` | API Resources | All 35+ API path definitions      |
| `api-gateway-core-methods-stack.yaml` | Core Methods | Health, User, Protection Groups, Recovery Plans |
| `api-gateway-operations-methods-stack.yaml` | Operations Methods | All Execution endpoints |
| `api-gateway-infrastructure-methods-stack.yaml` | Infrastructure Methods | DRS, EC2, Config, Target Accounts |
| `api-gateway-deployment-stack.yaml` | API Deployment | Deployment orchestrator and stage |
| `step-functions-stack.yaml` | Orchestration       | Step Functions state machine      |
| `eventbridge-stack.yaml`    | Event scheduling    | EventBridge rules for polling     |
| `security-stack.yaml`       | Security (optional) | WAF, CloudTrail                   |
| `frontend-stack.yaml`       | Frontend hosting    | S3, CloudFront                    |
| `cross-account-role-stack.yaml` | Multi-account (optional) | Cross-account IAM roles |

### DynamoDB Tables

| Table                       | Purpose             | Key Schema                            | Critical Data |
| --------------------------- | ------------------- | ------------------------------------- | ------------- |
| `protection-groups-{env}` | Server groupings    | `GroupId` (PK)                      | Tag-based selection criteria, launch configurations |
| `recovery-plans-{env}`    | Wave configurations | `PlanId` (PK)                       | Multi-wave sequences, dependencies, pause points |
| `execution-history-{env}` | Audit trail         | `ExecutionId` (PK), `PlanId` (SK) | Step Functions tokens, wave progress, server states |
| `target-accounts-{env}`   | Multi-account management | `AccountId` (PK), StatusIndex GSI | Cross-account role ARNs, validation status |

## Cost Estimate

| Component       | Monthly Cost (Est.)    |
| --------------- | ---------------------- |
| Lambda          | $1-5                   |
| API Gateway     | $3-10                  |
| DynamoDB        | $1-5                   |
| CloudFront      | $1-5                   |
| S3              | <$1                    |
| Step Functions  | $1-5                   |
| Cognito         | Free tier              |
| **Total** | **$12-40/month** |

*Costs vary based on usage. DRS replication costs are separate and depend on protected server count.*

## Security & RBAC

### Role-Based Access Control
The solution implements comprehensive RBAC with 5 granular DRS-specific roles designed for disaster recovery teams:

| Role | Description | Key Permissions |
|------|-------------|-----------------|
| **DRSOrchestrationAdmin** | Full administrative access | All operations including account deletion, configuration export/import, instance termination |
| **DRSRecoveryManager** | Recovery operations lead | Execute plans, terminate instances, manage configuration, register accounts (no account deletion) |
| **DRSPlanManager** | DR planning focus | Create/modify/delete protection groups & recovery plans, execute recovery (no instance termination) |
| **DRSOperator** | On-call operations | Execute/pause/resume recovery, modify existing plans (no create/delete, no instance termination) |
| **DRSReadOnly** | Audit and monitoring | View-only access to all resources for compliance officers |

### Cognito Group Mapping
Users are assigned roles via AWS Cognito Groups. The following group names are supported:

**Primary DRS Roles (Recommended):**
- `DRSOrchestrationAdmin` - Full administrative access
- `DRSRecoveryManager` - Recovery operations and configuration
- `DRSPlanManager` - Plan and protection group management
- `DRSOperator` - Execution operations only
- `DRSReadOnly` - View-only access

**Legacy Group Names (Backward Compatible):**
- `DRS-Administrator` → DRSOrchestrationAdmin
- `DRS-Infrastructure-Admin` → DRSRecoveryManager
- `DRS-Recovery-Plan-Manager` → DRSPlanManager
- `DRS-Operator` → DRSOperator
- `DRS-Read-Only` → DRSReadOnly

### Permission Matrix

| Permission | Admin | Recovery Mgr | Plan Mgr | Operator | ReadOnly |
|------------|:-----:|:------------:|:--------:|:--------:|:--------:|
| **Account Management** |
| Register Accounts | ✅ | ✅ | ❌ | ❌ | ❌ |
| Delete Accounts | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modify Accounts | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Accounts | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Recovery Operations** |
| Start Recovery | ✅ | ✅ | ✅ | ✅ | ❌ |
| Stop Recovery | ✅ | ✅ | ✅ | ✅ | ❌ |
| Terminate Instances | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Executions | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Protection Groups** |
| Create Groups | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delete Groups | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modify Groups | ✅ | ✅ | ✅ | ✅ | ❌ |
| View Groups | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Recovery Plans** |
| Create Plans | ✅ | ✅ | ✅ | ❌ | ❌ |
| Delete Plans | ✅ | ✅ | ✅ | ❌ | ❌ |
| Modify Plans | ✅ | ✅ | ✅ | ✅ | ❌ |
| View Plans | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Configuration** |
| Export Configuration | ✅ | ✅ | ❌ | ❌ | ❌ |
| Import Configuration | ✅ | ✅ | ❌ | ❌ | ❌ |

### Security Features
- **Encryption**: All data encrypted at rest (DynamoDB, S3) and in transit (HTTPS)
- **Authentication**: Cognito JWT token-based authentication with 45-minute sessions
- **Authorization**: API-level RBAC enforcement - all 47+ endpoints protected with granular permissions
- **Audit Trails**: Complete user action logging with role context
- **Test Coverage**: 308 automated tests including comprehensive RBAC enforcement tests
- **100% API Coverage**: Every API endpoint has RBAC permission mapping and enforcement

## Documentation

### Essential Guides
- [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) - Complete REST API documentation (47+ endpoints)
- [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) - CLI, SSM, Step Functions integration
- [DRS Execution Walkthrough](docs/guides/DRS_EXECUTION_WALKTHROUGH.md) - Complete drill and recovery procedures
- [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) - Common issues and debugging
- [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) - Complete deployment procedures
- [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) - Development, testing, and CI/CD workflows

### Deployment Guides
- [Fresh Deployment Guide](docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md) - Complete fresh environment setup
- [GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md) - Complete setup, usage, and troubleshooting guide for GitHub Actions CI/CD

### Development Guides
- [Developer Onboarding Checklist](docs/guides/development/developer-onboarding-checklist.md) - New developer setup
- [Python Coding Standards](docs/guides/development/python-coding-standards.md) - PEP 8 compliance and quality standards
- [PyCharm Setup Guide](docs/guides/development/pycharm-setup.md) - IDE configuration for development
- [IDE Integration Testing](docs/guides/development/ide-integration-testing.md) - Testing IDE configurations
- [IDE Troubleshooting FAQ](docs/guides/development/ide-troubleshooting-faq.md) - Common IDE issues and solutions

### Troubleshooting Guides
- [Deployment Troubleshooting](docs/guides/troubleshooting/DEPLOYMENT_TROUBLESHOOTING_GUIDE.md) - Deployment issues and solutions
- [DRS Execution Troubleshooting](docs/guides/troubleshooting/DRS_EXECUTION_TROUBLESHOOTING_GUIDE.md) - Recovery execution debugging
- [DRS Service Limits Testing](docs/guides/troubleshooting/DRS_SERVICE_LIMITS_TESTING.md) - Service limits and capacity planning

### Requirements & Architecture
- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) - Complete PRD v3.0
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Technical specifications v3.0
- [UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md) - User interface design patterns v3.0
- [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) - System architecture v3.0
- [Enterprise DR Orchestration Platform PRD](docs/enterprise-prd/README.md) - Multi-technology DR orchestration platform requirements (modular docs)

### Implementation Features
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md) - Multi-account DRS operations
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md) - Advanced server management
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md) - Workflow automation patterns

### Reference Documentation
- [DRS IAM and Permissions Reference](docs/reference/DRS_IAM_AND_PERMISSIONS_REFERENCE.md) - Complete IAM requirements
- [DRS Service Limits and Capabilities](docs/reference/DRS_SERVICE_LIMITS_AND_CAPABILITIES.md) - Service constraints and planning
- [DRS Cross-Account Reference](docs/reference/DRS_CROSS_ACCOUNT_REFERENCE.md) - Multi-account configuration

*All documentation updated to v3.0 (January 8, 2026) with complete requirements alignment.*

## Future Enhancements

### Enhancement Roadmap

📋 **[Complete Enhancement Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md)** - Comprehensive roadmap based on AWS DRS Plan Automation analysis with detailed implementation plans for 5 key enhancements.

### Planned Features

| Priority | Feature | Effort | Status |
|----------|---------|--------|--------|
| 1 | **SSM Automation Integration** | 4w | 📋 [Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md#1-ssm-automation-integration) |
| 2 | **Configuration Export/Import Enhancement** | 3w | 📋 [Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md#5-configuration-exportimport-enhancement) |
| 3 | **Enhanced Results Storage & Audit Trail** | 3w | 📋 [Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md#2-enhanced-results-storage--audit-trail) |
| 4 | **Sample Environment Deployment** | 3w | 📋 [Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md#3-sample-environment-deployment) |
| 5 | **Self-Updating CI/CD Pipeline** | 3w | 📋 [Roadmap](docs/implementation/ENHANCEMENT_ROADMAP.md#4-self-updating-cicd-pipeline) |
| 6 | **Fresh Deployment Setup** | 2-3w | 🟢 Ready |
| 7 | **Scheduled Drills** | 3-5d | Planned |
| 8 | **SNS Notification Integration** | 1-2w | Planned |
| 9 | **Step Functions Visualization** | 2-3w | Planned |
| 10 | **Advanced DRS Server Management** | 8-10w | Planned |

#### Priority 1: Fresh Deployment Setup
Complete deployment automation for fresh AWS environments, including AWS native CI/CD pipeline setup. See the comprehensive [Fresh Deployment Specification](.kiro/specs/fresh-deployment/) which includes:

- **[Requirements](.kiro/specs/fresh-deployment/requirements.md)** - Complete deployment requirements and acceptance criteria
- **[Design Document](.kiro/specs/fresh-deployment/design.md)** - Detailed technical architecture and implementation approach  
- **[CI/CD Pipeline Specification](.kiro/specs/fresh-deployment/cicd-pipeline-specification.md)** - Automated deployment pipeline design
- **[Security & Compliance](.kiro/specs/fresh-deployment/security-compliance-specification.md)** - Security controls and compliance requirements
- **[Testing Strategy](.kiro/specs/fresh-deployment/testing-strategy.md)** - Comprehensive testing approach and validation
- **[Migration Strategy](.kiro/specs/fresh-deployment/migration-strategy.md)** - Migration planning and execution strategy
- **[Implementation Tasks](.kiro/specs/fresh-deployment/tasks.md)** - Detailed task breakdown and dependencies

### Migration Specifications

#### CI/CD Migration (GitLab → GitHub Actions) - COMPLETED
The project has been fully migrated from GitLab CI/CD to GitHub Actions (January 2026). See the [GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md) for current deployment instructions.

**Migration Documentation** (archived for reference):
- **[Requirements](.kiro/specs/cicd-migration/requirements.md)** - Migration requirements and acceptance criteria
- **[Design Document](.kiro/specs/cicd-migration/design.md)** - Technical migration approach and architecture
- **[Implementation Tasks](.kiro/specs/cicd-migration/tasks.md)** - Detailed migration task breakdown

### Recently Completed

#### ✅ **Role-Based Access Control (RBAC)** (v1.0 - December 31, 2025)
- 5 Granular DRS-Specific Roles with enterprise security
- API-First Security Enforcement across all access methods
- Cognito Groups Integration with JWT token validation

#### ✅ **Tag Synchronization** (v1.2.0 - January 1, 2026)
- Automated Tag Synchronization from EC2 to DRS source servers
- EventBridge Scheduling with configurable intervals
- Multi-Region Support across all 28 commercial AWS DRS regions

#### ✅ **Comprehensive REST API** (v1.1.0)
- 47+ API Endpoints across 12 categories
- Cross-Account Operations with automated role assumption
- Configuration Export/Import with dry-run validation

For detailed implementation plans, see [docs/implementation/](docs/implementation/) directory.

## Code Quality & Development Standards

### Python Coding Standards Implementation (v1.2.2)

The codebase has undergone a comprehensive code quality enhancement implementing complete Python coding standards across all Lambda functions and supporting scripts.

#### Code Quality Metrics

| Metric | Before v1.2.2 | After v1.2.2 | Improvement |
|--------|---------------|--------------|-------------|
| **PEP 8 Violations** | 187 violations | 0 violations | ✅ **100% resolved** |
| **Line Length Issues** | 45 violations | 0 violations | ✅ **Fully compliant** |
| **Import Organization** | 23 violations | 0 violations | ✅ **Standardized** |
| **Whitespace Issues** | 67 violations | 0 violations | ✅ **Clean formatting** |
| **Naming Conventions** | 31 violations | 0 violations | ✅ **Consistent naming** |
| **String Formatting** | 21 violations | 0 violations | ✅ **Standardized quotes** |
| **Black Formatting** | 10 Lambda files | 10 Lambda files | ✅ **79-char compliant** |

#### Standards Implementation Details

**Comprehensive PEP 8 Compliance**
- **Line Length**: All lines comply with 79-character limit (strict PEP 8 standard)
- **Import Organization**: Standardized import order (standard library → third-party → local imports)
- **Whitespace**: Consistent spacing around operators, function definitions, and class declarations
- **Naming Conventions**: Snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **String Formatting**: Standardized double quotes for strings, f-string formatting throughout
- **Black Formatting**: All 10 Lambda functions formatted with Black using 79-character line length

**Code Readability Enhancements**
- **Function Complexity**: Added `# noqa` comments for complex but necessary functions (DRS integration logic)
- **Variable Naming**: Improved descriptive variable names for better code comprehension
- **Comment Standards**: Enhanced inline documentation following technical standards
- **Error Handling**: Consistent exception handling patterns across all Lambda functions

**Development Workflow Integration**
- **Flake8 Configuration**: Updated `.flake8` with project-specific rules and exclusions
- **Pre-commit Hooks**: Enhanced `.pre-commit-config.yaml` with comprehensive Python linting
- **CI/CD Integration**: GitHub Actions pipeline includes automated code quality checks
- **Development Environment**: Virtual environment (`venv/`) includes all quality tools

#### Quality Assurance Tools

**Linting and Formatting**
```bash
# Code quality validation
flake8 lambda/ --config .flake8
black --check lambda/
isort --check-only lambda/

# Automated formatting
black lambda/
isort lambda/
```

**Testing Integration**
```bash
# Run tests with quality checks
pytest tests/python/unit/ -v --flake8
pytest tests/python/integration/ -v --cov=lambda
```

**Pre-commit Validation**
```bash
# Install pre-commit hooks
pre-commit install

# Run all quality checks
pre-commit run --all-files
```

#### Zero Functional Impact Guarantee

**Deployment Safety**
- **No API Changes**: All REST API endpoints maintain identical functionality and responses
- **No Business Logic Changes**: DRS integration, wave execution, and orchestration logic unchanged
- **No Database Schema Changes**: DynamoDB table structures and queries remain identical
- **No Authentication Changes**: Cognito integration and RBAC enforcement unchanged

**Production Deployment Verification**
- **Lambda Function Updates**: Successfully deployed code-only updates using `--update-lambda-code`
- **API Gateway Testing**: Verified all 42+ endpoints respond correctly with improved code
- **CloudWatch Monitoring**: Confirmed no errors or performance degradation post-deployment
- **User Acceptance**: All UI functionality operates identically with enhanced backend code

**Development Standards Documentation**

**Comprehensive Standards Coverage**
- **Technical Standards**: Complete documentation in `.kiro/steering/technical-standards.md`
- **Development Workflow**: Detailed procedures in `.kiro/steering/development-workflow.md`
- **Frontend Standards**: CloudScape design system rules in `.kiro/steering/frontend-standards.md`
- **Project Context**: Architecture and technology stack in `.kiro/steering/project-context.md`

#### Quality Metrics Tracking

**Baseline Violation Report**
The `baseline_violations_report.txt` provides complete documentation of all resolved violations:
- **Detailed Analysis**: Line-by-line breakdown of each violation type and resolution
- **File-by-File Tracking**: Comprehensive coverage across all Python files in the codebase
- **Resolution Patterns**: Documented approaches for each violation category
- **Quality Metrics**: Before/after comparison showing 100% violation resolution

**Continuous Quality Monitoring**
- **GitHub Actions Integration**: Automated quality checks on every commit and pull request
- **Pre-commit Hooks**: Local validation prevents quality regressions
- **Development Environment**: Virtual environment includes all necessary quality tools
- **Documentation Standards**: Technical writing follows established patterns and formats

#### Future Quality Initiatives

**Ongoing Improvements**
- **Type Hints**: Gradual addition of comprehensive type annotations
- **Docstring Standards**: Enhanced function and class documentation
- **Test Coverage**: Expansion of unit test coverage with quality metrics
- **Performance Optimization**: Code efficiency improvements while maintaining quality standards

**Quality Assurance Process**
- **Code Review Standards**: Established patterns for reviewing AI-generated and human-written code
- **Automated Testing**: Integration of quality checks into testing workflows
- **Documentation Quality**: Consistent technical writing standards across all documentation
- **Standards Evolution**: Regular updates to coding standards based on industry best practices

This comprehensive code quality implementation ensures the AWS DRS Orchestration platform maintains enterprise-grade code standards while preserving all existing functionality and performance characteristics.

## CI/CD Pipeline

The project uses **GitHub Actions** for automated deployment with comprehensive security scanning, workflow conflict prevention, and OIDC-based AWS authentication.

📋 **[GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md)** - Complete setup, usage, and troubleshooting guide for GitHub Actions CI/CD.

### Active CI/CD Infrastructure
- **Workflow**: `.github/workflows/deploy.yml`
- **Primary Repository**: GitHub (`johnjcousens/aws-elasticdrs-orchestrator`)
- **Authentication**: OIDC (no long-lived credentials)
- **OIDC Stack**: `cfn/github-oidc-stack.yaml`
- **Current Stack**: `aws-elasticdrs-orchestrator-dev`
- **Project Name**: `aws-elasticdrs-orchestrator`

### Pipeline Stages

| Stage | Duration | Description | Triggers |
|-------|----------|-------------|----------|
| **Detect Changes** | ~10s | Analyzes changed files to determine deployment scope | Always |
| **Validate** | ~2 min | CloudFormation validation, Python linting, TypeScript checking | Skip for docs-only |
| **Security Scan** | ~3 min | **Enhanced comprehensive security scanning** | Skip for docs-only |
| **Build** | ~3 min | Lambda packaging, frontend build | Skip for docs-only |
| **Test** | ~2 min | Unit tests | Skip for docs-only |
| **Deploy Infrastructure** | ~10 min | CloudFormation stack deployment | Only if infrastructure/Lambda changed |
| **Deploy Frontend** | ~2 min | S3 sync, CloudFront invalidation | Only if frontend changed or infrastructure deployed |

**Optimized Durations**:
- **Documentation-only**: ~30 seconds (95% time savings)
- **Frontend-only**: ~12 minutes (45% time savings)  
- **Full deployment**: ~22 minutes (complete pipeline)

### Workflow Conflict Prevention (MANDATORY)

**CRITICAL**: Always check for running workflows before pushing to prevent deployment conflicts and failures.

#### Safe Push Scripts
```bash
# RECOMMENDED: Safe push with automatic workflow checking
./scripts/safe-push.sh

# Alternative: Quick check before manual push
./scripts/check-workflow.sh && git push

# Emergency force push (skip workflow check)
./scripts/safe-push.sh --force
```

#### MANDATORY Rules
1. **ALWAYS check for running workflows** before pushing
2. **NEVER push while deployment is in progress** - causes conflicts and failures
3. **WAIT for completion** if workflow running (max 30 minutes)
4. **Use safe-push.sh** instead of manual `git push`
5. **Monitor deployment** until completion before making additional changes

#### Workflow Status Indicators
- ✅ **Safe to push**: No workflows running
- ⏳ **Wait required**: Deployment in progress (wait for completion)
- ❌ **Conflict risk**: Multiple workflows would overlap
- 🚨 **Emergency only**: Use `--force` flag only for critical hotfixes

### Intelligent Deployment Optimization

The pipeline automatically detects changes and skips unnecessary stages:

**📝 Documentation-Only Changes**
```bash
# Only *.md files, docs/* changed
./scripts/check-deployment-scope.sh  # Preview what will deploy
./scripts/safe-push.sh               # ~30 seconds deployment
```

**🌐 Frontend-Only Changes**
```bash
# Only frontend/* files changed
./scripts/safe-push.sh  # Skips infrastructure deployment (~12 minutes)
```

**🏗️ Infrastructure Changes**
```bash
# cfn/*, lambda/*, or mixed changes
./scripts/safe-push.sh  # Full pipeline (~22 minutes)
```

**💡 Check Before Push**
```bash
# Preview deployment scope before pushing
./scripts/check-deployment-scope.sh
```

### Enhanced Security Scanning

The pipeline includes **enterprise-grade security scanning** with automated thresholds and comprehensive reporting:

#### Security Tools & Coverage
- **Bandit** (v1.9.2) - Python security analysis with medium+ severity detection
- **Safety** (v2.3.4) - Python dependency vulnerability scanning
- **Semgrep** (v1.146.0) - Advanced security pattern matching for Python and YAML
- **CFN-Lint** (v0.83.8) - CloudFormation security linting and best practices
- **ESLint** - Frontend TypeScript/React security rule scanning
- **NPM Audit** - Frontend dependency vulnerability detection

#### Security Thresholds & Quality Gates
- **Critical Issues**: 0 allowed (fails build immediately)
- **High Issues**: 10 maximum (warning, continues deployment)
- **Total Issues**: 50 maximum (informational tracking)
- **Automated Reporting**: JSON + human-readable formats with 30-day retention

#### Comprehensive Scanning Scope
- **Python Code**: `lambda/` and `scripts/` directories
- **Frontend Code**: TypeScript/React security patterns and dependencies
- **Infrastructure**: CloudFormation template security and compliance
- **Dependencies**: Both Python (pip) and NPM vulnerability scanning

#### Security Reports & Artifacts
- **Structured Reports**: Raw JSON data + formatted text outputs
- **Security Summary**: Consolidated findings with remediation guidance
- **Threshold Validation**: Automated pass/fail decisions based on severity
- **Artifact Retention**: 30-day GitHub Actions artifact storage
- **Build Integration**: Security findings block deployment of critical vulnerabilities

This enhanced security scanning restores the comprehensive capabilities from the original CodePipeline setup, ensuring enterprise-grade security validation for all deployments.

### Quick Start

```bash
# 1. Deploy OIDC stack (one-time)
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name aws-elasticdrs-orchestrator-github-oidc \
  --parameter-overrides \
    ProjectName=aws-elasticdrs-orchestrator \
    Environment=dev \
    GitHubOrg=YOUR_ORG \
    GitHubRepo=YOUR_REPO \
    DeploymentBucket=aws-elasticdrs-orchestrator \
  --capabilities CAPABILITY_NAMED_IAM

# 2. Add GitHub secrets: AWS_ROLE_ARN, DEPLOYMENT_BUCKET, STACK_NAME, ADMIN_EMAIL
# 3. Push to main branch to trigger deployment (use safe-push.sh)
./scripts/safe-push.sh
```

### Manual Deployment (EMERGENCY ONLY)

⚠️ **CRITICAL**: Manual deployment scripts are for emergencies only. ALL regular deployments MUST use GitHub Actions CI/CD pipeline with workflow conflict prevention.

**Emergency Use Cases Only:**
- GitHub Actions service outage (confirmed AWS/GitHub issue)
- Critical production hotfix when pipeline is broken
- Pipeline debugging (with immediate Git follow-up)

```bash
# EMERGENCY ONLY: Fast Lambda code update (5 seconds)
./scripts/sync-to-deployment-bucket.sh --update-lambda-code

# EMERGENCY ONLY: Full CloudFormation deployment (5-10 minutes)
./scripts/sync-to-deployment-bucket.sh --deploy-cfn

# IMMEDIATELY follow up with proper Git commit and push
git add .
git commit -m "emergency: describe the critical fix"
./scripts/safe-push.sh  # Restores proper CI/CD tracking
```

**Why GitHub Actions is Required:**
- ✅ **Audit Trail**: All changes tracked in Git history
- ✅ **Quality Gates**: Automated validation, testing, security scanning
- ✅ **Team Visibility**: All deployments visible to team members
- ✅ **Rollback Capability**: Git-based rollback and deployment history
- ✅ **Enterprise Compliance**: Meets deployment standards and governance
- ✅ **Conflict Prevention**: Workflow overlap detection and prevention

## Contributing

### Standard Development Workflow (REQUIRED)

**ALL deployments MUST use GitHub Actions CI/CD pipeline with workflow conflict prevention:**

1. **Fork the GitHub repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make changes and test locally**
4. **Commit changes** (`git commit -m 'Add amazing feature'`)
5. **Push to GitHub** (`./scripts/safe-push.sh origin feature/amazing-feature`)
6. **Open a Pull Request**
7. **After merge to main**, changes automatically deploy via GitHub Actions

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/johnjcousens/aws-elasticdrs-orchestrator.git
cd aws-elasticdrs-orchestrator

# Frontend development
cd frontend
npm install
npm run dev  # Development server at localhost:5173

# Backend testing
cd tests/python
pip install -r requirements.txt
pytest unit/ -v

# Validate before committing
make validate  # CloudFormation validation
```

### Deployment Process

```bash
# Standard workflow - ALWAYS use this
git add .
git commit -m "feat: describe your changes"
./scripts/safe-push.sh  # Automatically checks for workflow conflicts

# Monitor pipeline at: https://github.com/johnjcousens/aws-elasticdrs-orchestrator/actions
```

### Prohibited Practices

❌ **NEVER bypass GitHub Actions for regular development**  
❌ **NEVER use manual sync scripts for convenience**  
❌ **NEVER deploy "quick fixes" without Git tracking**  
❌ **NEVER skip the pipeline "just this once"**  
❌ **NEVER push while GitHub Actions workflow is running** (causes conflicts)  
❌ **NEVER use `git push` directly without checking workflow status**

**Why these are prohibited:**
- No audit trail for changes
- Skip quality gates (validation, testing, security)
- Team unaware of deployments
- No rollback capability
- Compliance violations
- Deployment conflicts and failures

## Repository Snapshots & Rollback

The repository uses Git tags to mark significant milestones and maintains a clean structure with historical artifacts preserved in the archive:

### Archive Structure
```text
archive/
├── build-artifacts/          # Historical build outputs and deployment packages
├── cfn/                     # Legacy CloudFormation templates and configurations
├── cicd-migration/          # Completed CI/CD migration specification (GitHub Actions deployed January 2026)
├── presentations/           # Project presentations and demo materials
├── python-coding-standards/ # Completed PEP 8 implementation specification (v1.2.2)
├── reports/                 # Historical quality reports and compliance tracking (v1.2.2)
├── repository-cleanup/      # Completed repository cleanup specification
├── status-reports/          # Historical status reports and project updates
└── working-lambda-reference/ # Reference Lambda implementations and development code
```

### Git Tags & Milestones

| Tag | Description | Date | Commit |
|-----|-------------|------|--------|
| `RBAC-Prototype-with-Password-Reset-capability-v1.0` | **RBAC Prototype v1.0** - Comprehensive role-based access control with 6 granular roles, API-first enforcement, and password reset capability for new users | December 31, 2025 | `TBD` |
| `MVP-DRILL-PROTOTYPE` | **MVP Drill Prototype Complete** - Complete disaster recovery orchestration platform with multi-account support, tag-based selection, and comprehensive drill capabilities | December 30, 2025 | `a34c5b7` |
| `v2.0.0-mvp-drill-prototype` | **MVP Drill Only Prototype v2.0** - Core drill functionality with comprehensive documentation | December 30, 2025 | - |
| `mvp-demo-ready` | MVP Demo Ready - Complete working state with all core features | December 9, 2025 | - |

### Rollback to a Tag

```bash
# View the repository at the tagged state
git checkout mvp-demo-ready

# Create a new branch from tag for development
git checkout -b my-feature-branch mvp-demo-ready

# Return to main branch
git checkout main
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete project history since November 8, 2025.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Built for enterprise disaster recovery on AWS