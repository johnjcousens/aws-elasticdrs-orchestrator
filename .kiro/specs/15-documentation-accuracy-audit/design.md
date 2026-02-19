# Design Document: Documentation Accuracy Audit

## Overview

This design covers a documentation-only correction pass across the HRP DRS Tech Adapter project (deployed as stack `hrp-drs-tech-adapter-dev` in `us-east-2`, account `891376951562`). No code in `/lambda`, `/cfn`, or `/frontend` will be modified. The work targets 7 documentation files plus the README, fixing broken links, incorrect counts, missing handler/module documentation, stale IAM policy descriptions, undocumented API endpoints, and wrong script references.

The changes are purely textual edits to Markdown files. There is no new architecture, no new components, and no data model changes. The design focuses on what content needs to change in each file and the order of operations to ensure consistency.

All corrections are verified against the actual deployed codebase:
- `cfn/master-template.yaml` — the source of truth for stack structure, IAM policies, and parameters
- `lambda/` directory — the source of truth for handler and shared module inventory
- `scripts/` directory — the source of truth for deployment script names

## Architecture

No architectural changes. The existing documentation file structure remains:

```
docs/
├── architecture/
│   ├── ARCHITECTURE.md          # Req 2: Stack info corrections
│   └── LAMBDA_HANDLERS_ARCHITECTURE.md  # Req 3, 4: Add handlers + modules
├── deployment/
│   └── QUICK_START_GUIDE.md     # Req 7: Fix script reference
├── guides/
│   └── DEVELOPER_GUIDE.md       # Req 7: Fix script reference
├── iam/
│   └── ORCHESTRATION_ROLE_POLICY.md  # Req 5: IAM corrections
├── reference/
│   ├── API_ENDPOINTS_CURRENT.md      # Req 6: Endpoint corrections
│   └── ORCHESTRATION_ROLE_SPECIFICATION.md  # Req 5: Role name fix
README.md                        # Req 1: Fix broken links
```

## Components and Interfaces

### Component 1: README Link Fixes (Requirement 1)

Three links in the README Documentation section point to non-existent files:

| Broken Link | Resolution Strategy |
|---|---|
| `docs/analysis/LAMBDA_HANDLERS_COMPLETE_ANALYSIS.md` | Redirect link to `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md` (closest existing equivalent) |
| `docs/api-reference/EXECUTION_HANDLER_API.md` | Redirect link to `docs/reference/API_ENDPOINTS_CURRENT.md` with a note that execution endpoints are documented there |
| `docs/troubleshooting/ERROR_CODES.md` | Create a minimal stub file listing the 13 error codes referenced in the README, with brief descriptions |

Rationale: For the first two, existing docs already cover the content. Creating stubs would duplicate information. For ERROR_CODES.md, no existing file covers this content, so a stub is warranted.

### Component 2: Architecture Doc Corrections (Requirement 2)

Four corrections to `docs/architecture/ARCHITECTURE.md`:

1. Add WAFStack to the nested stack table with a note: "Conditional — deployed only when `DeployFrontend=true` AND region is `us-east-1` (required for CloudFront CLOUDFRONT scope)"
   - Verified: `DeployWAFCondition` in master-template.yaml requires `DeployApiGateway=true`, `DeployFrontend=true`, AND `AWS::Region=us-east-1`
2. Move `cross-account-role-stack.yaml` and `github-oidc-stack.yaml` out of the nested stack table into a separate "Standalone Templates" section, noting they are deployed independently
   - Verified: Neither file is referenced as an `AWS::CloudFormation::Stack` resource in master-template.yaml
3. Change the total stack count. The master template contains exactly 14 `AWS::CloudFormation::Stack` resources (some conditional):
   - Always deployed (3): DatabaseStack, LambdaStack, StepFunctionsStack, EventBridgeStack
   - Conditional on API Gateway (7): ApiAuthStack, ApiGatewayCoreStack, ApiGatewayResourcesStack, ApiGatewayCoreMethodsStack, ApiGatewayOperationsMethodsStack, ApiGatewayInfrastructureMethodsStack, ApiGatewayDeploymentStack
   - Conditional on notifications (1): NotificationStack
   - Conditional on frontend+API (1): FrontendStack
   - Conditional on WAF (1): WAFStack
   - Plus 2 standalone templates (cross-account-role, github-oidc) not deployed by master
   - The doc should say "15 CloudFormation templates total: 1 master + 14 nested stacks (some conditional) + 2 standalone templates"
4. Replace all references to `DeploymentBucket` parameter with `SourceBucket`
   - Verified: The actual parameter in master-template.yaml is `SourceBucket` with default `hrp-drs-tech-adapter`

### Component 3: Lambda Handler Documentation (Requirement 3)

Add documentation sections to `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md` for the 3 missing handlers. Verified against `lambda/` directory structure and `cfn/master-template.yaml` LambdaStack:

