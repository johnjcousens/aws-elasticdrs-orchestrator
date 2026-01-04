# Repository Consolidation Plan

## Current State Analysis

### Active Repositories
1. **CodeCommit** (Primary CI/CD): `aws-elasticdrs-orchestrator-dev`
   - ✅ Active AWS CodePipeline integration
   - ✅ Working CI/CD with 7 stages
   - ✅ Security scanning integrated
   - ✅ SNS notifications configured

2. **GitHub** (Development/Backup): Has `.github/workflows/`
   - ❓ Redundant with CodeCommit
   - ❓ External dependency
   - ❓ Potential security compliance issues

3. **AWS Internal GitLab**: `https://code.aws.dev/personal_projects/alias_j/jocousen`
   - 🎯 Recommended primary repository
   - ✅ Enterprise features
   - ✅ AWS native integration
   - ✅ Superior developer experience

## Recommended Migration Path

### Phase 1: Immediate (Keep Pipeline Running)
**Status**: ✅ CURRENT - Pipeline is running successfully
- Keep CodeCommit as primary until migration complete
- Continue using current CI/CD pipeline
- Monitor current pipeline execution: `6a2d416b-3851-4029-a94a-61f19cdd6396`

### Phase 2: Prepare GitLab Migration
1. **Set up AWS Internal GitLab repository**
   ```bash
   # Create new repository on code.aws.dev
   # Repository: aws-drs-orchestration
   # Visibility: Internal (Amazon employees only)
   ```

2. **Migrate GitLab CI configuration**
   - Use existing `.gitlab-ci.yml` (already present)
   - Configure AWS credentials in GitLab CI/CD variables
   - Set up GitLab CI/CD pipeline

3. **Configure GitLab → CodePipeline integration**
   ```yaml
   # Option A: GitLab triggers CodePipeline
   # Option B: Migrate entire CI/CD to GitLab CI
   ```

### Phase 3: Migration Execution
1. **Mirror repositories**
   ```bash
   # Push to GitLab
   git remote add gitlab https://code.aws.dev/personal_projects/alias_j/jocousen/aws-drs-orchestration.git
   git push gitlab main --all
   git push gitlab main --tags
   ```

2. **Update CI/CD source**
   - Modify CodePipeline source to use GitLab webhook
   - Or migrate to GitLab CI entirely

3. **Test new pipeline**
   - Verify all stages work with GitLab source
   - Ensure security scanning still functions
   - Validate SNS notifications

### Phase 4: Cleanup
1. **Archive GitHub repository**
   - Add deprecation notice
   - Archive repository (read-only)

2. **Deprecate CodeCommit** (after GitLab CI is working)
   - Keep for historical reference
   - Remove from active CI/CD

## GitLab CI vs CodePipeline Comparison

### Option A: GitLab CI + AWS Integration
```yaml
# .gitlab-ci.yml advantages:
stages:
  - validate
  - security-scan    # Built-in security scanning
  - build
  - test
  - deploy-infra
  - deploy-frontend

# Benefits:
# - Single platform for code + CI/CD
# - Advanced pipeline features
# - Better developer experience
# - Integrated security scanning
```

### Option B: GitLab + CodePipeline Hybrid
```yaml
# Keep CodePipeline, change source to GitLab
# Benefits:
# - Minimal migration risk
# - Keep existing AWS integrations
# - Gradual transition possible
```

## Recommended Architecture: GitLab CI (Option A)

### Why GitLab CI is Superior
1. **Unified Platform**: Code, CI/CD, issues, wiki in one place
2. **Advanced Features**: 
   - Parallel/sequential job execution
   - Conditional deployments
   - Environment management
   - Deployment approvals
3. **Security**: Built-in SAST, dependency scanning
4. **Cost**: No additional AWS CodeBuild/CodePipeline costs

