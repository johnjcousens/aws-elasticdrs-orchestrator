# AWS Stack Protection Rules

## Stack Naming Convention

Use descriptive environment names for your stacks:
- `aws-drs-orchestration-dev` - Development environment
- `aws-drs-orchestration-test` - Test environment
- `aws-drs-orchestration-staging` - Staging environment
- `aws-drs-orchestration-prod` - Production environment

## Best Practices

### Before Any Stack Operation

1. **Verify the stack name** matches your intended environment
2. **Check the AWS account** you're deploying to
3. **Review the parameters** before deployment
4. **Use appropriate environment variables** from `.env.{environment}`

### Deployment Safety

- Always use the deploy script: `./scripts/deploy.sh {environment}`
- Run validation first: `./scripts/deploy.sh {environment} --validate-only`
- Use `--skip-push` for testing: `./scripts/deploy.sh {environment} --skip-push`
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
