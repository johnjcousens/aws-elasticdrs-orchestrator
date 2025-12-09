# CodeBuild & CodeCommit Migration Plan

**Version:** 1.0  
**Date:** January 2025  
**Status:** Ready for Implementation  
**Estimated Effort:** 1-2 weeks

---

## Executive Summary

### Current State

- **Source Control**: GitHub (local) + GitLab (code.aws.dev)
- **CI/CD**: GitLab CI/CD with 6-stage pipeline
- **Deployment**: Manual sync script + GitLab automation
- **Artifacts**: S3 bucket (`aws-drs-orchestration`)

### Target State

- **Source Control**: CodeCommit (primary) + GitLab mirror (optional)
- **CI/CD**: CodePipeline + CodeBuild
- **Deployment**: Automated via CodePipeline
- **Artifacts**: S3 bucket (same)

### Migration Strategy

**Hybrid Approach**: Maintain GitLab as development repository, mirror to CodeCommit, use CodePipeline for AWS-native deployments.

### Business Value

- **AWS-Native Integration**: Seamless integration with AWS services
- **Cost Optimization**: No external CI/CD costs
- **Security**: IAM-based access control, no external credentials
- **Proven Pattern**: Leverage archived DR orchestrator pipeline architecture
- **Compliance**: All code and artifacts within AWS boundary

---

## Architecture Analysis

### Archived DR Orchestrator Pipeline

The archived solution (`archive/dr-orchestration-artifacts/pipeline.yaml`) provides a proven CodePipeline pattern:

**Key Components:**
- **CodeCommit Source**: Triggers on main branch commits
- **Self-Updating Pipeline**: Updates itself via CloudFormation
- **CodeBuild Projects**: Separate projects for scanning, packaging, deployment
- **Multi-Stage Deployment**: Dev → Stage → Prod with manual approvals
- **Cross-Account Support**: Deploys to multiple AWS accounts
- **CloudWatch Dashboards**: Automated dashboard deployment

**Pipeline Stages:**
1. CodeCommit-Source
2. Apply-CodeBuild-Updates (self-update)
3. Apply-Pipeline-Changes (self-update)
4. Scan-Templates (cfn-lint)
5. Build-Module-Lambda-Package
6. Build-Other-Lambda-Packages
7. Deploy-Other-Lambda-Stage
8. Deploy-Other-Lambda-Prod
9. Deploy-DR-Orchestrator-Dev
10. Approval-to-update-prod-copy (manual)
11. Deploy-DR-Orchestrator-Prod

### Current GitLab CI/CD Pipeline

**Stages:**
1. validate (CloudFormation + TypeScript)
2. lint (Python + Frontend)
3. build (Lambda + Frontend)
4. test (disabled - tests not in git)
5. deploy-infra (S3 upload + CloudFormation)
6. deploy-frontend (S3 + CloudFront)

**Key Features:**
- ECR Public images (avoids Docker Hub rate limits)
- Individual Lambda package builds
- Frontend build with Vite
- Automated aws-config.js generation
- CloudFront invalidation

---

## Migration Architecture

### Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitLab (code.aws.dev)                     │
│                  Development Repository                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ (Option 1: Mirror)
                         │ (Option 2: Webhook)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      AWS CodeCommit                          │
│                   Primary AWS Repository                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ (trigger on commit)
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                     AWS CodePipeline                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Source → Validate → Build → Deploy → Frontend        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼───────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  CodeBuild    │ │ CodeBuild   │ │ CodeBuild   │
│  Validate     │ │ Build       │ │ Deploy      │
└───────────────┘ └─────────────┘ └─────────────┘
        │                │                │
        └────────────────┴────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                  S3 Deployment Bucket                        │
│              aws-drs-orchestration                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: CodeCommit Setup (Week 1, Days 1-2)

#### 1.1 Create CodeCommit Repository

