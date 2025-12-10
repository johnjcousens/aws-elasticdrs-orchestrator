# CodeBuild & CodeCommit Migration Plan

**Version:** 1.1  
**Date:** December 2025  
**Status:** Ready for Implementation  
**Estimated Effort:** 4-6 working days

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
- **SSM Parameter Store**: Configuration stored in SSM (not hardcoded)
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

```text
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
│  Validate     │ │ Build       │ │ Deploy FE   │
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

### Phase 1: CodeCommit Setup (Day 1)

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
cd /path/to/AWS-DRS-Orchestration
git remote add codecommit codecommit://drs-orchestration

# Push to CodeCommit
git push codecommit main
```

#### 1.3 Setup SSM Parameters

Store configuration in SSM Parameter Store (following archived pipeline pattern):

```bash
# Create SSM parameters for pipeline configuration
aws ssm put-parameter \
  --name "/drs-orchestration/pipeline/deployment-bucket" \
  --value "aws-drs-orchestration" \
  --type String

aws ssm put-parameter \
  --name "/drs-orchestration/pipeline/admin-email" \
  --value "admin@example.com" \
  --type String

aws ssm put-parameter \
  --name "/drs-orchestration/pipeline/environment" \
  --value "dev" \
  --type String
```

#### 1.4 Setup GitLab Mirror (Optional)

**In GitLab (code.aws.dev):**

1. Settings → Repository → Mirroring repositories
2. Git repository URL: `codecommit://drs-orchestration`
3. Mirror direction: Push
4. Authentication: AWS IAM credentials
5. Enable "Mirror only protected branches"

---

### Phase 2: CodeBuild Projects (Days 2-3)

#### 2.1 Create Validation CodeBuild Project

Create `cfn/codebuild/codebuild-validate.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for CloudFormation and TypeScript validation'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'

Resources:
  ValidateProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-validate'
      Description: 'Validate CloudFormation templates and TypeScript'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/python:3.12
        EnvironmentVariables:
          - Name: AWS_DEFAULT_REGION
            Value: us-east-1
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec-validate.yml
      TimeoutInMinutes: 15
      LogsConfig:
        CloudWatchLogs:
          Status: ENABLED
          GroupName: !Sub '/codebuild/${ProjectName}-validate'

  CodeBuildRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-codebuild-validate-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'logs:CreateLogGroup'
                  - 'logs:CreateLogStream'
                  - 'logs:PutLogEvents'
                Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/codebuild/*'
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:GetObjectVersion'
                  - 's3:PutObject'
                Resource:
                  - !Sub 'arn:aws:s3:::${ProjectName}-pipeline-artifacts/*'
              - Effect: Allow
                Action:
                  - 'cloudformation:ValidateTemplate'
                Resource: '*'

Outputs:
  ProjectName:
    Value: !Ref ValidateProject
  ProjectArn:
    Value: !GetAtt ValidateProject.Arn
```

Create `buildspec-validate.yml` in repository root:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.12
      nodejs: 22
    commands:
      - pip install cfn-lint==1.42.0 awscli
      - cd frontend && npm ci --prefer-offline

  build:
    commands:
      - echo "=== Validating CloudFormation templates ==="
      - cfn-lint --config-file .cfnlintrc.yaml cfn/*.yaml
      - |
        for template in cfn/*.yaml; do
          echo "Validating $template with AWS CLI..."
          aws cloudformation validate-template --template-body file://$template
        done
      - echo "=== Validating TypeScript ==="
      - cd frontend && npx tsc --noEmit
      - echo "=== Running ESLint ==="
      - npm run lint || true
      - echo "=== Validation complete ==="

cache:
  paths:
    - frontend/node_modules/**/*
```


#### 2.2 Create Build CodeBuild Project

Create `cfn/codebuild/codebuild-build.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for building Lambda packages'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'
  DeploymentBucket:
    Type: String
    Default: 'aws-drs-orchestration'

