# ADR-001: Function-Specific IAM Roles and CloudFormation Reorganization

**Status**: Accepted

**Date**: 2025-01-28

**Deciders**: Platform Engineering Team

**Related Requirements**: Requirements 16.1-16.117 (Function-Specific IAM Roles), Requirements 16.47 (CloudFormation Reorganization)

## Context

The DR Orchestration Platform initially used a single unified IAM role shared across 5 Lambda functions, with CloudFormation templates organized in a flat directory structure. As the platform matured, two architectural issues became apparent:

### Problem 1: Security Risk from Unified IAM Role

The unified role (`UnifiedOrchestrationRole`) contained 20+ inline policies granting comprehensive permissions across DRS, EC2, DynamoDB, Step Functions, SNS, S3, CloudFront, and other AWS services. All 5 Lambda functions shared this role:

- **Query Handler**: Read-only function for status queries
- **Data Management Handler**: DynamoDB CRUD and DRS metadata operations
- **Execution Handler**: Step Functions orchestration and notifications
- **Orchestration Function**: DRS recovery operations (critical)
- **Frontend Deployer**: S3 and CloudFront deployment operations

This architecture violated the principle of least privilege in several ways:

1. **Excessive Permissions**: The read-only Query Handler had write permissions to DynamoDB, DRS recovery operations, and Step Functions execution capabilities it never used
2. **Large Blast Radius**: A compromised query function could execute disaster recovery operations, delete production data, or terminate recovery instances
3. **Audit Complexity**: CloudTrail logs showed all actions performed by "UnifiedOrchestrationRole" without clear attribution to specific functions
4. **Compliance Gap**: Failed AWS Well-Architected Framework security pillar requirements for least privilege access

### Problem 2: Maintainability Issues from Flat CloudFormation Structure

All CloudFormation templates resided in a flat `/cfn/` directory:

```
cfn/
├── master-template.yaml (1200+ lines, monolithic)
├── lambda-stack.yaml
├── dynamodb-stack.yaml
├── eventbridge-stack.yaml
├── api-auth-stack.yaml
├── api-core-stack.yaml
├── api-resources-stack.yaml
├── api-core-methods-stack.yaml
├── api-infrastructure-methods-stack.yaml
├── api-operations-methods-stack.yaml
├── api-deployment-stack.yaml
└── ... (15+ templates)
```

This structure created maintainability challenges:

1. **Navigation Difficulty**: Developers had to scan 15+ templates to find IAM roles, Lambda functions, or DynamoDB tables
2. **Monolithic Master Template**: The 1200+ line master template orchestrated all nested stacks, making it difficult to understand dependencies
3. **No Service Grouping**: Related resources (e.g., all Lambda functions, all IAM roles) were scattered across multiple templates
4. **Duplicate Resources**: EventBridge rules appeared in both `lambda-stack.yaml` and `eventbridge-stack.yaml`, causing confusion
5. **Scaling Concerns**: Adding new services required modifying the monolithic master template

## Decision

We decided to implement two architectural improvements:

### Decision 1: Implement Function-Specific IAM Roles

Replace the single unified IAM role with five dedicated roles, each scoped to the minimum permissions required by its Lambda function:

1. **Query Handler Role**: Read-only DRS, DynamoDB, EC2, and CloudWatch permissions
2. **Data Management Role**: DynamoDB CRUD, DRS metadata, and tagging permissions (NO recovery operations)
3. **Execution Handler Role**: Step Functions, SNS, DynamoDB, and DRS orchestration permissions
4. **Orchestration Role**: Comprehensive DRS and EC2 permissions for recovery operations (most privileged)
5. **Frontend Deployer Role**: S3, CloudFront, and CloudFormation read permissions (NO DRS or DynamoDB access)

**Backward Compatibility**: Maintain the unified role architecture through a CloudFormation parameter (`UseFunctionSpecificRoles`) that allows switching between architectures without data loss.

### Decision 2: Reorganize CloudFormation Templates into Service-Based Nested Stacks

Create a new directory structure organizing templates by AWS service:

```
cfn/
├── main-stack.yaml (new root orchestrator)
├── iam/
│   └── roles-stack.yaml (all IAM roles)
├── lambda/
│   └── functions-stack.yaml (all Lambda functions)
├── dynamodb/
│   └── tables-stack.yaml (all DynamoDB tables)
├── stepfunctions/
│   └── statemachine-stack.yaml (Step Functions state machine)
├── sns/
│   └── topics-stack.yaml (SNS topics)
├── eventbridge/
│   └── rules-stack.yaml (EventBridge rules, consolidated)
├── s3/
│   └── buckets-stack.yaml (S3 buckets)
├── cloudfront/
│   └── distribution-stack.yaml (CloudFront distribution)
├── apigateway/
│   ├── auth-stack.yaml
│   ├── core-stack.yaml
│   ├── resources-stack.yaml
│   ├── core-methods-stack.yaml
│   ├── infrastructure-methods-stack.yaml
│   ├── operations-methods-stack.yaml
│   └── deployment-stack.yaml
├── cognito/
│   └── auth-stack.yaml (Cognito user pool)
├── monitoring/
│   └── alarms-stack.yaml (CloudWatch alarms)
└── waf/
    └── webacl-stack.yaml (WAF web ACL)
```

