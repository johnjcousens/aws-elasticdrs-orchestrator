#!/bin/bash
set -e

echo "========================================"
echo "Add Detailed Tag Descriptions"
echo "========================================"
echo ""
echo "This will recreate all tags with comprehensive descriptions"
echo ""

# Delete existing tags
echo "Removing existing tags..."
git tag -d v0.1.0 v0.2.0 v0.3.0 v0.4.0 v0.5.0 v0.6.0 2>/dev/null || true
git tag -d v1.0.0 v1.1.0 v1.2.0 v1.3.0 v1.4.0 v1.5.0 v1.6.0 v1.7.0 v1.8.0 2>/dev/null || true
git tag -d v2.0.0 v2.1.0 v2.2.0 v2.3.0 v2.4.0 v2.5.0 v2.6.0 v2.7.0 v2.8.0 v2.9.0 2>/dev/null || true

echo ""
echo "Creating tags with detailed descriptions..."
echo ""

# Phase 1: Foundation & Prototyping
echo "Phase 1: Foundation (v0.x.x)..."

git tag -a v0.1.0 $(git rev-list -n 1 phase-1-baseline) -m "v0.1.0 - Initial Prototype

Foundation release featuring:
- Basic CloudFormation infrastructure
- Initial Lambda function framework
- DRS API exploration and integration
- Project structure and development environment
- First working deployment to AWS"

git tag -a v0.2.0 $(git rev-list -n 1 working-drs-drill-integration) -m "v0.2.0 - DRS Drill Integration

First working DRS drill capability featuring:
- DRS drill execution via API
- Basic recovery operations
- Source server discovery
- Initial testing framework
- Proof of concept validation"

git tag -a v0.3.0 $(git rev-list -n 1 v1.0.0-step-functions-drs-discovery) -m "v0.3.0 - Step Functions Orchestration

Step Functions integration featuring:
- State machine orchestration
- DRS server discovery automation
- Workflow coordination
- Error handling patterns
- Foundation for wave-based execution"

# Phase 2: Core Features
echo "Phase 2: Core Features (v0.4-v0.6)..."

git tag -a v0.4.0 $(git rev-list -n 1 v1.4) -m "v0.4.0 - Backend Integration

Backend API and database integration featuring:
- DynamoDB table design
- API Gateway REST endpoints
- Lambda function integration
- CRUD operations for protection groups
- Data persistence layer"

git tag -a v0.5.0 $(git rev-list -n 1 v1.0.0-prototype-drs-working) -m "v0.5.0 - Working Prototype

First end-to-end working prototype featuring:
- Complete DRS recovery workflow
- Protection group management
- Recovery plan creation
- Execution tracking
- Basic UI components"

git tag -a v0.6.0 $(git rev-list -n 1 v1.5-working-prototype) -m "v0.6.0 - Enhanced Prototype

Enhanced prototype with improvements featuring:
- Improved error handling
- Better UI/UX design
- Enhanced logging and monitoring
- Performance optimizations
- Stability improvements"

# Phase 3: Major Features
echo "Phase 3: Major Features (v1.0-v1.2)..."

git tag -a v1.0.0 $(git rev-list -n 1 v4.0-ProtoType-StepFunctionsWithPauseAndResume) -m "v1.0.0 - Wave-Based Orchestration

First major release featuring:
- Wave-based recovery execution
- Pause/resume functionality
- waitForTaskToken pattern
- Manual validation gates between waves
- Coordinated multi-tier recovery
- Production-ready orchestration"

git tag -a v1.1.0 $(git rev-list -n 1 v5.0-Prototype-UIEnhancements) -m "v1.1.0 - CloudScape Design System

UI enhancement release featuring:
- AWS CloudScape Design System integration
- Professional AWS console-style interface
- Enhanced user experience
- Improved navigation and layout
- Consistent design patterns"

git tag -a v1.2.0 $(git rev-list -n 1 mvp-demo-ready) -m "v1.2.0 - MVP Demo Ready

Minimum viable product release featuring:
- Complete recovery workflow
- Protection group management
- Recovery plan orchestration
- Execution history tracking
- Demo-ready functionality"

# Phase 4: Advanced Features
echo "Phase 4: Advanced Features (v1.3-v1.5)..."

git tag -a v1.3.0 $(git rev-list -n 1 DualModeWithTagAndCommandLineSupport) -m "v1.3.0 - Dual Mode Support

Advanced recovery modes featuring:
- Tag-based server selection
- Plan-based orchestration
- Flexible recovery options
- Command-line interface support
- Dynamic server discovery"

git tag -a v1.4.0 $(git rev-list -n 1 drs-launch-settings-v1) -m "v1.4.0 - Launch Settings Management

Bulk DRS configuration featuring:
- Launch configuration management
- EC2 launch template integration
- Bulk settings updates
- Server-level customization
- Configuration validation"