Resources:
  BuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-build'
      Description: 'Build Lambda deployment packages'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/python:3.12
        EnvironmentVariables:
          - Name: DEPLOYMENT_BUCKET
            Value: !Ref DeploymentBucket
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec-build.yml
      TimeoutInMinutes: 15
      LogsConfig:
        CloudWatchLogs:
          Status: ENABLED
          GroupName: !Sub '/codebuild/${ProjectName}-build'

  CodeBuildRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-codebuild-build-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'logs:CreateLogGroup'
                  - 'logs:CreateLogStream'
                  - 'logs:PutLogEvents'
                Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/codebuild/*'
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:GetObjectVersion'
                  - 's3:PutObject'
                Resource:
                  - !Sub 'arn:aws:s3:::${ProjectName}-pipeline-artifacts/*'
                  - !Sub 'arn:aws:s3:::${DeploymentBucket}/*'

Outputs:
  ProjectName:
    Value: !Ref BuildProject
  ProjectArn:
    Value: !GetAtt BuildProject.Arn
```

Create `buildspec-build.yml` in repository root:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      python: 3.12
    commands:
      - apt-get update && apt-get install -y zip

  build:
    commands:
      - echo "=== Building Lambda packages ==="
      - cd lambda
      - |
        # Install dependencies if not present
        if [ ! -d "package" ]; then
          echo "Installing Lambda dependencies..."
          pip install -r requirements.txt -t package/ --no-cache-dir
        fi
      - |
        # Package api-handler (index.py)
        echo "Packaging api-handler..."
        cd package && zip -r ../api-handler.zip . -x "*.pyc" "__pycache__/*" && cd ..
        zip -g api-handler.zip index.py
        
        # Package orchestration-stepfunctions
        echo "Packaging orchestration-stepfunctions..."
        cd package && zip -r ../orchestration-stepfunctions.zip . -x "*.pyc" "__pycache__/*" && cd ..
        zip -g orchestration-stepfunctions.zip orchestration_stepfunctions.py
        
        # Package execution-finder
        echo "Packaging execution-finder..."
        cd package && zip -r ../execution-finder.zip . -x "*.pyc" "__pycache__/*" && cd ..
        zip -g execution-finder.zip poller/execution_finder.py
        
        # Package execution-poller
        echo "Packaging execution-poller..."
        cd package && zip -r ../execution-poller.zip . -x "*.pyc" "__pycache__/*" && cd ..
        zip -g execution-poller.zip poller/execution_poller.py
        
        # Package frontend-builder
        echo "Packaging frontend-builder..."
        cd package && zip -r ../frontend-builder.zip . -x "*.pyc" "__pycache__/*" && cd ..
        zip -g frontend-builder.zip build_and_deploy.py
      - echo "Lambda packages created:"
      - ls -lh *.zip

artifacts:
  files:
    - lambda/*.zip
    - cfn/**/*
  discard-paths: no

cache:
  paths:
    - lambda/package/**/*
```

#### 2.3 Create Frontend Build CodeBuild Project

Create `cfn/codebuild/codebuild-frontend-build.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for frontend build'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'

Resources:
  FrontendBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-frontend-build'
      Description: 'Build React frontend with Vite'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/docker/library/node:22-alpine
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec-frontend-build.yml
      TimeoutInMinutes: 15
      LogsConfig:
        CloudWatchLogs:
          Status: ENABLED
          GroupName: !Sub '/codebuild/${ProjectName}-frontend-build'

  CodeBuildRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-codebuild-frontend-build-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'logs:CreateLogGroup'
                  - 'logs:CreateLogStream'
                  - 'logs:PutLogEvents'
                Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/codebuild/*'
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:GetObjectVersion'
                  - 's3:PutObject'
                Resource:
                  - !Sub 'arn:aws:s3:::${ProjectName}-pipeline-artifacts/*'

Outputs:
  ProjectName:
    Value: !Ref FrontendBuildProject
  ProjectArn:
    Value: !GetAtt FrontendBuildProject.Arn
```

Create `buildspec-frontend-build.yml` in repository root:

```yaml
version: 0.2

phases:
  install:
    runtime-versions:
      nodejs: 22
    commands:
      - cd frontend
      - npm ci --prefer-offline

  build:
    commands:
      - echo "=== Building React frontend with Vite ==="
      - cd frontend
      - npm run build
      - echo "Build complete. Artifacts:"
      - ls -lh dist/

artifacts:
  files:
    - frontend/dist/**/*
  discard-paths: no

cache:
  paths:
    - frontend/node_modules/**/*
```

#### 2.4 Create Frontend Deploy CodeBuild Project (NEW - Critical)

This project handles aws-config.js generation and CloudFront invalidation.

Create `cfn/codebuild/codebuild-frontend-deploy.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'CodeBuild project for frontend deployment with aws-config.js generation'