**Backward Compatibility**: Preserve the existing `/cfn/master-template.yaml` and flat structure for production use. The new `main-stack.yaml` deploys to test/QA environments only.

## Rationale

### Why Function-Specific IAM Roles?

**Security Benefits**:
- **Reduced Blast Radius**: A compromised Query Handler can only read data, not execute recovery operations or modify DynamoDB tables
- **Least Privilege**: Each function has only the permissions it needs, following AWS security best practices
- **Audit Clarity**: CloudTrail logs clearly show which function performed which action (e.g., "QueryHandlerRole" vs "OrchestrationRole")
- **Compliance**: Meets AWS Well-Architected Framework security pillar requirements and industry compliance standards (SOC2, ISO 27001)

**Operational Benefits**:
- **Faster Incident Response**: Security teams can immediately identify which function was compromised based on CloudTrail logs
- **Granular Monitoring**: CloudWatch alarms can detect permission issues per function, not just globally
- **Safer Development**: Developers can test new features in dev environment without risk of accidentally triggering production recovery operations

**Example Security Improvement**:

Before (Unified Role):
```
Query Handler → UnifiedRole → Can execute StartRecovery, TerminateInstances, DeleteItem
```

After (Function-Specific Roles):
```
Query Handler → QueryHandlerRole → Can ONLY execute Describe* operations
Orchestration Function → OrchestrationRole → Can execute StartRecovery, TerminateInstances
```

If the Query Handler is compromised (e.g., SQL injection, SSRF), the attacker can only read data, not execute disaster recovery operations.

### Why CloudFormation Reorganization?

**Maintainability Benefits**:
- **Service-Based Organization**: Developers can immediately locate IAM roles in `/cfn/iam/`, Lambda functions in `/cfn/lambda/`, etc.
- **Modular Architecture**: Nested stacks can be updated independently without modifying the root template
- **Clear Separation**: IAM, Lambda, and service resources in dedicated templates reduce cognitive load
- **Reduced Complexity**: Smaller, focused templates (200-300 lines) instead of monolithic master template (1200+ lines)

**Operational Benefits**:
- **Faster Development**: Developers can modify a single service stack without understanding the entire infrastructure
- **Safer Updates**: Changes to Lambda functions don't require modifying IAM roles or DynamoDB tables
- **Better Testing**: Service-specific stacks can be tested independently before integration
- **Easier Onboarding**: New developers can understand one service at a time instead of the entire monolith

**Example Maintainability Improvement**:

Before (Flat Structure):
```
Developer needs to add a new Lambda function:
1. Open master-template.yaml (1200+ lines)
2. Find Lambda section (line 400-800)
3. Add function definition
4. Find IAM section (line 100-300)
5. Add role definition
6. Update 5+ parameter references
7. Risk: Accidentally modify unrelated resources
```

After (Service-Based Structure):
```
Developer needs to add a new Lambda function:
1. Open cfn/lambda/functions-stack.yaml (300 lines)
2. Add function definition
3. Open cfn/iam/roles-stack.yaml (400 lines)
4. Add role definition
5. Update main-stack.yaml to pass role ARN (10 lines)
6. Risk: Minimal, only modifying relevant service stacks
```

## Alternatives Considered

### Alternative 1: Keep Unified Role, Add IAM Conditions

**Description**: Keep the single unified role but add IAM condition keys to restrict permissions based on Lambda function name.

**Example**:
```yaml
- Effect: Allow
  Action: drs:StartRecovery
  Resource: "*"
  Condition:
    StringEquals:
      aws:PrincipalTag/FunctionName: orchestration-function
```

**Why Rejected**:
- **Complexity**: Requires tagging all Lambda functions and maintaining complex condition logic
- **Limited Effectiveness**: Condition keys don't prevent a compromised function from assuming the role directly
- **Audit Confusion**: CloudTrail logs still show "UnifiedRole" performing actions, not specific functions
- **Maintenance Burden**: Every new permission requires adding condition keys to multiple policies

### Alternative 2: Use AWS IAM Permission Boundaries

**Description**: Keep the unified role but apply permission boundaries to each Lambda function.

**Why Rejected**:
- **Indirect Control**: Permission boundaries limit what a role can do, but the role still has all permissions granted
- **Complexity**: Requires managing both role policies and permission boundaries
- **Audit Confusion**: CloudTrail logs show the role's full permissions, not the effective permissions after boundary
- **Limited Adoption**: Permission boundaries are less commonly used and understood by developers

### Alternative 3: Keep Flat CloudFormation Structure, Use Comments for Organization

