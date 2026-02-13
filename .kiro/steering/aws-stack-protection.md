---
inclusion: always
---

# AWS Stack Protection Rules

## Stack Naming Convention

**Primary Working Stack**: `aws-drs-orchestration-dev`
- AWS Account: `123456789012`
- Stack ARN: TBD (after first deployment)
- This is the main working environment
- All development and testing happens here
- S3 Deployment Bucket: `aws-drs-orchestration-dev`
- S3 Frontend Bucket: `aws-drs-orchestration-fe-123456789012-dev`
- API Endpoint: TBD (after first deployment)
- CloudFront URL: TBD (after first deployment)

Other environments (if they exist):
- `aws-drs-orchestration-test` - Test environment
- `aws-drs-orchestration-staging` - Staging environment
- `aws-drs-orchestration-prod` - Production environment

## Current Working Environment

**Always deploy to**: `dev` environment
```bash
./scripts/deploy.sh dev
```

## Best Practices

### Before Any Stack Operation

1. **Verify the stack name** matches your intended environment
2. **Check the AWS account** you're deploying to
3. **Review the parameters** before deployment
4. **Use appropriate environment variables** from `.env.{environment}`

### Deployment Safety

- Always use the deploy script: `./scripts/deploy.sh {environment}`
- Run validation first: `./scripts/deploy.sh {environment} --validate-only`
- Check stack status before deploying: `aws cloudformation describe-stacks --stack-name {stack-name}`

### Environment Isolation

Each environment should have:
- Separate S3 deployment bucket: `aws-drs-orchestration-{environment}`
- Separate DynamoDB tables: `aws-drs-orchestration-*-{environment}`
- Separate Lambda functions: `aws-drs-orchestration-*-{environment}`
- Separate CloudFront distribution
- Separate Cognito User Pool

## Emergency Procedures

If you accidentally deploy to the wrong environment:

1. **IMMEDIATELY** check what was deployed:
   ```bash
   aws cloudformation describe-stacks --stack-name {stack-name}
   ```

2. **If wrong environment**, delete the stack:
   ```bash
   aws cloudformation delete-stack --stack-name {stack-name}
   ```

3. **Document the incident** and review deployment process

## Verification Checklist

Before deploying to production:

- [ ] Code reviewed and approved
- [ ] All tests passing
- [ ] Security scans completed
- [ ] Deployed and tested in dev environment
- [ ] Deployed and tested in test/staging environment
- [ ] Backup plan in place
- [ ] Rollback procedure documented
- [ ] Team notified of deployment

## Related Documentation

- [CI/CD Workflow Enforcement](cicd-workflow-enforcement.md) - Deployment workflow
- [Deployment Flexibility Guide](../../docs/guides/DEPLOYMENT_FLEXIBILITY_GUIDE.md) - Deployment modes