Parameters:
  ProjectName:
    Type: String
    Default: 'drs-orchestration'
  Environment:
    Type: String
    Default: 'dev'

Resources:
  FrontendDeployProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub '${ProjectName}-frontend-deploy'
      Description: 'Deploy frontend to S3 with aws-config.js and CloudFront invalidation'
      ServiceRole: !GetAtt CodeBuildRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: public.ecr.aws/aws-cli/aws-cli:latest
        EnvironmentVariables:
          - Name: STACK_NAME
            Value: !Sub '${ProjectName}-${Environment}'
          - Name: AWS_DEFAULT_REGION
            Value: !Ref 'AWS::Region'
      Source:
        Type: CODEPIPELINE
        BuildSpec: buildspec-frontend-deploy.yml
      TimeoutInMinutes: 15
      LogsConfig:
        CloudWatchLogs:
          Status: ENABLED
          GroupName: !Sub '/codebuild/${ProjectName}-frontend-deploy'

  CodeBuildRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-codebuild-frontend-deploy-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: CodeBuildPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 'logs:CreateLogGroup'
                  - 'logs:CreateLogStream'
                  - 'logs:PutLogEvents'
                Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/codebuild/*'
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:GetObjectVersion'
                  - 's3:PutObject'
                  - 's3:DeleteObject'
                  - 's3:ListBucket'
                Resource:
                  - !Sub 'arn:aws:s3:::${ProjectName}-pipeline-artifacts/*'
                  - 'arn:aws:s3:::*-frontend-*'
                  - 'arn:aws:s3:::*-frontend-*/*'
              - Effect: Allow
                Action:
                  - 'cloudformation:DescribeStacks'
                Resource: !Sub 'arn:aws:cloudformation:${AWS::Region}:${AWS::AccountId}:stack/${ProjectName}-*/*'
              - Effect: Allow
                Action:
                  - 'cloudfront:CreateInvalidation'
                Resource: '*'

Outputs:
  ProjectName:
    Value: !Ref FrontendDeployProject
  ProjectArn:
    Value: !GetAtt FrontendDeployProject.Arn
```

Create `buildspec-frontend-deploy.yml` in repository root:

```yaml
version: 0.2

phases:
  build:
    commands:
      - echo "=== Retrieving CloudFormation stack outputs ==="
      - |
        export API_ENDPOINT=$(aws cloudformation describe-stacks \
          --stack-name ${STACK_NAME} \
          --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
          --output text)
        export USER_POOL_ID=$(aws cloudformation describe-stacks \
          --stack-name ${STACK_NAME} \
          --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
          --output text)
        export APP_CLIENT_ID=$(aws cloudformation describe-stacks \
          --stack-name ${STACK_NAME} \
          --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
          --output text)
        export BUCKET_NAME=$(aws cloudformation describe-stacks \
          --stack-name ${STACK_NAME} \
          --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
          --output text)
        export DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
          --stack-name ${STACK_NAME} \
          --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
          --output text)
      - echo "API_ENDPOINT=${API_ENDPOINT}"
      - echo "USER_POOL_ID=${USER_POOL_ID}"
      - echo "BUCKET_NAME=${BUCKET_NAME}"
      - echo "DISTRIBUTION_ID=${DISTRIBUTION_ID}"
      
      - echo "=== Generating aws-config.js ==="
      - |
        cat > frontend/dist/aws-config.js <<EOF
        window.AWS_CONFIG = {
          Auth: {
            Cognito: {
              region: '${AWS_DEFAULT_REGION}',
              userPoolId: '${USER_POOL_ID}',
              userPoolClientId: '${APP_CLIENT_ID}',
              loginWith: {
                email: true
              }
            }
          },
          API: {
            REST: {
              DRSOrchestration: {
                endpoint: '${API_ENDPOINT}',
                region: '${AWS_DEFAULT_REGION}'
              }
            }
          }
        };
        EOF
      - echo "Generated aws-config.js:"
      - cat frontend/dist/aws-config.js
      
      - echo "=== Deploying frontend to S3 ==="
      - |
        # Sync static assets with long cache
        aws s3 sync frontend/dist/ s3://${BUCKET_NAME}/ \
          --delete \
          --cache-control "public, max-age=31536000, immutable" \
          --exclude "*.html" \
          --exclude "aws-config.js"
        
        # Sync HTML and config with no-cache
        aws s3 sync frontend/dist/ s3://${BUCKET_NAME}/ \
          --exclude "*" \
          --include "*.html" \
          --include "aws-config.js" \
          --cache-control "no-cache, no-store, must-revalidate"
      
      - echo "=== Creating CloudFront invalidation ==="
      - |
        aws cloudfront create-invalidation \
          --distribution-id ${DISTRIBUTION_ID} \
          --paths "/*"
      
      - echo "=== Frontend deployment complete ==="
