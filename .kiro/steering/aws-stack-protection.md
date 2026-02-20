---
inclusion: manual
---

# AWS Stack Protection Rules

## Stack Naming Convention

**Primary Working Stack**: `aws-drs-orchestration-qa`
- AWS Account: `438465159935`
- Region: `us-east-1`
- Stack ARN: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestration-qa/ae2732a0-0da7-11f1-81ab-0ebf70dc8dab`
- This is the main working environment
- All development and testing happens here
- S3 Deployment Bucket: `aws-drs-orchestration-qa`
- API Endpoint: `https://k8uzkghqrf.execute-api.us-east-1.amazonaws.com/qa`
- CloudFront URL: `https://d2km02vao8dqje.cloudfront.net`
- Nested Stacks:
  - DatabaseStack: `aws-drs-orchestration-qa-DatabaseStack-1MY9XMZ4LI7DQ`
  - NotificationStack: `aws-drs-orchestration-qa-NotificationStack-O9MFLSH6IP5U`
  - LambdaStack: `aws-drs-orchestration-qa-LambdaStack-4AU80AY53S7T`
  - StepFunctionsStack: `aws-drs-orchestration-qa-StepFunctionsStack-1JI5C6MSZ243F`
  - ApiAuthStack: `aws-drs-orchestration-qa-ApiAuthStack-H3JNU260ZT6U`
  - ApiGatewayCoreStack: `aws-drs-orchestration-qa-ApiGatewayCoreStack-10G1O9XGTTLWL`
  - ApiGatewayResourcesStack: `aws-drs-orchestration-qa-ApiGatewayResourcesStack-8NRG9RV4E2L9`
  - ApiGatewayCoreMethodsStack: `aws-drs-orchestration-qa-ApiGatewayCoreMethodsStack-U5WVD72NA5HV`
  - ApiGatewayInfrastructureMethodsStack: `aws-drs-orchestration-qa-ApiGatewayInfrastructureMethodsStack-3F6359CJ219S`
  - ApiGatewayOperationsMethodsStack: `aws-drs-orchestration-qa-ApiGatewayOperationsMethodsStack-EFJQXPVTXR3Q`
  - ApiGatewayDeploymentStack: `aws-drs-orchestration-qa-ApiGatewayDeploymentStack-1E6CGF61XYWA3`
  - EventBridgeStack: `aws-drs-orchestration-qa-EventBridgeStack-1MIBA851ECMMR`
  - FrontendStack: `aws-drs-orchestration-qa-FrontendStack-BRP6S2Y63M1W`
  - WAFStack: `aws-drs-orchestration-qa-WAFStack-1FCIM8KKTSR1H`

**Legacy Stack (UPDATE_ROLLBACK_FAILED)**: `aws-drs-orchestration-test`
- Status: UPDATE_ROLLBACK_FAILED (do not use)
- Stack ARN: `arn:aws:cloudformation:us-east-1:438465159935:stack/aws-drs-orchestration-test/e1e00cb0-fe49-11f0-a956-0ef4995d315b`

## Current Working Environment

**Always deploy to**: `qa` environment
```bash
./scripts/deploy.sh qa
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
- Separate API Gateway deployment

**Supported Environments**: `dev`, `test`, `qa`, `uat`, `prod`

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
