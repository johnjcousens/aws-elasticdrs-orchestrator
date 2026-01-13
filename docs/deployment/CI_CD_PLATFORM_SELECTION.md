# CI/CD Platform Selection: AWS Native vs GitHub Actions

> **STATUS: DECISION IMPLEMENTED** - GitHub Actions was selected and implemented as the CI/CD platform in January 2026 (v1.3.0). See [GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md) for current implementation details.

## Executive Summary

This document analyzes the feasibility of implementing CI/CD for the AWS DRS Orchestration platform using either AWS native tools (CodeCommit/CodePipeline/CodeBuild) or GitHub Actions, with a proposed CloudFormation parameter to select the deployment approach.

### Decision Outcome

**Selected Platform**: GitHub Actions with OIDC authentication

**Rationale**:
- Eliminates circular dependency issues (pipeline updating its own CloudFormation stack)
- Native Git integration without CodeCommit mirroring
- Superior developer experience with PR workflows and code review
- OIDC authentication provides secure AWS access without long-lived credentials
- Simpler architecture and easier debugging

**Implementation**: `.github/workflows/deploy.yml` with `cfn/github-oidc-stack.yaml` for IAM role setup

## Current State Analysis

> **Note**: This section describes the historical AWS Native CI/CD pipeline that was replaced by GitHub Actions in January 2026.

### Historical AWS Native CI/CD Pipeline (Deprecated)

**Active Infrastructure:**
- **Pipeline**: `aws-elasticdrs-orchestrator-pipeline-dev`
- **Repository**: CodeCommit (`aws-elasticdrs-orchestrator-dev`)
- **Account**: 777788889999
- **Deployment Bucket**: `aws-elasticdrs-orchestrator`

**Pipeline Stages (7 stages, ~15-20 minutes):**
1. **Source** (~30s) - CodeCommit retrieval
2. **Validate** (~2-3min) - CloudFormation validation, Python linting, TypeScript checking
3. **SecurityScan** (~3-4min) - Bandit, Semgrep, Safety, npm audit
4. **Build** (~4-5min) - Lambda packaging, frontend builds
5. **Test** (~3-4min) - Unit tests, integration tests, coverage
6. **DeployInfrastructure** (~8-10min) - CloudFormation deployment
7. **DeployFrontend** (~2-3min) - S3 sync, CloudFront invalidation

**BuildSpec Files:**
- `validate-buildspec.yml` - Template validation and code quality
- `security-buildspec.yml` - Comprehensive security scanning
- `build-buildspec.yml` - Lambda and frontend builds
- `test-buildspec.yml` - Unit and integration tests
- `deploy-infra-buildspec.yml` - Infrastructure deployment
- `deploy-frontend-buildspec.yml` - Frontend deployment with dynamic config

## Platform Comparison

### AWS Native Tools (Current)

**Advantages:**
- ✅ **Native Integration**: Seamless AWS service integration
- ✅ **IAM Security**: Native role-based access with least privilege
- ✅ **VPC Support**: Can run in private subnets for enhanced security
- ✅ **Cost Efficiency**: Pay-per-use pricing model
- ✅ **Enterprise Ready**: Built for AWS workloads
- ✅ **Artifact Management**: Native S3 integration for build artifacts
- ✅ **CloudWatch Integration**: Native logging and monitoring

**Disadvantages:**
- ❌ **Vendor Lock-in**: AWS-specific tooling
- ❌ **Limited Ecosystem**: Smaller community compared to GitHub
- ❌ **Learning Curve**: AWS-specific concepts and configurations
- ❌ **Git Limitations**: CodeCommit lacks advanced Git features

**Cost Estimate (Monthly):**
- CodeBuild: $5-15 (based on build minutes)
- CodePipeline: $1 per active pipeline
- CodeCommit: $1-3 (based on users/requests)
- **Total: $7-19/month**

### GitHub Actions

**Advantages:**
- ✅ **Ecosystem**: Massive marketplace of actions and integrations
- ✅ **Developer Experience**: Superior Git features, PR workflows, code review
- ✅ **Community**: Large community, extensive documentation
- ✅ **Flexibility**: Supports any cloud provider or deployment target
- ✅ **Matrix Builds**: Parallel execution across multiple environments
- ✅ **Secrets Management**: Built-in secrets management
- ✅ **Free Tier**: 2,000 minutes/month for public repos

