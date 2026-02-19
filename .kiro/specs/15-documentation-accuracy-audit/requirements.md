# Requirements Document

## Introduction

The HRP DRS Tech Adapter project has accumulated documentation that has drifted from the actual deployed codebase. Broken links in the README, incorrect stack counts, undocumented Lambda handlers, missing API endpoints, wrong parameter names, and stale script references all reduce developer trust in the docs. This spec covers a documentation-only audit and correction pass — no code in `/lambda`, `/cfn`, or `/frontend` will be modified.

## Glossary

- **README**: The top-level `README.md` file in the repository root
- **Architecture_Doc**: The file `docs/architecture/ARCHITECTURE.md`
- **Lambda_Architecture_Doc**: The file `docs/architecture/LAMBDA_HANDLERS_ARCHITECTURE.md`
- **IAM_Policy_Doc**: The file `docs/iam/ORCHESTRATION_ROLE_POLICY.md`
- **IAM_Role_Spec_Doc**: The file `docs/reference/ORCHESTRATION_ROLE_SPECIFICATION.md`
- **API_Endpoints_Doc**: The file `docs/reference/API_ENDPOINTS_CURRENT.md`
- **Quick_Start_Doc**: The file `docs/deployment/QUICK_START_GUIDE.md`
- **Developer_Guide_Doc**: The file `docs/guides/DEVELOPER_GUIDE.md`
- **Master_Template**: The CloudFormation file `cfn/master-template.yaml`
- **Audit_System**: The set of documentation files being corrected in this spec

## Requirements

### Requirement 1: Fix Broken README Links

**User Story:** As a developer, I want all links in the README to resolve to existing files, so that I can navigate the documentation without hitting dead ends.

#### Acceptance Criteria

1. WHEN a developer follows a link in the README to `docs/analysis/LAMBDA_HANDLERS_COMPLETE_ANALYSIS.md`, THE Audit_System SHALL either create the referenced file or update the README link to point to an existing equivalent file
2. WHEN a developer follows a link in the README to `docs/api-reference/EXECUTION_HANDLER_API.md`, THE Audit_System SHALL either create the referenced file or update the README link to point to an existing equivalent file
3. WHEN a developer follows a link in the README to `docs/troubleshooting/ERROR_CODES.md`, THE Audit_System SHALL either create the referenced file or update the README link to point to an existing equivalent file
4. WHEN all README link fixes are complete, THE README SHALL contain zero links that reference non-existent files

### Requirement 2: Correct Architecture Document Stack Information

**User Story:** As a developer, I want the architecture document to accurately reflect the deployed CloudFormation stack structure, so that I can understand the system topology without cross-referencing the templates.

#### Acceptance Criteria

1. WHEN a developer reads the Architecture_Doc, THE Architecture_Doc SHALL list the WAFStack as a conditional nested stack deployed only in us-east-1
2. WHEN a developer reads the Architecture_Doc nested stack list, THE Architecture_Doc SHALL identify `cross-account-role-stack.yaml` and `github-oidc-stack.yaml` as standalone templates not deployed by the Master_Template
3. WHEN a developer reads the Architecture_Doc stack count, THE Architecture_Doc SHALL state the correct total of 14 nested stacks matching the Master_Template
4. WHEN a developer reads the Architecture_Doc parameter list, THE Architecture_Doc SHALL use the parameter name `SourceBucket` instead of the incorrect `DeploymentBucket`

### Requirement 3: Document Missing Lambda Handlers

**User Story:** As a developer, I want all Lambda handlers documented in the Lambda architecture doc, so that I can understand the full set of functions deployed in the stack.

#### Acceptance Criteria