```bash
# Create repository
aws codecommit create-repository \
  --repository-name drs-orchestration \
  --repository-description "AWS DRS Orchestration Solution" \
  --region us-east-1

# Get clone URL
aws codecommit get-repository \
  --repository-name drs-orchestration \
  --query 'repositoryMetadata.cloneUrlHttp' \
  --output text
```

#### 1.2 Configure Git Credentials

```bash
# Install git-remote-codecommit
pip install git-remote-codecommit

# Add CodeCommit as remote
cd /Users/jocousen/Library/CloudStorage/OneDrive-amazon.com/DOCUMENTS/CODE/GITHUB/AWS-DRS-Orchestration
git remote add codecommit codecommit://drs-orchestration

# Push to CodeCommit
git push codecommit main
```

#### 1.3 Setup GitLab Mirror (Optional)

**In GitLab (code.aws.dev):**
1. Settings → Repository → Mirroring repositories
2. Git repository URL: `codecommit://drs-orchestration`
3. Mirror direction: Push
4. Authentication: AWS IAM credentials
5. Enable "Mirror only protected branches"

---

### Phase 2: CodeBuild Projects (Week 1, Days 3-5)

#### 2.1 Create Validation CodeBuild Project

Create `cfn/codebuild-validate.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for validation'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'

Resources:
  ValidateProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-validate'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/python:3.12
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              commands:
                - pip install cfn-lint==1.42.0 awscli
            build:
              commands:
                - echo "Validating CloudFormation templates..."
                - cfn-lint --config-file .cfnlintrc.yaml cfn/*.yaml
                - |
                  for template in cfn/*.yaml; do
                    echo "Validating $template"
                    aws cloudformation validate-template --template-body file://$template
                  done
                - echo "Validation complete"

  CodeBuildRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess'
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:PutObject'
                Resource: 'arn:aws:s3:::aws-drs-orchestration/*'
              - Effect: Allow
                Action:
                  - 'cloudformation:ValidateTemplate'
                Resource: '*'
```

#### 2.2 Create Build CodeBuild Project

Create `cfn/codebuild-build.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for building Lambda packages'

Resources:
  BuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-build'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/python:3.12
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              commands:
                - apt-get update && apt-get install -y zip
            build:
              commands:
                - echo "Building Lambda packages..."
                - cd lambda
                - |
                  if [ ! -d "package" ]; then
                    pip install -r requirements.txt -t package/ --no-cache-dir
                  fi
                - |
                  # Package api-handler
                  cd package && zip -r ../api-handler.zip . -x "*.pyc" "__pycache__/*" && cd ..
                  zip -g api-handler.zip index.py
                  
                  # Package orchestration-stepfunctions
                  cd package && zip -r ../orchestration-stepfunctions.zip . -x "*.pyc" "__pycache__/*" && cd ..
                  zip -g orchestration-stepfunctions.zip orchestration_stepfunctions.py
                  
                  # Package execution-finder
                  cd package && zip -r ../execution-finder.zip . -x "*.pyc" "__pycache__/*" && cd ..
                  zip -g execution-finder.zip poller/execution_finder.py
                  
                  # Package execution-poller
                  cd package && zip -r ../execution-poller.zip . -x "*.pyc" "__pycache__/*" && cd ..
                  zip -g execution-poller.zip poller/execution_poller.py
                - ls -lh *.zip
          artifacts:
            files:
              - lambda/*.zip
              - cfn/**/*
```

#### 2.3 Create Frontend Build Project

Create `cfn/codebuild-frontend.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for frontend build'

Resources:
  FrontendBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-frontend-build'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/node:22-alpine
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              commands:
                - cd frontend
                - npm ci --prefer-offline
            build:
              commands:
                - echo "Building React frontend..."
                - npm run build
                - ls -lh dist/
          artifacts:
            files:
              - frontend/dist/**/*
```

---

### Phase 3: CodePipeline Setup (Week 2, Days 1-3)

#### 3.1 Create Pipeline CloudFormation Template