**Disadvantages:**
- ❌ **External Dependency**: Relies on GitHub infrastructure
- ❌ **Security Complexity**: Requires OIDC or long-lived credentials for AWS
- ❌ **Network Latency**: External service may have higher latency
- ❌ **Cost Scaling**: Can become expensive for private repos with heavy usage

**Cost Estimate (Monthly):**
- GitHub Actions: $0-50 (based on usage, private repo minutes)
- **Total: $0-50/month**

## Proposed Solution Architecture

### CloudFormation Parameter-Driven Deployment

```yaml
Parameters:
  CiCdPlatform:
    Type: String
    Default: "AWS_NATIVE"
    AllowedValues:
      - "AWS_NATIVE"
      - "GITHUB_ACTIONS"
      - "EXTERNAL_CI_CD"
    Description: "Select CI/CD platform for deployment automation"

Conditions:
  DeployAwsNativeCiCd: !Equals [!Ref CiCdPlatform, "AWS_NATIVE"]
  DeployExternalCiCd: !Or 
    - !Equals [!Ref CiCdPlatform, "GITHUB_ACTIONS"]
    - !Equals [!Ref CiCdPlatform, "EXTERNAL_CI_CD"]
```

### Architecture Options

#### Option 1: AWS Native CI/CD Stack
```yaml
Resources:
  # Deploy when CiCdPlatform = "AWS_NATIVE"
  CodeCommitRepository: !If [DeployAwsNativeCiCd, !Ref CodeCommitStack, !Ref "AWS::NoValue"]
  CodePipelineStack: !If [DeployAwsNativeCiCd, !Ref PipelineStack, !Ref "AWS::NoValue"]
  CodeBuildProjects: !If [DeployAwsNativeCiCd, !Ref BuildStack, !Ref "AWS::NoValue"]
```

#### Option 2: External CI/CD Integration Stack
```yaml
Resources:
  # Deploy when CiCdPlatform = "GITHUB_ACTIONS" or "EXTERNAL_CI_CD"
  CiCdServiceUser: !If [DeployExternalCiCd, !Ref CiCdUser, !Ref "AWS::NoValue"]
  CiCdServiceRole: !If [DeployExternalCiCd, !Ref CiCdRole, !Ref "AWS::NoValue"]
  OidcProvider: !If [DeployExternalCiCd, !Ref GitHubOidcProvider, !Ref "AWS::NoValue"]
```

## GitHub Actions Implementation

**Inspired by HealthEdge Test Synth Pipeline patterns:**

### Advanced Workflow Structure

