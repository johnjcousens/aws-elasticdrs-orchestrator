# CI/CD Migration Design Document

## Overview
Technical design for migrating the AWS DRS Orchestration project from GitLab CI/CD to AWS CodeCommit and CodePipeline, integrating the CI/CD infrastructure directly into the CloudFormation master template.

## Current State Analysis

### Existing Infrastructure
- **Repository**: GitLab-hosted with `.gitlab-ci.yml` pipeline
- **Deployment**: Manual CloudFormation deployment using `scripts/sync-to-deployment-bucket.sh`
- **Architecture**: 6 CloudFormation nested stacks (master template with DatabaseStack, LambdaStack, StepFunctionsStack, ApiStack, EventBridgeStack, FrontendStack)
- **Frontend**: React with CloudScape UI, built with Vite
- **Backend**: 5 Lambda functions with Python 3.12 runtime
- **Storage**: S3 bucket `aws-drs-orchestration` for deployment artifacts

## Target Architecture

### Repository Structure
```
CodeCommit Repository (aws-drs-orchestration)
├── cfn/
│   ├── master-template.yaml (updated with CI/CD stacks)
│   ├── codecommit-stack.yaml (new)
│   ├── codepipeline-stack.yaml (new)
│   ├── codebuild-projects-stack.yaml (new)
│   └── existing stacks...
├── buildspecs/
│   ├── validate-buildspec.yml (new)
│   ├── build-buildspec.yml (new)
│   ├── test-buildspec.yml (new)
│   ├── deploy-infra-buildspec.yml (new)
│   └── deploy-frontend-buildspec.yml (new)
├── scripts/
│   └── deployment scripts (adapted for CodeBuild)
└── source code...
```

### CI/CD Pipeline Architecture

#### CodePipeline Stages
1. **Source Stage** - Trigger: CodeCommit repository changes
2. **Validate Stage** - CloudFormation template validation and linting
3. **Build Stage** - Lambda function packaging and frontend build
4. **Test Stage** - Unit tests and integration tests
5. **Deploy Infrastructure Stage** - CloudFormation stack deployment
6. **Deploy Frontend Stage** - S3 sync and CloudFront invalidation

### CloudFormation Stack Structure

#### Master Template Updates
```yaml
Resources:
  # Existing nested stacks
  DatabaseStack: ...
  LambdaStack: ...
  StepFunctionsStack: ...
  ApiStack: ...
  EventBridgeStack: ...
  FrontendStack: ...
  
  # New CI/CD stacks
  CodeCommitStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Sub '${TemplateBaseURL}/codecommit-stack.yaml'
      Parameters:
        GitHubRepositoryURL: !Ref GitHubRepositoryURL
        
  CodePipelineStack:
    Type: AWS::CloudFormation::Stack
    DependsOn: [CodeCommitStack, CodeBuildProjectsStack]
    Properties:
      TemplateURL: !Sub '${TemplateBaseURL}/codepipeline-stack.yaml'
      Parameters:
        CodeCommitRepositoryName: !GetAtt CodeCommitStack.Outputs.RepositoryName
        ArtifactBucketName: !GetAtt CodeCommitStack.Outputs.ArtifactBucketName
        
  CodeBuildProjectsStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Sub '${TemplateBaseURL}/codebuild-projects-stack.yaml'
      Parameters:
        ArtifactBucketName: !GetAtt CodeCommitStack.Outputs.ArtifactBucketName
```

## Detailed Component Design

### 1. CodeCommit Stack (`codecommit-stack.yaml`)
**Status**: ✅ Already created

**Components**:
- CodeCommit repository with GitHub mirroring
- S3 bucket for pipeline artifacts
- IAM roles for repository access

### 2. CodePipeline Stack (`codepipeline-stack.yaml`)
**Status**: 🔄 To be created

**Components**:
- CodePipeline with 6 stages
- Service role for pipeline execution
- Integration with CodeBuild projects
- Artifact management

### 3. CodeBuild Projects Stack (`codebuild-projects-stack.yaml`)
**Status**: 🔄 To be created

**Projects**:
- **ValidateProject**: Template validation and linting
- **BuildProject**: Lambda packaging and frontend build
- **TestProject**: Unit and integration tests
- **DeployInfraProject**: CloudFormation deployment
- **DeployFrontendProject**: S3 sync and CloudFront invalidation

### 4. BuildSpec Files
**Status**: 🔄 To be created

#### Key BuildSpec Configurations
- **validate-buildspec.yml**: CloudFormation validation, Python linting (PEP 8), TypeScript checks
- **build-buildspec.yml**: Lambda packaging (5 zip files), frontend build with Vite
- **test-buildspec.yml**: Python unit tests with pytest, frontend tests, coverage reporting
- **deploy-infra-buildspec.yml**: S3 artifact upload, CloudFormation deployment
- **deploy-frontend-buildspec.yml**: Frontend configuration generation, S3 sync, CloudFront invalidation