```


---

### Phase 3: CodePipeline Setup (Days 4-5)

#### 3.1 Create Pipeline CloudFormation Template

Create `cfn/pipeline/pipeline.yaml`:

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
  Environment:
    Type: String
    Default: 'dev'
    AllowedValues:
      - dev
      - test
      - prod

Resources:
  # S3 Bucket for Pipeline Artifacts
  PipelineArtifactBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${ProjectName}-pipeline-artifacts-${AWS::AccountId}'
      VersioningConfiguration:
        Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldArtifacts
            Status: Enabled
            ExpirationInDays: 30

  # CodePipeline
  Pipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      Name: !Sub '${ProjectName}-pipeline'
      RoleArn: !GetAtt PipelineRole.Arn
      ArtifactStore:
        Type: S3
        Location: !Ref PipelineArtifactBucket
      RestartExecutionOnUpdate: true
      Stages:
        # Stage 1: Source from CodeCommit
        - Name: Source
          Actions:
            - Name: CodeCommitSource
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeCommit
                Version: '1'
              Configuration:
                RepositoryName: !Ref ProjectName
                BranchName: main
                PollForSourceChanges: false
              OutputArtifacts:
                - Name: SourceOutput
              Namespace: SourceVariables
              RunOrder: 1

        # Stage 2: Validate (CloudFormation + TypeScript + Lint)
        - Name: Validate
          Actions:
            - Name: ValidateTemplates
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Sub '${ProjectName}-validate'
              InputArtifacts:
                - Name: SourceOutput
              RunOrder: 1

        # Stage 3: Build (Lambda + Frontend in parallel)
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
              RunOrder: 1
            
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
              RunOrder: 1

        # Stage 4: Deploy Infrastructure
        - Name: DeployInfrastructure
          Actions:
            - Name: UploadLambdaToS3
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
              RunOrder: 1
            
            - Name: DeployCloudFormation
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Provider: CloudFormation
                Version: '1'
              Configuration:
                ActionMode: CREATE_UPDATE
                StackName: !Sub '${ProjectName}-${Environment}'
                TemplatePath: SourceOutput::cfn/master-template.yaml
                Capabilities: CAPABILITY_IAM,CAPABILITY_NAMED_IAM,CAPABILITY_AUTO_EXPAND
                RoleArn: !GetAtt CloudFormationRole.Arn
                ParameterOverrides: !Sub |
                  {
                    "ProjectName": "${ProjectName}",
                    "Environment": "${Environment}",
                    "SourceBucket": "${DeploymentBucket}",
                    "AdminEmail": "${AdminEmail}"
                  }
                OutputFileName: stack-outputs.json
              InputArtifacts:
                - Name: SourceOutput
              OutputArtifacts:
                - Name: StackOutputs
              RunOrder: 2

        # Stage 5: Deploy Frontend (with aws-config.js and CloudFront invalidation)
        - Name: DeployFrontend
          Actions:
            - Name: DeployFrontendToS3
              ActionTypeId:
                Category: Build
                Owner: AWS
                Provider: CodeBuild
                Version: '1'
              Configuration:
                ProjectName: !Sub '${ProjectName}-frontend-deploy'
                EnvironmentVariables: !Sub |
                  [
                    {"name": "STACK_NAME", "value": "${ProjectName}-${Environment}"},
                    {"name": "AWS_DEFAULT_REGION", "value": "${AWS::Region}"}
                  ]
              InputArtifacts:
                - Name: FrontendArtifacts
              RunOrder: 1

  # EventBridge Rule to trigger pipeline on CodeCommit push
  CodeCommitEventRule:
    Type: AWS::Events::Rule
    Properties:
      Name: !Sub '${ProjectName}-codecommit-trigger'
      Description: 'Trigger pipeline on CodeCommit push to main'
      EventPattern:
        source:
          - aws.codecommit
        detail-type:
          - CodeCommit Repository State Change
        resources:
          - !Sub 'arn:aws:codecommit:${AWS::Region}:${AWS::AccountId}:${ProjectName}'
        detail:
          event:
            - referenceCreated
            - referenceUpdated
          referenceType:
            - branch
          referenceName:
            - main
      State: ENABLED
      Targets:
        - Id: CodePipelineTarget
          Arn: !Sub 'arn:aws:codepipeline:${AWS::Region}:${AWS::AccountId}:${ProjectName}-pipeline'
          RoleArn: !GetAtt EventBridgeRole.Arn

  # IAM Role for EventBridge
  EventBridgeRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-eventbridge-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: events.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: StartPipeline
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: 'codepipeline:StartPipelineExecution'
                Resource: !Sub 'arn:aws:codepipeline:${AWS::Region}:${AWS::AccountId}:${ProjectName}-pipeline'

  # IAM Role for CodePipeline
  PipelineRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-pipeline-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action: 'sts:AssumeRole'
      Policies:
        - PolicyName: PipelinePolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:GetObjectVersion'
                  - 's3:PutObject'
                  - 's3:ListBucket'
                Resource:
                  - !Sub 'arn:aws:s3:::${PipelineArtifactBucket}'
                  - !Sub 'arn:aws:s3:::${PipelineArtifactBucket}/*'
                  - !Sub 'arn:aws:s3:::${DeploymentBucket}'
                  - !Sub 'arn:aws:s3:::${DeploymentBucket}/*'
              - Effect: Allow
                Action:
                  - 'codecommit:GetBranch'
                  - 'codecommit:GetCommit'
                  - 'codecommit:UploadArchive'
                  - 'codecommit:GetUploadArchiveStatus'
                  - 'codecommit:CancelUploadArchive'
                Resource: !Sub 'arn:aws:codecommit:${AWS::Region}:${AWS::AccountId}:${ProjectName}'
              - Effect: Allow
                Action:
                  - 'codebuild:BatchGetBuilds'
                  - 'codebuild:StartBuild'
                Resource:
                  - !Sub 'arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:project/${ProjectName}-*'
              - Effect: Allow
                Action:
                  - 'cloudformation:CreateStack'
                  - 'cloudformation:UpdateStack'
                  - 'cloudformation:DeleteStack'
                  - 'cloudformation:DescribeStacks'
                  - 'cloudformation:DescribeStackEvents'
                  - 'cloudformation:GetTemplate'
                  - 'cloudformation:ValidateTemplate'
                Resource: !Sub 'arn:aws:cloudformation:${AWS::Region}:${AWS::AccountId}:stack/${ProjectName}-*/*'
              - Effect: Allow
                Action:
                  - 'iam:PassRole'
                Resource: !GetAtt CloudFormationRole.Arn

  # IAM Role for CloudFormation
  CloudFormationRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-cloudformation-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: cloudformation.amazonaws.com
            Action: 'sts:AssumeRole'
      ManagedPolicyArns:
        - 'arn:aws:iam::aws:policy/AdministratorAccess'

Outputs:
  PipelineName:
    Description: 'CodePipeline name'
    Value: !Ref Pipeline
  PipelineUrl:
    Description: 'CodePipeline console URL'
    Value: !Sub 'https://${AWS::Region}.console.aws.amazon.com/codesuite/codepipeline/pipelines/${ProjectName}-pipeline/view'
  ArtifactBucket:
    Description: 'Pipeline artifact bucket'
    Value: !Ref PipelineArtifactBucket
```