```yaml
# .github/workflows/deploy.yml
name: Deploy AWS DRS Orchestration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    outputs:
      secrets_found: ${{ steps.secrets.outputs.secrets_found }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Detect Secrets
        id: secrets
        run: |
          pip install detect-secrets
          detect-secrets scan --all-files --baseline .secrets.baseline
          echo "secrets_found=false" >> $GITHUB_OUTPUT
      
      - name: Security Scan
        run: |
          pip install bandit semgrep safety
          bandit -r lambda/ -ll
          semgrep --config=auto lambda/
          safety scan

  detect-changes:
    runs-on: ubuntu-latest
    needs: security-scan
    outputs:
      cfn_files: ${{ steps.changes.outputs.cfn_files }}
      lambda_files: ${{ steps.changes.outputs.lambda_files }}
      has_changes: ${{ steps.changes.outputs.has_changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Detect CloudFormation Changes
        id: changes
        run: |
          # Smart change detection for CloudFormation templates
          CFN_FILES=$(git diff --name-only origin/main...HEAD | grep 'cfn/.*\.yaml$' | jq -R -s -c 'split("\n")[:-1]')
          LAMBDA_FILES=$(git diff --name-only origin/main...HEAD | grep 'lambda/.*\.py$' | jq -R -s -c 'split("\n")[:-1]')
          
          echo "cfn_files=$CFN_FILES" >> $GITHUB_OUTPUT
          echo "lambda_files=$LAMBDA_FILES" >> $GITHUB_OUTPUT
          echo "has_changes=$([ "$CFN_FILES" != "[]" ] || [ "$LAMBDA_FILES" != "[]" ] && echo true || echo false)" >> $GITHUB_OUTPUT

  validate-templates:
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.has_changes == 'true'
    strategy:
      matrix:
        template: ${{ fromJson(needs.detect-changes.outputs.cfn_files) }}
      max-parallel: 2
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup AWS Environment
        uses: ./.github/actions/setup-aws-environment
        with:
          aws-role-arn: ${{ secrets.AWS_ROLE_ARN }}
          deployment-bucket: ${{ secrets.DEPLOYMENT_BUCKET }}
      
      - name: Validate CloudFormation
        uses: ./.github/actions/validate-cloudformation
        with:
          template-file: ${{ matrix.template }}
          stack-name: aws-elasticdrs-orchestrator-dev

  test-lambda:
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.has_changes == 'true'
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Run Lambda Tests
        run: |
          cd tests/python
          python -m pytest unit/ -v --cov=../../lambda --cov-report=term-missing

  deploy-infrastructure:
    needs: [validate-templates, test-lambda]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && needs.detect-changes.outputs.has_changes == 'true'
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup AWS Environment
        uses: ./.github/actions/setup-aws-environment
        with:
          aws-role-arn: ${{ secrets.AWS_ROLE_ARN }}
          deployment-bucket: ${{ secrets.DEPLOYMENT_BUCKET }}
      
      - name: Deploy CloudFormation
        run: |
          aws cloudformation deploy \
            --template-file cfn/master-template.yaml \
            --stack-name aws-elasticdrs-orchestrator-dev \
            --parameter-overrides \
              ProjectName=aws-elasticdrs-orchestrator \
              Environment=dev \
              SourceBucket=${{ secrets.DEPLOYMENT_BUCKET }} \
              CiCdPlatform=GITHUB_ACTIONS \
            --capabilities CAPABILITY_NAMED_IAM

  validation-gate:
    runs-on: ubuntu-latest
    needs: [security-scan, detect-changes, validate-templates, test-lambda]
    if: always()
    steps:
      - name: Check All Jobs
        run: |
          if [[ "${{ needs.security-scan.result }}" == "failure" ]] || 
             [[ "${{ needs.validate-templates.result }}" == "failure" ]] || 
             [[ "${{ needs.test-lambda.result }}" == "failure" ]]; then
            echo "One or more validation jobs failed"
            exit 1
          fi
          echo "All validations passed"
```

### Composite Actions

```yaml
# .github/actions/setup-aws-environment/action.yml
name: 'Setup AWS Environment'
description: 'Configure AWS credentials and environment'
inputs:
  aws-role-arn:
    description: 'AWS IAM Role ARN for OIDC'
    required: true
  aws-region:
    description: 'AWS Region'
    required: true
    default: 'us-east-1'
  deployment-bucket:
    description: 'S3 Deployment Bucket'
    required: true

runs:
  using: 'composite'
  steps:
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        role-to-assume: ${{ inputs.aws-role-arn }}
        aws-region: ${{ inputs.aws-region }}
    
    - name: Verify AWS Access
      shell: bash
      run: |
        aws sts get-caller-identity
        aws s3 ls s3://${{ inputs.deployment-bucket }}/ > /dev/null
```

```yaml
# .github/actions/validate-cloudformation/action.yml
name: 'Validate CloudFormation'
description: 'Validate CloudFormation templates with diff generation'
inputs:
  template-file:
    description: 'CloudFormation template file path'
    required: true
  stack-name:
    description: 'CloudFormation stack name for diff'
    required: false

outputs:
  validation-status:
    description: 'Template validation status'
    value: ${{ steps.validate.outputs.status }}
  has-changes:
    description: 'Whether template has changes'
    value: ${{ steps.diff.outputs.has_changes }}

runs:
  using: 'composite'
  steps:
    - name: Install Tools
      shell: bash
      run: |
        pip install cfn-lint
    
    - name: Validate Template
      id: validate
      shell: bash
      run: |
        cfn-lint ${{ inputs.template-file }}
        aws cloudformation validate-template --template-body file://${{ inputs.template-file }}
        echo "status=success" >> $GITHUB_OUTPUT
    
    - name: Generate Diff
      id: diff
      if: inputs.stack-name != ''
      shell: bash
      run: |
        if aws cloudformation describe-stacks --stack-name ${{ inputs.stack-name }} > /dev/null 2>&1; then
          echo "Stack exists, generating diff..."
          # CloudFormation change set for diff
          aws cloudformation create-change-set \
            --stack-name ${{ inputs.stack-name }} \
            --template-body file://${{ inputs.template-file }} \
            --change-set-name github-actions-diff-$(date +%s) \
            --capabilities CAPABILITY_NAMED_IAM || true
          echo "has_changes=true" >> $GITHUB_OUTPUT
        else
          echo "Stack does not exist, will be created"
          echo "has_changes=true" >> $GITHUB_OUTPUT
        fi
```

