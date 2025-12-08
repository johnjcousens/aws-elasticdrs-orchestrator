# ✅ Redeployment Ready

**Status**: Your deployment CAN be fully reproduced from S3

## Single Command to Redeploy Everything

```bash
aws cloudformation create-stack \
  --stack-name drs-orchestration-dev \
  --template-url https://s3.amazonaws.com/aws-drs-orchestration/cfn/master-template.yaml \
  --parameters \
    ParameterKey=ProjectName,ParameterValue=drs-orchestration \
    ParameterKey=Environment,ParameterValue=dev \
    ParameterKey=SourceBucket,ParameterValue=aws-drs-orchestration \
    ParameterKey=AdminEmail,ParameterValue=admin@example.com \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --profile 438465159935_AdministratorAccess
```

**Time**: 20-30 minutes  
**Creates**: Everything (6 Lambda functions, 2 state machines, 3 DynamoDB tables, API Gateway, Cognito, S3, CloudFront)

## What's Protected in S3

**Bucket**: `s3://aws-drs-orchestration`

✅ **7 CloudFormation templates** (validated and working)
✅ **8 Lambda packages** (current code)
✅ **Frontend source** (React app)

## Keep Synced

After any local code changes:

```bash
# Sync everything to S3
./scripts/sync-to-deployment-bucket.sh

# Then update the running stack
./scripts/sync-to-deployment-bucket.sh --deploy-cfn
```

## That's It

Your S3 bucket has everything needed. If the stack is deleted, run the single command above to recreate it exactly as it is now.