Create `cfn/pipeline.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'DRS Orchestration CI/CD Pipeline'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'
  DeploymentBucket:
    Type: String
    Default: 'aws-drs-orchestration'
  AdminEmail:
    Type: String

Resources:
  # S3 Bucket for Pipeline Artifacts
  PipelineArtifactBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-pipeline-artifacts'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  # CodePipeline
  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      Name: !Sub '${ProjectName}-pipeline'
      RoleArn: !GetAtt PipelineRole.Arn
      ArtifactStore:
        Type: S3
        Location: !Ref PipelineArtifactBucket
      Stages:
        # Stage 1: Source
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeCommit
                Version: '1'
              Configuration:
                RepositoryName: !Ref ProjectName
                BranchName: main
              OutputArtifacts:
                - Name: SourceOutput

        # Stage 2: Validate
        - Name: Validate
          Actions:
            - Name: ValidateCloudFormation
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Sub '${ProjectName}-validate'
              InputArtifacts:
                - Name: SourceOutput

        # Stage 3: Build
        - Name: Build
          Actions:
            - Name: BuildLambda
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Sub '${ProjectName}-build'
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: LambdaArtifacts
            
            - Name: BuildFrontend
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Sub '${ProjectName}-frontend-build'
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: FrontendArtifacts

        # Stage 4: Deploy Infrastructure
        - Name: DeployInfrastructure
          Actions:
            - Name: UploadArtifacts
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: S3
                Version: '1'
              Configuration:
                BucketName: !Ref DeploymentBucket
                Extract: true
              InputArtifacts:
                - Name: LambdaArtifacts
            
            - Name: DeployCloudFormation
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: CloudFormation
                Version: '1'
              Configuration:
                ActionMode: CREATE_UPDATE
                StackName: !Sub '${ProjectName}-dev'
                TemplatePath: SourceOutput::cfn/master-template.yaml
                Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM
                RoleArn: !GetAtt CloudFormationRole.Arn
                ParameterOverrides: !Sub |
                  {
                    "ProjectName": "${ProjectName}",
                    "Environment": "dev",
                    "SourceBucket": "${DeploymentBucket}",
                    "AdminEmail": "${AdminEmail}"
                  }
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: StackOutputs

        # Stage 5: Deploy Frontend
        - Name: DeployFrontend
          Actions:
            - Name: DeployToS3
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: S3
                Version: '1'
              Configuration:
                BucketName: !GetAtt StackOutputs.FrontendBucketName
                Extract: true
              InputArtifacts:
                - Name: FrontendArtifacts

  # IAM Roles
  PipelineRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/AWSCodePipelineFullAccess'
        - 'arn:aws:iam::aws:policy/AWSCodeBuildAdminAccess'
        - 'arn:aws:iam::aws:policy/AWSCodeCommitReadOnly'
      Policies:
        - PolicyName: PipelinePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 's3:*'
                  - 'cloudformation:*'
                Resource: '*'

  CloudFormationRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: cloudformation.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/AdministratorAccess'
```

---

### Phase 4: Migration Execution (Week 2, Days 4-5)

#### 4.1 Deploy CodeBuild Projects

```bash
# Deploy validation project
aws cloudformation deploy \
  --template-file cfn/codebuild-validate.yaml \
  --stack-name drs-orchestration-codebuild-validate \
  --capabilities CAPABILITY_IAM

# Deploy build project
aws cloudformation deploy \
  --template-file cfn/codebuild-build.yaml \
  --stack-name drs-orchestration-codebuild-build \
  --capabilities CAPABILITY_IAM

# Deploy frontend build project
aws cloudformation deploy \
  --template-file cfn/codebuild-frontend.yaml \
  --stack-name drs-orchestration-codebuild-frontend \
  --capabilities CAPABILITY_IAM
```

#### 4.2 Deploy CodePipeline