1. WHEN a developer reads the Lambda_Architecture_Doc, THE Lambda_Architecture_Doc SHALL include documentation for the `dr-orchestration-stepfunction` handler covering its wave orchestration responsibilities
2. WHEN a developer reads the Lambda_Architecture_Doc, THE Lambda_Architecture_Doc SHALL include documentation for the `frontend-deployer` handler covering its S3 and CloudFront deployment responsibilities
3. WHEN a developer reads the Lambda_Architecture_Doc, THE Lambda_Architecture_Doc SHALL include documentation for the `drs-agent-deployer` handler and note its current disabled status in CloudFormation
4. WHEN a developer reads the Lambda_Architecture_Doc handler list, THE Lambda_Architecture_Doc SHALL document all 6 Lambda handlers deployed or defined in the stack

### Requirement 4: Document Missing Shared Modules

**User Story:** As a developer, I want all shared Lambda modules documented, so that I can discover reusable utilities without reading source code.

#### Acceptance Criteria

1. WHEN a developer reads the Lambda_Architecture_Doc shared modules section, THE Lambda_Architecture_Doc SHALL document the following modules: `config_merge.py`, `drs_regions.py`, `drs_utils.py`, `execution_utils.py`, `iam_utils.py`, `launch_config_validation.py`, `notifications.py`, `security_utils.py`, `staging_account_models.py`
2. WHEN a developer reads the Lambda_Architecture_Doc shared modules section, THE Lambda_Architecture_Doc SHALL document all production shared modules present in `lambda/shared/`

### Requirement 5: Correct IAM Documentation

**User Story:** As a developer, I want the IAM documentation to match the actual CloudFormation-defined policies, so that I can accurately assess permissions without reading the templates.

#### Acceptance Criteria

1. WHEN a developer reads the IAM_Policy_Doc trust policy section, THE IAM_Policy_Doc SHALL list Lambda, Step Functions, and API Gateway as trusted principals matching the Master_Template
2. WHEN a developer reads the IAM_Role_Spec_Doc cross-account role naming section, THE IAM_Role_Spec_Doc SHALL use the role name `DRSOrchestrationRole` matching the Master_Template
3. WHEN a developer reads the IAM_Policy_Doc policy list, THE IAM_Policy_Doc SHALL document the CloudWatch Logs, License Manager, Resource Groups, ELB, SQS, and API Gateway Deployment policies present in the Master_Template
4. WHEN a developer reads the IAM_Policy_Doc SNS policy section, THE IAM_Policy_Doc SHALL include all 8 subscription management actions defined in the Master_Template
5. WHEN a developer reads the IAM_Policy_Doc CloudWatch policy section, THE IAM_Policy_Doc SHALL include the `GetMetricData` action defined in the Master_Template

### Requirement 6: Correct API Endpoint Documentation

**User Story:** As a developer, I want the API endpoint documentation to reflect all implemented endpoints, so that I can integrate with the API without guessing at available routes.

#### Acceptance Criteria

1. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL document all 5 server launch configuration endpoints that are implemented in the codebase
2. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL document all 6 staging account management endpoints that are implemented in the codebase
3. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL document the 2 capacity query endpoints that are implemented in the codebase
4. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL document the config validation endpoint that is implemented in the codebase
5. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL document the GET method for `/drs/tag-sync` in addition to the existing POST documentation
6. WHEN a developer reads the API_Endpoints_Doc, THE API_Endpoints_Doc SHALL include a section noting the approximately 20 DRS infrastructure endpoints defined in CloudFormation but not yet implemented
7. WHEN a developer reads the API_Endpoints_Doc endpoint count, THE API_Endpoints_Doc SHALL state the correct count of approximately 35 implemented endpoints instead of the incorrect 44

### Requirement 7: Fix Deployment Script References

**User Story:** As a developer, I want deployment guides to reference the correct script paths, so that I can follow setup instructions without encountering missing files.

#### Acceptance Criteria

1. WHEN a developer reads the Quick_Start_Doc, THE Quick_Start_Doc SHALL reference `./scripts/deploy.sh` instead of the non-existent `./scripts/local-deploy.sh`
2. WHEN a developer reads the Developer_Guide_Doc, THE Developer_Guide_Doc SHALL reference `./scripts/deploy.sh` instead of the non-existent `./scripts/local-deploy.sh`
