---
inclusion: always
---

# AWS Stack Protection Rules

## Stack Naming Convention

**Primary Working Stack**: `hrp-drs-tech-adapter-dev`
- AWS Account: `891376951562`
- Stack ARN: TBD (after first deployment)
- This is the main working environment
- All development and testing happens here
- S3 Deployment Bucket: `hrp-drs-tech-adapter-dev`
- S3 Frontend Bucket: `hrp-drs-tech-adapter-fe-891376951562-dev`
- API Endpoint: TBD (after first deployment)
- CloudFront URL: TBD (after first deployment)

Other environments (if they exist):
- `hrp-drs-tech-adapter-test` - Test environment
- `hrp-drs-tech-adapter-staging` - Staging environment
- `hrp-drs-tech-adapter-prod` - Production environment

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
- Separate S3 deployment bucket: `hrp-drs-tech-adapter-{environment}`
- Separate DynamoDB tables: `hrp-drs-tech-adapter-*-{environment}`
- Separate Lambda functions: `hrp-drs-tech-adapter-*-{environment}`
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