**Description**: Keep all templates in `/cfn/` but add extensive comments to organize resources by service.

**Why Rejected**:
- **Doesn't Scale**: Comments don't prevent the master template from growing to 2000+ lines
- **No Enforcement**: Developers can still add resources to wrong templates
- **Limited Tooling**: IDEs and CloudFormation tools don't understand comment-based organization
- **Duplicate Resources**: Comments don't prevent EventBridge rules from appearing in multiple templates

### Alternative 4: Consolidate API Gateway Nested Stacks into Single Template

**Description**: Merge the 7 API Gateway nested stacks into a single `apigateway-stack.yaml`.

**Why Rejected**:
- **Monolithic Template**: Would create a 1500+ line template, defeating the purpose of reorganization
- **Deployment Risk**: Single template means all API Gateway resources update together, increasing risk
- **Existing Architecture**: The current 7-stack pattern works well and follows AWS best practices for API Gateway
- **No Clear Benefit**: Consolidation would reduce maintainability without providing security or operational benefits

## Consequences

### Positive Consequences

**Security**:
- ✅ Reduced blast radius: Compromised query function cannot execute recovery operations
- ✅ Least privilege: Each function has only the permissions it needs
- ✅ Audit clarity: CloudTrail logs clearly show which function performed which action
- ✅ Compliance: Meets AWS Well-Architected Framework security best practices

**Maintainability**:
- ✅ Service-based organization: Easy to locate and modify infrastructure code
- ✅ Modular architecture: Nested stacks can be updated independently
- ✅ Clear separation: IAM, Lambda, and service resources in dedicated templates
- ✅ Reduced complexity: Smaller, focused templates instead of monolithic master template

**Operational**:
- ✅ Backward compatibility: Can rollback to unified role without data loss
- ✅ Gradual migration: Test in dev before promoting to production
- ✅ No downtime: CloudFormation update completes without service interruption
- ✅ Monitoring: CloudWatch alarms detect permission issues immediately

### Negative Consequences

**Complexity**:
- ⚠️ More IAM roles to manage (5 instead of 1)
- ⚠️ More CloudFormation templates to maintain (12 service stacks instead of 1 master template)
- ⚠️ More complex deployment: Must sync nested stack templates to S3 before deploying main stack

**Migration Effort**:
- ⚠️ Requires comprehensive testing to ensure functional equivalence
- ⚠️ Requires updating deployment scripts to support new nested stack architecture
- ⚠️ Requires documentation updates for new directory structure

**Operational Overhead**:
- ⚠️ Developers must understand nested stack dependencies
- ⚠️ CloudFormation updates may take longer due to nested stack orchestration
- ⚠️ Debugging stack failures requires understanding parent-child stack relationships

### Mitigation Strategies

**For Complexity**:
- Create comprehensive documentation in `/cfn/README.md` explaining the nested stack architecture
- Provide deployment examples for both `scripts/deploy.sh` (existing) and `scripts/deploy-main-stack.sh` (new)
- Use consistent parameter naming across all nested stacks (ProjectName, Environment, DeploymentBucket)

**For Migration Effort**:
- Implement comprehensive functional equivalence testing (Task 18.6)
- Execute negative security tests to verify permission restrictions (Task 18.7)
- Test rollback capability to ensure backward compatibility (Task 18.8)
- Deploy to QA environment first, validate thoroughly before production

**For Operational Overhead**:
- Create CloudWatch dashboard showing nested stack status
- Implement CloudWatch alarms for stack update failures
- Document troubleshooting procedures for common nested stack issues
- Provide training for developers on nested stack architecture

## Implementation Status

**Completed**:
- ✅ Task 18.6: Functional equivalence testing (all tests passed)
- ✅ Task 18.7: Negative security testing (all tests passed)
- ✅ Task 18.8: Rollback testing (verified backward compatibility)
- ✅ Task 18.10: Monitoring verification (CloudWatch alarms operational)
- ✅ Task 19: QA deployment (stack deployed successfully)
- ✅ Task 19.8: QA negative security tests (all tests passed)
- ✅ Task 19.9: QA monitoring verification (alarms operational)
- ✅ Task 19.10: QA EventBridge verification (rules operational)

**Current Status**: Implementation complete and validated in QA environment. Ready for production deployment.

## References

- [Requirements Document](.kiro/specs/function-specific-iam-roles/requirements.md)
- [Design Document](.kiro/specs/function-specific-iam-roles/design.md)
- [QA Deployment Configuration](../QA_DEPLOYMENT_CONFIGURATION.md)
- [Functional Equivalence Test Results](../../tests/integration/TASK_18_6_FUNCTIONAL_EQUIVALENCE_SUMMARY.md)
- [Negative Security Test Results](../../tests/integration/TASK_18_7_NEGATIVE_SECURITY_TESTS.md)
- [Rollback Test Guide](../../tests/integration/TASK_18_8_ROLLBACK_TEST_GUIDE.md)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