```bash
aws cloudformation deploy \
  --template-file cfn/pipeline.yaml \
  --stack-name drs-orchestration-pipeline \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    DeploymentBucket=aws-drs-orchestration \
    AdminEmail=admin@example.com \
  --capabilities CAPABILITY_IAM
```

#### 4.3 Test Pipeline

```bash
# Trigger pipeline manually
aws codepipeline start-pipeline-execution \
  --name drs-orchestration-pipeline

# Monitor execution
aws codepipeline get-pipeline-state \
  --name drs-orchestration-pipeline
```

---

## Comparison: GitLab CI/CD vs CodePipeline

| Feature | GitLab CI/CD | CodePipeline + CodeBuild |
|---------|--------------|--------------------------|
| **Cost** | Free (self-hosted) | ~$1/month per pipeline + build minutes |
| **Integration** | External | Native AWS |
| **Credentials** | AWS keys in GitLab | IAM roles (no keys) |
| **Artifacts** | GitLab artifacts | S3 |
| **Approval Gates** | Manual jobs | Manual approval actions |
| **Multi-Account** | Requires AWS keys | Cross-account IAM roles |
| **Monitoring** | GitLab UI | CloudWatch + CodePipeline console |
| **Self-Updating** | No | Yes (pipeline updates itself) |

---

## Migration Checklist

### Pre-Migration
- [ ] Review archived DR orchestrator pipeline pattern
- [ ] Document current GitLab CI/CD workflows
- [ ] Identify GitLab-specific features in use
- [ ] Plan downtime window (if needed)

### CodeCommit Setup
- [ ] Create CodeCommit repository
- [ ] Configure Git credentials
- [ ] Push code to CodeCommit
- [ ] Setup GitLab mirror (optional)
- [ ] Test clone/push/pull operations

### CodeBuild Setup
- [ ] Create validation CodeBuild project
- [ ] Create build CodeBuild project
- [ ] Create frontend build project
- [ ] Test each project independently
- [ ] Verify artifacts in S3

### CodePipeline Setup
- [ ] Create pipeline CloudFormation template
- [ ] Deploy pipeline stack
- [ ] Configure manual approval gates
- [ ] Test end-to-end pipeline execution
- [ ] Verify CloudFormation deployment

### Post-Migration
- [ ] Update documentation
- [ ] Train team on CodePipeline
- [ ] Monitor first production deployment
- [ ] Decommission GitLab CI/CD (optional)
- [ ] Archive GitLab pipeline configuration

---

## Rollback Plan

If migration fails:

1. **Immediate**: Continue using GitLab CI/CD (no changes to existing pipeline)
2. **CodeCommit**: Keep as mirror, revert to GitHub/GitLab as primary
3. **CodePipeline**: Delete pipeline stack, no impact on deployments
4. **CodeBuild**: Delete projects, no dependencies

**Recovery Time**: <1 hour (GitLab CI/CD remains functional throughout migration)

---

## Cost Analysis

### Current (GitLab CI/CD)
- GitLab: $0 (self-hosted on code.aws.dev)
- AWS: S3 storage only (~$5/month)
- **Total**: ~$5/month

### Proposed (CodePipeline + CodeBuild)
- CodePipeline: $1/month per active pipeline
- CodeBuild: $0.005/minute (estimated 100 minutes/month = $0.50)
- S3 storage: ~$5/month
- **Total**: ~$6.50/month

**Additional Cost**: ~$1.50/month

---

## Success Metrics

- **Pipeline Execution Time**: <15 minutes (same as GitLab)
- **Deployment Success Rate**: >95%
- **Mean Time to Deploy**: <20 minutes
- **Pipeline Availability**: >99.9%
- **Cost**: <$10/month

---

## References

- [Archived DR Orchestrator Pipeline](../archive/dr-orchestration-artifacts/pipeline.yaml)
- [Current GitLab CI/CD](.gitlab-ci.yml)
- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)
- [AWS CodeCommit Documentation](https://docs.aws.amazon.com/codecommit/)