---

### Phase 4: Migration Execution (Day 6)

#### 4.1 Deploy CodeBuild Projects

```bash
# Deploy validation project
aws cloudformation deploy \
  --template-file cfn/codebuild/codebuild-validate.yaml \
  --stack-name drs-orchestration-codebuild-validate \
  --parameter-overrides ProjectName=drs-orchestration \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Deploy build project
aws cloudformation deploy \
  --template-file cfn/codebuild/codebuild-build.yaml \
  --stack-name drs-orchestration-codebuild-build \
  --parameter-overrides ProjectName=drs-orchestration \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Deploy frontend build project
aws cloudformation deploy \
  --template-file cfn/codebuild/codebuild-frontend-build.yaml \
  --stack-name drs-orchestration-codebuild-frontend-build \
  --parameter-overrides ProjectName=drs-orchestration \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

# Deploy frontend deploy project (NEW)
aws cloudformation deploy \
  --template-file cfn/codebuild/codebuild-frontend-deploy.yaml \
  --stack-name drs-orchestration-codebuild-frontend-deploy \
  --parameter-overrides ProjectName=drs-orchestration Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### 4.2 Deploy CodePipeline

```bash
aws cloudformation deploy \
  --template-file cfn/pipeline/pipeline.yaml \
  --stack-name drs-orchestration-pipeline \
  --parameter-overrides \
    ProjectName=drs-orchestration \
    DeploymentBucket=aws-drs-orchestration \
    AdminEmail=admin@example.com \
    Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