| Handler | Directory | Key Details |
|---|---|---|
| `dr-orchestration-stepfunction` | `lambda/dr-orchestration-stepfunction/` | Wave orchestration engine invoked by Step Functions state machine. Handles wave execution, launch config sync, DRS recovery initiation. Referenced in master template as `DrOrchestrationStepFunctionArn` |
| `frontend-deployer` | `lambda/frontend-deployer/` | CloudFormation Custom Resource handler. Builds frontend, syncs to S3, invalidates CloudFront. Referenced in master template as `FrontendDeployerFunctionArn` |
| `drs-agent-deployer` | `lambda/drs-agent-deployer/` | SSM-based DRS agent deployment. Not yet developed — directory exists with code but is not referenced in master-template.yaml or lambda-stack.yaml. Should be documented with a note about its pre-development status |

The current doc only covers 3 handlers (data-management-handler, execution-handler, query-handler). It also mentions `notification-formatter` in a "Supporting Handlers" section but doesn't give it a full documentation section. After this update, all 6 directories under `lambda/` (excluding `shared/`) should be documented.

Each new section should follow the existing documentation pattern: purpose, key operations, invocation pattern, and a Mermaid diagram if appropriate.

### Component 4: Shared Module Documentation (Requirement 4)

Add entries to the shared modules table in `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`. Verified against `lambda/shared/` directory listing (17 files total):

Currently documented (6): `account_utils.py`, `conflict_detection.py`, `cross_account.py`, `drs_limits.py`, `response_utils.py`, and partially `rbac_middleware.py`

Need to add (9 production modules):

| Module | Purpose |
|---|---|
| `config_merge.py` | Merges per-server launch configs with protection group defaults |
| `drs_regions.py` | DRS regional availability data (30 regions) |
| `drs_utils.py` | DRS API helper functions, server data transformation |
| `execution_utils.py` | Execution state management utilities |
| `iam_utils.py` | IAM role and policy helper functions |
| `launch_config_validation.py` | Validates launch configuration parameters (subnet, SG, IP) |
| `notifications.py` | SNS notification publishing utilities |
| `security_utils.py` | Input sanitization and security validation |
| `staging_account_models.py` | Data models for staging account management |

Excluded from documentation (2):
- `__init__.py` — Package init, no documentation needed
- `test_staging_account_models.py` — Test file, not a production module

### Component 5: IAM Documentation Corrections (Requirement 5)

Five corrections across two files, all verified against `cfn/master-template.yaml`:

**`docs/iam/ORCHESTRATION_ROLE_POLICY.md`:**
1. Update trust policy section to list all three trusted principals from the `AssumeRolePolicyDocument`:
   - `lambda.amazonaws.com`
   - `states.amazonaws.com`
   - `apigateway.amazonaws.com`
2. Add documentation for 6 missing policy statements. The master template defines 22 policies total; the doc currently covers only 16. Missing policies:
   - `CloudWatchLogsAccess` — CreateLogGroup, CreateLogStream, DescribeLogGroups, DescribeLogStreams, PutLogEvents, GetLogEvents, FilterLogEvents (for API Gateway access logging)
   - `LicenseManagerAccess` — ListLicenseConfigurations (for DRS license queries)
   - `ResourceGroupsAccess` — ListGroups (for DRS resource organization)
   - `ELBAccess` — DescribeLoadBalancers (for DRS load balancer integration)
   - `SQSAccess` — SendMessage, GetQueueAttributes scoped to `${ProjectName}-*` (for Lambda DLQ)
   - `ApiGatewayDeploymentAccess` — apigateway:GET, apigateway:POST on restapis (for deployment orchestrator)
3. Update SNS policy section. The master template `SNSAccess` policy has 8 actions total:
   - `sns:Publish`, `sns:Subscribe`, `sns:Unsubscribe`, `sns:ListSubscriptionsByTopic`, `sns:GetSubscriptionAttributes`, `sns:SetSubscriptionAttributes`, `sns:GetTopicAttributes`, `sns:ListTopics`
4. Update CloudWatch policy section. The master template `CloudWatchAccess` policy has 3 actions:
   - `cloudwatch:PutMetricData`, `cloudwatch:GetMetricStatistics`, `cloudwatch:GetMetricData`

**`docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md`:**
5. Change cross-account role name to `DRSOrchestrationRole`. Verified in master template `STSAccess` policy: resource is `arn:${AWS::Partition}:iam::*:role/DRSOrchestrationRole`

### Component 6: API Endpoint Documentation (Requirement 6)

Updates to `docs/reference/API_ENDPOINTS_CURRENT.md`:

1. Add "Server Launch Configuration" section with 5 endpoints (GET/PUT per-server config, GET/PUT group launch config, validate config)
2. Add "Staging Account Management" section with 6 endpoints (CRUD for staging accounts, discover, refresh)
3. Add "Capacity Queries" section with 2 endpoints (get DRS account capacity, get recovery capacity)
4. Add config validation endpoint
5. Add `GET /drs/tag-sync` alongside existing `POST /drs/tag-sync`
6. Add "Defined but Not Implemented" section listing ~20 DRS infrastructure endpoints in CFN that have no handler code
7. Correct the endpoint count from 44 to ~35 implemented, noting the additional ~20 defined-but-unimplemented

### Component 7: Deployment Script Reference Fixes (Requirement 7)

`./scripts/local-deploy.sh` is an old reference to what is now `./scripts/deploy.sh`. Simple find-and-replace in two files:

| File | Old Reference | New Reference |
|---|---|---|
| `docs/deployment/QUICK_START_GUIDE.md` | `./scripts/local-deploy.sh` | `./scripts/deploy.sh` |
| `docs/guides/DEVELOPER_GUIDE.md` | `./scripts/local-deploy.sh` | `./scripts/deploy.sh` |

## Data Models

No data model changes. This is a documentation-only spec.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Since this is a documentation-only spec, correctness properties focus on verifiable invariants between the documentation and the codebase. These can be implemented as automated checks (Python scripts or tests) that parse documentation files and cross-reference them against the actual project structure.

### Property 1: All README relative links resolve to existing files

*For any* relative Markdown link `[text](path)` in `README.md`, the referenced file path SHALL exist in the repository.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: All Lambda handler directories are documented

*For any* subdirectory under `lambda/` (excluding `shared/`), the directory name SHALL appear in `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 3: All production shared modules are documented

*For any* `.py` file in `lambda/shared/` (excluding `__init__.py` and files prefixed with `test_`), the module name SHALL appear in `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`.

**Validates: Requirements 4.1, 4.2**

### Property 4: Architecture doc stack count matches master template

*For any* version of the repository, the nested stack count stated in `docs/architecture/ARCHITECTURE.md` SHALL equal the number of `AWS::CloudFormation::Stack` resources defined in `cfn/master-template.yaml` (currently 14 nested stacks).

**Validates: Requirements 2.3**

## Error Handling

Not applicable. This spec involves only Markdown file edits. There are no runtime error conditions, API responses, or exception flows to handle.

If a documentation file referenced in this spec does not exist at implementation time (e.g., it was renamed or deleted), the implementer should flag it and skip that correction rather than creating incorrect content.

## Testing Strategy

### Unit Tests (Example-Based)

Spot-check tests to verify specific corrections were applied:

- Verify `docs/architecture/ARCHITECTURE.md` contains "WAFStack" and "us-east-1"
- Verify `docs/architecture/ARCHITECTURE.md` does not list `cross-account-role-stack.yaml` as a nested stack
- Verify `docs/architecture/ARCHITECTURE.md` uses "SourceBucket" not "DeploymentBucket" as a parameter name
- Verify `docs/iam/ORCHESTRATION_ROLE_POLICY.md` mentions `states.amazonaws.com` and `apigateway.amazonaws.com` as trusted principals
- Verify `docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md` contains "DRSOrchestrationRole"
- Verify `docs/reference/API_ENDPOINTS_CURRENT.md` contains "launch-config" or equivalent endpoint paths
- Verify `docs/deployment/QUICK_START_GUIDE.md` does not contain "local-deploy.sh"
- Verify `docs/guides/DEVELOPER_GUIDE.md` does not contain "local-deploy.sh"

### Property-Based Tests

Use `pytest` with `hypothesis` (already in the project's dev dependencies) for the 4 correctness properties:

- **Property 1**: Parse all `[text](path)` links from README.md, verify each relative path resolves to an existing file
- **Property 2**: List `lambda/*/` directories, verify each appears in LAMBDA_HANDLERS_ARCHITECTURE.md
- **Property 3**: List `lambda/shared/*.py` files (excluding `__init__.py` and `test_*`), verify each appears in LAMBDA_HANDLERS_ARCHITECTURE.md
- **Property 4**: Count `AWS::CloudFormation::Stack` resources in master-template.yaml, compare to the number stated in ARCHITECTURE.md

Note: Properties 2, 3, and 4 are deterministic cross-reference checks rather than randomized property tests. They don't benefit from hypothesis generators since the inputs are fixed (the actual files in the repo). They should be implemented as standard pytest assertions. Property 1 is similarly deterministic. All four are best implemented as parameterized pytest tests using `@pytest.mark.parametrize` over the actual file/directory listings.

**Test Configuration:**
- Framework: `pytest`
- Location: `tests/unit/test_documentation_accuracy.py`
- Tag format: **Feature: documentation-accuracy-audit, Property {number}: {property_text}**
- Run with: `.venv/bin/pytest tests/unit/test_documentation_accuracy.py -v`