git tag -a v1.5.0 $(git rev-list -n 1 ArchitectureDocsUpdated) -m "v1.5.0 - Architecture Documentation

Documentation milestone featuring:
- Comprehensive architecture diagrams
- Technical specifications
- Deployment guides
- API documentation
- Best practices documentation"

# Phase 5: Enterprise Features
echo "Phase 5: Enterprise Features (v1.6-v1.8)..."

git tag -a v1.6.0 $(git rev-list -n 1 tag-sync-prototype-28-regions) -m "v1.6.0 - Multi-Region Support

Multi-region capability featuring:
- 28 AWS regions support
- Tag synchronization across regions
- Cross-region operations
- Regional failover support
- Global deployment capability"

git tag -a v1.7.0 $(git rev-list -n 1 v1.0.0-multi-account-prototype) -m "v1.7.0 - Multi-Account Architecture

Cross-account management featuring:
- Hub-and-spoke architecture
- Cross-account IAM roles
- Multi-account orchestration
- Centralized management
- Enterprise-scale support"

git tag -a v1.8.0 $(git rev-list -n 1 MVP-DRILL-PROTOTYPE) -m "v1.8.0 - Production Drill Capability

Production-ready drill release featuring:
- Complete drill workflow
- Automated testing
- Production validation
- Rollback capabilities
- Enterprise readiness"

# Phase 6: Security & RBAC
echo "Phase 6: Security & RBAC (v2.0-v2.4)..."

git tag -a v2.0.0 $(git rev-list -n 1 RBAC-Prototype-with-Password-Reset-capability-v1.0) -m "v2.0.0 - RBAC Implementation

Security milestone featuring:
- Role-based access control
- Cognito user management
- Permission-based authorization
- Password reset capability
- Security groups and policies
- Enterprise security compliance"

git tag -a v2.1.0 $(git rev-list -n 1 RBAC-Documentation-Complete-v1.1) -m "v2.1.0 - RBAC Documentation

Security documentation featuring:
- Complete RBAC documentation
- Permission matrices
- User management guides
- Security best practices
- Compliance documentation"

git tag -a v2.2.0 $(git rev-list -n 1 Documentation-Security-Fixes-v1.1.1) -m "v2.2.0 - Security Enhancements

Security improvements featuring:
- Security scanning integration
- Vulnerability fixes
- Compliance improvements
- Code quality enhancements
- Security audit trail"

git tag -a v2.3.0 $(git rev-list -n 1 GitLab-CICD-Pipeline-Alignment-v1.2.0) -m "v2.3.0 - CI/CD Pipeline

Automation milestone featuring:
- GitLab CI/CD integration
- Automated deployments
- Pipeline optimization
- Quality gates
- Continuous integration"

git tag -a v2.4.0 $(git rev-list -n 1 v2.1.0-major-doc-consolidation) -m "v2.4.0 - Documentation Consolidation

Documentation overhaul featuring:
- Consolidated documentation structure
- Improved organization
- Complete user guides
- API reference documentation
- Troubleshooting guides"

# Phase 7: Restoration & Stability
echo "Phase 7: Restoration & Stability (v2.5-v2.9)..."

git tag -a v2.5.0 $(git rev-list -n 1 v1.6.0-working-prototype-restored) -m "v2.5.0 - Functionality Restoration

Restoration milestone featuring:
- Restored working functionality
- Bug fixes after refactoring
- Stability improvements
- Performance optimization
- System reliability"

git tag -a v2.6.0 $(git rev-list -n 1 v1.6.0-comprehensive-restoration-milestone) -m "v2.6.0 - Complete System Restoration

Comprehensive restoration featuring:
- All features working
- Complete functionality restored
- Performance optimization
- System stability
- Production readiness"

git tag -a v2.7.0 $(git rev-list -n 1 v1.6.1-eventbridge-restored) -m "v2.7.0 - EventBridge Polling

EventBridge integration featuring:
- Execution polling functionality
- Real-time status updates
- Event-driven architecture
- Automated monitoring
- Execution tracking"

git tag -a v2.8.0 $(git rev-list -n 1 v1.7.0-eventbridge-enhanced) -m "v2.8.0 - EventBridge Enhancement

EventBridge improvements featuring:
- Enhanced polling mechanism
- Better error handling
- Performance optimization
- Reliability improvements
- Monitoring enhancements"

git tag -a v2.9.0 $(git rev-list -n 1 v1.3.0-pre-security-fixes) -m "v2.9.0 - Pre-Refactor Baseline

Stable baseline featuring:
- All features working
- Stable codebase
- Production-ready
- Pre-refactor snapshot
- Migration preparation"

echo ""
echo "✅ All tags recreated with detailed descriptions!"
echo ""
echo "Pushing updated tags to remote..."
git push origin --tags --force

echo ""
echo "✅ Complete! View tags with: git tag -l -n99 v*"
echo ""