### Key Enhancements from HealthEdge Pattern

### Key Enhancements from HealthEdge Pattern

**Configuration-Driven Deployment:**
- YAML configuration files drive infrastructure deployment
- Auto-generated stack names from config values
- Environment-specific account mapping via JSON configuration

**Advanced Pipeline Features:**
- **Matrix Strategy**: Parallel validation of CloudFormation templates (max 2 concurrent)
- **Smart Change Detection**: Only validate affected files based on git diff
- **Environment Gates**: Different deployment rules for dev/nonprod/prod environments
- **Resource Grouping**: Map templates to deployment stages via configuration

**Security & Compliance:**
- **Secret Scanning**: Prevents credential leaks before merge using `detect-secrets`
- **CloudFormation Guard**: Compliance checks against security policies
- **Validation Gate**: Final job that blocks merge on any failure
- **Construct Protection**: Prevents deletion of critical infrastructure components

**Deployment Strategy:**
- **Environment Detection**: Automatic AWS account selection based on config
- **Pre-deployment Diff**: CloudFormation change sets show deployment impact
- **Parallel Deployment**: Group configurations by environment for efficient deployment
- **Status Reporting**: Automated PR comments with detailed validation results

**Configuration Structure for AWS DRS:**
```yaml
# config/drs-orchestration-dev.yaml
globals:
  cdk_action: deploy
  org_name: "aws-drs"
  project_name: "orchestration"
  environment: "dev"
  region: "us-east-1"
  deployment_bucket: "aws-elasticdrs-orchestrator"

resource_groups:
  core_infrastructure:
    template: "cfn/master-template.yaml"
    parameters:
      ProjectName: "aws-elasticdrs-orchestrator"
      Environment: "dev"
      CiCdPlatform: "GITHUB_ACTIONS"
  
  security_stack:
    template: "cfn/security-stack.yaml"
    depends_on: ["core_infrastructure"]
    parameters:
      EnableWAF: true
      EnableCloudTrail: true
```

### Security Implementation

#### OIDC Provider Setup (Recommended)
```yaml
# CloudFormation template for GitHub OIDC
GitHubOidcProvider:
  Type: AWS::IAM::OIDCIdentityProvider
  Condition: DeployExternalCiCd
  Properties:
    Url: https://token.actions.githubusercontent.com
    ClientIdList:
      - sts.amazonaws.com
    ThumbprintList:
      - 6938fd4d98bab03faadb97b34396831e3780aea1

GitHubActionsRole:
  Type: AWS::IAM::Role
  Condition: DeployExternalCiCd
  Properties:
    AssumeRolePolicyDocument:
      Version: '2012-10-17'
      Statement:
        - Effect: Allow
          Principal:
            Federated: !Ref GitHubOidcProvider
          Action: sts:AssumeRole
          Condition:
            StringEquals:
              'token.actions.githubusercontent.com:aud': sts.amazonaws.com
            StringLike:
              'token.actions.githubusercontent.com:sub': 
                - 'repo:johnjcousens/aws-elasticdrs-orchestrator:ref:refs/heads/main'
                - 'repo:johnjcousens/aws-elasticdrs-orchestrator:pull_request'
```

#### Alternative: Service User with Access Keys
```yaml
CiCdServiceUser:
  Type: AWS::IAM::User
  Condition: DeployExternalCiCd
  Properties:
    UserName: !Sub "${ProjectName}-cicd-user"
    Policies:
      - PolicyName: CiCdDeploymentPolicy
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - cloudformation:*
                - s3:*
                - lambda:*
                - apigateway:*
              Resource: "*"

CiCdAccessKey:
  Type: AWS::IAM::AccessKey
  Condition: DeployExternalCiCd
  Properties:
    UserName: !Ref CiCdServiceUser

CiCdSecretKey:
  Type: AWS::SecretsManager::Secret
  Condition: DeployExternalCiCd
  Properties:
    Name: !Sub "${ProjectName}-cicd-credentials"
    SecretString: !Sub |
      {
        "AccessKeyId": "${CiCdAccessKey}",
        "SecretAccessKey": "${CiCdAccessKey.SecretAccessKey}"
      }
```

## Migration Strategy

