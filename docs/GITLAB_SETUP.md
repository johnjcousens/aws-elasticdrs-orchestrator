# GitLab Setup Guide for AWS DRS Orchestration

## Quick Start

The repository has been initialized with Git and is ready for GitLab. Follow these steps to complete the setup:

## 1. Create GitLab Repository

### Option A: GitLab UI
1. Log in to your GitLab instance
2. Click **New Project** → **Create blank project**
3. Enter project details:
   - **Project name**: `AWS-DRS-Orchestration`
   - **Project slug**: `aws-drs-orchestration`
   - **Visibility**: Private (recommended)
4. Click **Create project**

### Option B: GitLab CLI
```bash
# Create project via API
curl --request POST \
  --header "PRIVATE-TOKEN: <your_access_token>" \
  --data "name=AWS-DRS-Orchestration&visibility=private" \
  "https://gitlab.example.com/api/v4/projects"
```

## 2. Add GitLab Remote

```bash
cd AWS-DRS-Orchestration

# Add GitLab as remote origin
git remote add origin git@gitlab.example.com:your-username/aws-drs-orchestration.git

# Or use HTTPS
git remote add origin https://gitlab.example.com/your-username/aws-drs-orchestration.git

# Verify remote
git remote -v
```

## 3. Push to GitLab

```bash
# Push main branch
git push -u origin main

# Create and push develop branch
git checkout -b develop
git push -u origin develop
```

## 4. Configure CI/CD Variables

In GitLab, navigate to **Settings** → **CI/CD** → **Variables** and add:

### Required Variables

| Variable | Description | Protected | Masked |
|----------|-------------|-----------|--------|
| `AWS_ACCESS_KEY_ID` | AWS credentials for deployment | ✓ | ✓ |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | ✓ | ✓ |
| `AWS_DEFAULT_REGION` | Default AWS region (e.g., us-west-2) | ✗ | ✗ |

### Optional Variables

| Variable | Description | Protected | Masked |
|----------|-------------|-----------|--------|
| `ADMIN_EMAIL` | Admin email for Cognito | ✗ | ✗ |
| `NOTIFICATION_EMAIL` | SNS notification email | ✗ | ✗ |
| `CLOUDFRONT_PRICE_CLASS` | CloudFront price class | ✗ | ✗ |

## 5. Configure Protected Branches

1. Navigate to **Settings** → **Repository** → **Protected branches**
2. Protect `main` branch:
   - **Allowed to merge**: Maintainers
   - **Allowed to push**: No one
   - **Require approval**: 1 approval
3. Protect `develop` branch:
   - **Allowed to merge**: Developers
   - **Allowed to push**: Developers

## 6. Enable Auto DevOps (Optional)

1. Navigate to **Settings** → **CI/CD** → **Auto DevOps**
2. Configure as needed for your organization's standards

## 7. Set Up Merge Request Approvals

1. Navigate to **Settings** → **Merge requests**
2. Configure:
   - **Merge method**: Merge commit
   - **Merge checks**: All discussions resolved
   - **Approvals**: At least 1 approval required

## 8. Configure Runners

### Using Shared Runners
- Ensure shared runners are enabled in **Settings** → **CI/CD** → **Runners**

### Using Specific Runners
```bash
# Register a GitLab Runner
gitlab-runner register \
  --url https://gitlab.example.com \
  --registration-token <project_token> \
  --executor docker \
  --docker-image python:3.12 \
  --description "AWS DRS Orchestration Runner"
```

## 9. Test CI/CD Pipeline

```bash
# Make a small change
echo "# Test" >> README.md
git add README.md
git commit -m "test: Trigger CI/CD pipeline"
git push

# Monitor pipeline in GitLab UI: CI/CD → Pipelines
```

## 10. Configure Deployment Environments

In GitLab, create environments:

1. **Development**
   - Auto-deploy from `develop` branch
   - Manual approval required

2. **Staging**
   - Auto-deploy from `main` branch
   - Manual approval required

3. **Production**
   - Deploy from `main` branch only
   - Requires staging deployment + approval

## Pipeline Overview

The `.gitlab-ci.yml` includes:

### Stages

1. **Validate**: CloudFormation templates, Python code, YAML syntax
2. **Test**: Unit tests for Lambda functions (to be implemented)
3. **Build**: Create Lambda deployment packages
4. **Deploy**: Multi-environment deployment with manual triggers

### Deployment Flow

```
develop branch → Dev Environment (manual)
     ↓
main branch → Staging Environment (manual)
     ↓
main branch → Production Environment (requires staging + manual approval)
```

## Troubleshooting

### Issue: Pipeline fails on CloudFormation validation
**Solution**: Ensure AWS credentials are configured in CI/CD variables

### Issue: Lambda package build fails
**Solution**: Check Python dependencies in requirements.txt

### Issue: Deployment fails with permissions error
**Solution**: Verify IAM permissions for deployment user/role

## Branch Strategy

### Main Branches
- `main`: Production-ready code, deployable to production
- `develop`: Integration branch for features

### Feature Branches
```bash
# Create feature branch
git checkout develop
git checkout -b feature/add-api-gateway
git push -u origin feature/add-api-gateway

# After completion, create merge request to develop
```

### Hotfix Branches
```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug-fix
git push -u origin hotfix/critical-bug-fix

# Merge to both main and develop
```

## Next Steps

1. Complete remaining implementation steps (API Gateway, Custom Resources, Frontend)
2. Implement unit tests in Step 12
3. Configure production AWS credentials
4. Set up monitoring and alerting
5. Document deployment runbooks

## Additional Resources

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [AWS CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [GitLab Runner Documentation](https://docs.gitlab.com/runner/)

---

**Repository Status**: Initialized and ready for GitLab push  
**Current Branch**: main  
**Total Commits**: 2
