# Deployment Verification Rule

## After Every Code Change Session

Before marking work complete, ALWAYS verify:

### 1. S3 Bucket Has Latest Code
```bash
# Check timestamps - should be recent
aws s3 ls s3://aws-drs-orchestration/lambda/ --region us-east-1
aws s3 ls s3://aws-drs-orchestration/cfn/ --region us-east-1
aws s3 ls s3://aws-drs-orchestration/frontend/ --region us-east-1
```

### 2. CloudFormation Templates Are Current
```bash
# Verify master template is valid
aws cloudformation validate-template \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --region us-east-1
```

### 3. Can Redeploy from Scratch
**Test command** (don't actually run, just verify it would work):
```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-dev-TEST \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=drs-orchestration \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=SourceBucket,ParameterValue=aws-drs-orchestration \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
```

## Red Flags

**Stop and fix if:**
- ❌ S3 timestamps are old (not from today)
- ❌ Local code differs from S3 artifacts
- ❌ CloudFormation template validation fails
- ❌ Deployed Lambda code doesn't match local

## Recovery Check

**Can you answer YES to:**
- [ ] If stack is deleted, can I redeploy from S3?
- [ ] Are all 7 CloudFormation templates in S3? (master + 6 nested)
- [ ] Are all 5 Lambda source files in S3?
- [ ] Is frontend source code in S3?
- [ ] Is S3 bucket synced with latest code?

**Architecture Verification:**
- [ ] 5 Lambda functions: api-handler, orchestration-stepfunctions, execution-finder, execution-poller, frontend-builder
- [ ] 6 nested stacks: database, lambda, api, step-functions, security, frontend
- [ ] S3 contains source code (NOT zip packages during sync)

If any answer is NO, run:
```bash
./scripts/sync-to-deployment-bucket.sh
```