### Phase 1: Parallel Implementation (2-3 weeks)
1. **Create GitHub Actions workflows** based on existing BuildSpecs
2. **Implement OIDC provider** in CloudFormation template
3. **Add CiCdPlatform parameter** to master template
4. **Test GitHub Actions pipeline** in development environment

### Phase 2: Feature Parity (1-2 weeks)
1. **Security scanning** - Port all security tools to GitHub Actions
2. **Test coverage** - Ensure identical test execution
3. **Artifact management** - Implement S3 artifact storage
4. **Deployment validation** - Verify identical deployment outcomes

### Phase 3: Production Deployment (1 week)
1. **Documentation update** - Update deployment guides
2. **Team training** - GitHub Actions workflow training
3. **Gradual migration** - Switch development environments first
4. **Production cutover** - Final migration with rollback plan

## Recommendations

### Implemented Solution: GitHub Actions

**Decision Made**: GitHub Actions was selected and implemented in January 2026 (v1.3.0).

**Implementation Details**:
- **Workflow File**: `.github/workflows/deploy.yml`
- **OIDC Stack**: `cfn/github-oidc-stack.yaml` (deploy separately)
- **Authentication**: OIDC-based (no long-lived credentials)
- **Repository**: GitHub (primary source of truth)

**Why GitHub Actions Was Chosen**:
1. **No Circular Dependencies**: Pipeline runs outside AWS, avoiding self-update issues
2. **Native Git Integration**: No CodeCommit mirroring required
3. **Better Developer Experience**: Superior PR workflows, code review, and collaboration
4. **OIDC Security**: Secure AWS access without storing credentials
5. **Simpler Architecture**: Easier to debug and maintain

**Deployment Commands**:
```bash
# Deploy OIDC stack (one-time setup)
aws cloudformation deploy \
  --template-file cfn/github-oidc-stack.yaml \
  --stack-name PROJECT-github-oidc \
  --parameter-overrides \
    ProjectName=PROJECT \
    Environment=ENV \
    GitHubOrg=YOUR_ORG \
    GitHubRepo=YOUR_REPO \
  --capabilities CAPABILITY_NAMED_IAM

# Then configure GitHub repository secrets and push to main branch
```

### Historical Reference: AWS Native Option

The AWS Native CI/CD option (CodeCommit/CodePipeline/CodeBuild) remains documented below for reference but is no longer the recommended approach due to circular dependency issues discovered during implementation.

### Implementation Priority (Completed)

| Priority | Component | Status | Notes |
|----------|-----------|--------|-------|
| 1 | **GitHub OIDC Stack** | ✅ Completed | `cfn/github-oidc-stack.yaml` |
| 2 | **GitHub Actions Workflow** | ✅ Completed | `.github/workflows/deploy.yml` |
| 3 | **Documentation** | ✅ Completed | `docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md` |
| 4 | **Legacy Deprecation** | ✅ Completed | `.gitlab-ci.yml` marked deprecated |

### Success Criteria

**Technical Requirements:**
- ✅ Identical deployment outcomes regardless of CI/CD platform
- ✅ Security scanning parity between platforms
- ✅ Test coverage maintained across all workflows
- ✅ Artifact management consistency

**Operational Requirements:**
- ✅ <20 minute total pipeline duration
- ✅ Automated rollback capabilities
- ✅ Comprehensive logging and monitoring
- ✅ Cost optimization (target <$20/month for CI/CD)

## Next Steps

> **All next steps have been completed as of January 2026.**

For current CI/CD setup and usage, see:
- [GitHub Actions CI/CD Guide](docs/guides/deployment/GITHUB_ACTIONS_CICD_GUIDE.md) - Complete GitHub Actions setup and usage
- [Fresh Deployment Guide](docs/guides/deployment/FRESH_DEPLOYMENT_GUIDE.md) - New environment deployment

## Conclusion

**GitHub Actions was selected and implemented** as the CI/CD platform for AWS DRS Orchestration in January 2026. This decision was driven by the need to eliminate circular dependency issues where the AWS Native pipeline would attempt to update the CloudFormation stack containing itself.

The implementation provides:
- ✅ OIDC-based secure AWS authentication
- ✅ 6-stage pipeline (~20 minutes total)
- ✅ Native Git integration without mirroring
- ✅ Superior developer experience
- ✅ Simpler architecture and debugging

The AWS Native CI/CD option documentation is retained for historical reference and for organizations that may prefer AWS-native tooling despite the circular dependency challenges.