## Migration Strategy

### Phase 1: Infrastructure Setup
1. ✅ Create CodeCommit stack (completed)
2. 🔄 Create CodePipeline stack
3. 🔄 Create CodeBuild projects stack
4. 🔄 Update master template with new nested stacks

### Phase 2: Pipeline Configuration
1. 🔄 Create buildspec files for each stage
2. 🔄 Adapt existing deployment scripts for CodeBuild
3. 🔄 Configure IAM permissions for cross-service access

### Phase 3: Testing and Validation
1. 🔄 Deploy updated master template
2. 🔄 Test pipeline with sample commits
3. 🔄 Validate all stages execute correctly
4. 🔄 Performance and security testing

### Phase 4: Migration Cutover
1. 🔄 Mirror GitLab repository to CodeCommit
2. 🔄 Update team workflows and documentation
3. 🔄 Decommission GitLab CI/CD pipeline

## Security Considerations

### IAM Roles and Permissions
- **CodePipelineServiceRole**: Pipeline execution permissions
- **CodeBuildServiceRole**: Build project execution permissions
- **CloudFormationDeploymentRole**: Infrastructure deployment permissions
- **GitHubMirroringRole**: Repository synchronization permissions

### Secrets Management
- GitHub personal access token stored in AWS Secrets Manager
- Database credentials managed through existing parameter store
- API keys and sensitive configuration via environment variables

### Network Security
- CodeBuild projects in VPC for secure resource access
- S3 bucket policies for artifact access control
- CloudTrail logging for audit compliance

## Monitoring and Observability

### CloudWatch Integration
- Pipeline execution metrics
- Build project logs and metrics
- Custom dashboards for CI/CD health
- Alarms for pipeline failures

### Notifications
- SNS topics for pipeline state changes
- Email notifications for deployment failures
- EventBridge integration for automated responses

## Rollback Strategy

### Emergency Rollback
1. Revert to manual deployment process
2. Use existing `sync-to-deployment-bucket.sh` script
3. Deploy previous known-good CloudFormation templates

### Gradual Rollback
1. Disable automatic pipeline triggers
2. Use pipeline for validation only
3. Manual approval gates for deployments

## Performance Considerations

### Build Optimization
- Parallel execution where possible
- Caching for npm and pip dependencies
- Incremental builds for unchanged components
- Artifact reuse between stages

### Cost Optimization
- Right-sized CodeBuild compute types
- S3 lifecycle policies for artifacts
- Scheduled cleanup of old pipeline executions

## Implementation Checklist

### CloudFormation Templates
- [x] `cfn/codecommit-stack.yaml` - Repository and basic infrastructure
- [ ] `cfn/codepipeline-stack.yaml` - Pipeline definition
- [ ] `cfn/codebuild-projects-stack.yaml` - Build projects
- [ ] Update `cfn/master-template.yaml` - Integrate new stacks

### BuildSpec Files
- [ ] `buildspecs/validate-buildspec.yml` - Validation stage
- [ ] `buildspecs/build-buildspec.yml` - Build stage
- [ ] `buildspecs/test-buildspec.yml` - Test stage
- [ ] `buildspecs/deploy-infra-buildspec.yml` - Infrastructure deployment
- [ ] `buildspecs/deploy-frontend-buildspec.yml` - Frontend deployment

### Scripts and Configuration
- [ ] Adapt `scripts/sync-to-deployment-bucket.sh` for CodeBuild
- [ ] Create deployment helper scripts
- [ ] Update documentation and README files

### Testing and Validation
- [ ] Unit tests for new CloudFormation templates
- [ ] Integration testing of complete pipeline
- [ ] Security and compliance validation
- [ ] Performance benchmarking

## Success Criteria

1. **Functional Requirements**
   - All existing deployment capabilities preserved
   - Automated pipeline triggers on code changes
   - Successful deployment of all stack components
   - Frontend and backend deployments working correctly

2. **Non-Functional Requirements**
   - Pipeline execution time < 15 minutes
   - 99.5% pipeline reliability
   - Zero downtime deployments
   - Comprehensive logging and monitoring

3. **Security Requirements**
   - All IAM roles follow least privilege principle
   - Secrets properly managed and rotated
   - Audit trail for all deployments
   - Compliance with organizational security policies

This design provides a comprehensive roadmap for migrating from GitLab CI/CD to AWS CodeCommit/CodePipeline while maintaining all existing functionality and improving automation capabilities.