#### 4.3 Test Pipeline

```bash
# Trigger pipeline manually
aws codepipeline start-pipeline-execution \
  --name drs-orchestration-pipeline \
  --region us-east-1

# Monitor execution
aws codepipeline get-pipeline-state \
  --name drs-orchestration-pipeline \
  --region us-east-1

# Watch pipeline in console
echo "https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/drs-orchestration-pipeline/view"
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
| **aws-config.js** | Generated in deploy job | Generated in CodeBuild |
| **CloudFront Invalidation** | In deploy job | In CodeBuild |
| **TypeScript Validation** | Yes | Yes (added) |
| **ESLint** | Yes | Yes (added) |

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
- [ ] Create SSM parameters for configuration
- [ ] Setup GitLab mirror (optional)
- [ ] Test clone/push/pull operations

### CodeBuild Setup

- [ ] Create buildspec-validate.yml
- [ ] Create buildspec-build.yml
- [ ] Create buildspec-frontend-build.yml
- [ ] Create buildspec-frontend-deploy.yml (NEW)
- [ ] Deploy validation CodeBuild project
- [ ] Deploy build CodeBuild project
- [ ] Deploy frontend build project
- [ ] Deploy frontend deploy project (NEW)
- [ ] Test each project independently
- [ ] Verify artifacts in S3

### CodePipeline Setup

- [ ] Create pipeline CloudFormation template
- [ ] Deploy pipeline stack
- [ ] Configure EventBridge trigger
- [ ] Test end-to-end pipeline execution
- [ ] Verify CloudFormation deployment
- [ ] Verify aws-config.js generation (NEW)
- [ ] Verify CloudFront invalidation (NEW)

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
- CloudWatch Logs: ~$0.50/month
- **Total**: ~$7/month

**Additional Cost**: ~$2/month

---

## Success Metrics

- **Pipeline Execution Time**: <15 minutes (same as GitLab)
- **Deployment Success Rate**: >95%
- **Mean Time to Deploy**: <20 minutes
- **Pipeline Availability**: >99.9%
- **Cost**: <$10/month

---

## File Structure After Migration

```text
AWS-DRS-Orchestration/
├── buildspec-validate.yml          # NEW: Validation buildspec
├── buildspec-build.yml             # NEW: Lambda build buildspec
├── buildspec-frontend-build.yml    # NEW: Frontend build buildspec
├── buildspec-frontend-deploy.yml   # NEW: Frontend deploy buildspec
├── cfn/
│   ├── codebuild/                  # NEW: CodeBuild project templates
│   │   ├── codebuild-validate.yaml
│   │   ├── codebuild-build.yaml
│   │   ├── codebuild-frontend-build.yaml
│   │   └── codebuild-frontend-deploy.yaml
│   ├── pipeline/                   # NEW: Pipeline template
│   │   └── pipeline.yaml
│   ├── master-template.yaml
│   ├── database-stack.yaml
│   ├── lambda-stack.yaml
│   ├── api-stack.yaml
│   ├── step-functions-stack.yaml
│   ├── frontend-stack.yaml
│   └── security-stack.yaml
├── .gitlab-ci.yml                  # KEEP: For GitLab mirror (optional)
└── ...
```

---

## References

- [Archived DR Orchestrator Pipeline](../../archive/dr-orchestration-artifacts/pipeline.yaml)
- [Current GitLab CI/CD](../../.gitlab-ci.yml)
- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)
- [AWS CodeCommit Documentation](https://docs.aws.amazon.com/codecommit/)
