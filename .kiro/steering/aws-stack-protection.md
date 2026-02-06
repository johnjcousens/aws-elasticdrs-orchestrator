# AWS Stack Protection Rules

## Stack Naming Convention

**Primary Working Stack**: `aws-drs-orchestration-test`
- Stack ARN: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestration-test/e1e00cb0-fe49-11f0-a956-0ef4995d315b`
- Created: January 31, 2026
- This is the main working environment
- All development and testing happens here
- S3 Deployment Bucket: `aws-drs-orchestration-test`
- S3 Frontend Bucket: `aws-drs-orchestration-fe-438465159935-test`
- API Endpoint: `https://mgqims9lj1.execute-api.us-east-1.amazonaws.com/test`
- CloudFront URL: `https://d319nadlgk4oj.cloudfront.net`

Other environments (if they exist):
- `aws-drs-orchestration-dev` - Alternative development environment
- `aws-drs-orchestration-staging` - Staging environment
- `aws-drs-orchestration-prod` - Production environment

## Current Working Environment

**Always deploy to**: `test` environment
```bash
./scripts/deploy.sh test
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
