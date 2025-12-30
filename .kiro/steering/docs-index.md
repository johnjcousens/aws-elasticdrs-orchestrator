# Documentation Index

Quick reference to detailed documentation. Use these when you need comprehensive specifications beyond the steering summaries.

## Requirements (Source of Truth)

These documents are the authoritative source for all system specifications. When conflicts exist between steering files and requirements documents, the requirements documents take precedence.

- [Product Requirements Document](docs/requirements/PRODUCT_REQUIREMENTS_DOCUMENT.md) - Features, capabilities, success metrics
- [Software Requirements Specification](docs/requirements/SOFTWARE_REQUIREMENTS_SPECIFICATION.md) - Functional requirements, API contracts, validation rules

### UX/UI Design Specifications (Modular)
- **[UX/UI Design Specifications](docs/requirements/UX_UI_DESIGN_SPECIFICATIONS.md)** - Master index and overview
- [Visual Design System](docs/requirements/UX_VISUAL_DESIGN_SYSTEM.md) - Colors, typography, spacing, icons
- [Technology Stack](docs/requirements/UX_TECHNOLOGY_STACK.md) - Dependencies, versions, build configuration
- [Page Specifications](docs/requirements/UX_PAGE_SPECIFICATIONS.md) - All 7 pages with layouts and behavior
- [Component Library](docs/requirements/UX_COMPONENT_LIBRARY.md) - All 32 components with usage patterns

## Architecture

- [Architecture Diagram (PNG)](docs/architecture/AWS-DRS-Orchestration-Architecture.png) - Visual system overview
- [Architecture Diagram (Source)](docs/architecture/AWS-DRS-Orchestration-Architecture.drawio) - Editable draw.io file
- [Architecture Diagrams](docs/architecture/ARCHITECTURE_DIAGRAMS.md) - All mermaid diagrams and flows
- [Architectural Design Document](docs/architecture/ARCHITECTURAL_DESIGN_DOCUMENT.md) - Detailed component architecture

## Implementation (Active Development)

### Consolidated Feature Categories
- [Cross-Account Features](docs/implementation/CROSS_ACCOUNT_FEATURES.md) - Multi-account orchestration, monitoring, and extended source servers
- [DRS Source Server Management](docs/implementation/DRS_SOURCE_SERVER_MANAGEMENT.md) - Complete DRS server configuration and management
- [Automation & Orchestration](docs/implementation/AUTOMATION_AND_ORCHESTRATION.md) - SSM automation, Step Functions, and scheduled drills
- [Notifications & Monitoring](docs/implementation/NOTIFICATIONS_AND_MONITORING.md) - SNS notifications, monitoring, and alerting
- [Recovery Enhancements](docs/implementation/RECOVERY_ENHANCEMENTS.md) - Agent installation, replication monitoring, and failover/failback
- [Infrastructure Improvements](docs/implementation/INFRASTRUCTURE_IMPROVEMENTS.md) - CI/CD migration and MCP integration

### Consolidation Strategy
- [Future Enhancements Consolidation Plan](docs/FUTURE_ENHANCEMENTS_CONSOLIDATION_PLAN.md) - Documentation consolidation strategy and progress

### Archived Implementation Plans
- [Archived Plans](docs/archive/implementation/) - Completed feature implementation plans (20+ archived documents)

## Guides

### Essential Guides (New)
- [API Reference Guide](docs/guides/API_REFERENCE_GUIDE.md) - Complete REST API documentation with examples
- [Development Workflow Guide](docs/guides/DEVELOPMENT_WORKFLOW_GUIDE.md) - Development, testing, and deployment procedures
- [Troubleshooting Guide](docs/guides/TROUBLESHOOTING_GUIDE.md) - Common issues and debugging procedures

### Existing Guides
- [Multi-Account Setup Guide](docs/guides/MULTI_ACCOUNT_SETUP_GUIDE.md) - Cross-account configuration and deployment
- [Local Development Guide](docs/guides/LOCAL_DEVELOPMENT.md) - Development environment setup
- [Manual Test Instructions](docs/guides/MANUAL_TEST_INSTRUCTIONS.md) - Manual testing procedures
- [Deployment and Operations Guide](docs/guides/DEPLOYMENT_AND_OPERATIONS_GUIDE.md) - Step-by-step deployment
- [Deployment Recovery Guide](docs/guides/DEPLOYMENT_RECOVERY_GUIDE.md) - Redeploy from S3 artifacts
- [Orchestration Integration Guide](docs/guides/ORCHESTRATION_INTEGRATION_GUIDE.md) - CLI, SSM, Step Functions, EventBridge, Python SDK integration
- [Testing and Quality Assurance](docs/guides/TESTING_AND_QUALITY_ASSURANCE.md) - Test strategy and procedures

## Reference

- [DRS Complete IAM Analysis](docs/reference/DRS_COMPLETE_IAM_ANALYSIS.md) - Critical IAM permissions for DRS
- [AWS DRS API Reference](docs/guides/AWS_DRS_API_REFERENCE.md) - DRS API integration patterns

## Research & Analysis

- [AWS DRS Cross-Account Comprehensive Research](docs/research/AWS_DRS_CROSS_ACCOUNT_COMPREHENSIVE_RESEARCH.md) - Cross-account DRS implementation research

## Implementation Status

- [Multi-Account Implementation Status](docs/implementation/MULTI_ACCOUNT_IMPLEMENTATION_STATUS.md) - Current multi-account feature status

## Troubleshooting

- [Drill Debugging Checklist](docs/troubleshooting/DRILL_DEBUGGING_CHECKLIST.md) - Step-by-step drill troubleshooting
- [DRS Drill Failure Analysis](docs/troubleshooting/DRS_DRILL_FAILURE_ANALYSIS.md) - Common failures and fixes
- [IAM Permission Troubleshooting](docs/troubleshooting/IAM_ROLE_ANALYSIS_DRS_PERMISSIONS.md) - Permission issues