### Migration Timeline
- **Week 1**: Set up GitLab repository and basic CI
- **Week 2**: Migrate CI/CD pipeline to GitLab CI
- **Week 3**: Test and validate all functionality
- **Week 4**: Switch primary development to GitLab
- **Week 5**: Archive GitHub, deprecate CodeCommit

## Implementation Steps

### 1. Set Up GitLab Repository
```bash
# Create repository on code.aws.dev
# Configure AWS credentials in GitLab CI/CD variables:
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
# - AWS_SESSION_TOKEN (if using temporary credentials)
# - AWS_DEFAULT_REGION: us-east-1
# - DEPLOYMENT_BUCKET: aws-elasticdrs-orchestrator
# - ADMIN_EMAIL: jocousen@amazon.com
```

### 2. Configure GitLab CI Pipeline
The existing `.gitlab-ci.yml` is already comprehensive and includes:
- ✅ CloudFormation validation
- ✅ Python linting (Black, Flake8, isort)
- ✅ Frontend linting (ESLint)
- ✅ Lambda packaging
- ✅ Frontend building
- ✅ Infrastructure deployment
- ✅ Frontend deployment

### 3. Add Security Scanning to GitLab CI
```yaml
# Add to .gitlab-ci.yml
security-scan:
  stage: security-scan
  image: public.ecr.aws/docker/library/python:3.12
  script:
    - pip install bandit semgrep safety
    - bandit -r lambda/ -f json -o bandit-report.json
    - semgrep --config=auto lambda/ --json -o semgrep-report.json
    - safety check --json --output safety-report.json
  artifacts:
    reports:
      sast: [bandit-report.json, semgrep-report.json]
    paths:
      - "*-report.json"
```

### 4. Migration Commands
```bash
# 1. Add GitLab remote
git remote add gitlab https://code.aws.dev/personal_projects/alias_j/jocousen/aws-drs-orchestration.git

# 2. Push all branches and tags
git push gitlab main
git push gitlab --all
git push gitlab --tags

# 3. Set GitLab as primary
git remote set-url origin https://code.aws.dev/personal_projects/alias_j/jocousen/aws-drs-orchestration.git

# 4. Update local clone
git remote remove codecommit
git remote remove github
```

## Benefits of Consolidation

### Developer Experience
- ✅ Single source of truth
- ✅ Modern Git interface
- ✅ Integrated CI/CD
- ✅ Better code review process

### Security & Compliance
- ✅ AWS native (no external dependencies)
- ✅ Amazon security policies compliant
- ✅ Built-in security scanning
- ✅ Audit trail and access controls

### Operational Efficiency
- ✅ Reduced complexity (1 repo vs 3)
- ✅ Lower maintenance overhead
- ✅ Consistent development workflow
- ✅ Better project management tools

## Risk Mitigation

### Backup Strategy
1. **Keep CodeCommit as backup** during transition
2. **Export GitHub repository** before archiving
3. **Test GitLab CI thoroughly** before switching
4. **Maintain rollback plan** to CodePipeline if needed

### Validation Checklist
- [ ] GitLab CI pipeline runs successfully
- [ ] All 7 stages complete (validate → deploy-frontend)
- [ ] Security scanning produces same results
- [ ] SNS notifications work correctly
- [ ] Lambda functions deploy properly
- [ ] Frontend deploys to S3/CloudFront
- [ ] All team members have GitLab access

## Next Steps

### Immediate (After Current Pipeline Completes)
1. **Monitor current pipeline completion**
2. **Verify all security utilities are deployed**
3. **Document current working state**

### Short Term (Next Week)
1. **Set up GitLab repository**
2. **Configure GitLab CI variables**
3. **Test GitLab CI pipeline**
4. **Validate AWS integrations**

### Medium Term (Next Month)
1. **Switch primary development to GitLab**
2. **Archive GitHub repository**
3. **Deprecate CodeCommit (keep as backup)**
4. **Update documentation and team processes**

---

**Recommendation**: Migrate to AWS Internal GitLab for superior developer experience, better AWS integration, and enterprise-grade features while maintaining security and compliance.