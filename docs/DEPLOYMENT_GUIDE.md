# Frontend Deployment Guide

This guide explains how the AWS DRS Orchestration React frontend is automatically deployed through CloudFormation Custom Resources.

## Overview

The frontend deployment is **fully automated** through CloudFormation. When you create or update the CloudFormation stack, a Custom Resource Lambda function automatically:

1. Extracts AWS configuration from CloudFormation outputs (Cognito, API Gateway, Region)
2. Injects configuration into the React app's `aws-config.ts`
3. Builds the React application with `npm run build`
4. Uploads the production build to S3 with proper cache headers
5. Invalidates the CloudFront cache
6. Provides the CloudFront URL for immediate access

**No external scripts or manual configuration needed!**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Methods](#deployment-methods)
3. [How It Works](#how-it-works)
4. [Configuration Management](#configuration-management)
5. [Build Optimization](#build-optimization)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Topics](#advanced-topics)

---

## Prerequisites

### AWS Requirements

1. **AWS Account** with appropriate permissions
2. **AWS CLI** configured (for stack deployment)
3. **S3 Bucket** for Lambda deployment packages
4. **IAM Permissions**:
   - `cloudformation:*`
   - `lambda:*`
   - `s3:*`
   - `cloudfront:*`
   - `cognito-idp:*`
   - `apigateway:*`

### Local Development

For local development only (not required for deployment):
- **Node.js 18+** and **npm**
- **TypeScript** for type checking

---

## Deployment Methods

### Method 1: Initial Stack Creation (Recommended)

Deploy the complete CloudFormation stack, which automatically builds and deploys the frontend:

```bash
# 1. Package Lambda functions
cd AWS-DRS-Orchestration
./scripts/package-lambdas.sh your-deployment-bucket

# 2. Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name DRS-Orchestration \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=AdminEmail,ParameterValue=your@email.com \
    ParameterKey=LambdaCodeBucket,ParameterValue=your-deployment-bucket \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2

# 3. Monitor deployment (wait ~10-15 minutes)
aws cloudformation wait stack-create-complete --stack-name DRS-Orchestration

# 4. Get CloudFront URL
aws cloudformation describe-stacks \
  --stack-name DRS-Orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

**That's it!** The frontend is automatically built and deployed.

### Method 2: Stack Update (Frontend Changes)

When you make changes to the frontend code and want to redeploy:

```bash
# 1. Update Lambda package with new frontend code
./scripts/package-lambdas.sh your-deployment-bucket

# 2. Update CloudFormation stack (triggers rebuild)
aws cloudformation update-stack \
  --stack-name DRS-Orchestration \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=AdminEmail,UsePreviousValue=true \
    ParameterKey=LambdaCodeBucket,UsePreviousValue=true \
  --capabilities CAPABILITY_NAMED_IAM

# 3. Wait for update
aws cloudformation wait stack-update-complete --stack-name DRS-Orchestration
```

The Custom Resource Lambda detects the update and automatically rebuilds the frontend.

### Method 3: Using Frontend Source from S3

For production deployments, upload frontend source to S3:

```bash
# 1. Create zip of frontend source
cd AWS-DRS-Orchestration
zip -r frontend.zip frontend/ -x "frontend/node_modules/*" -x "frontend/dist/*"

# 2. Upload to S3
aws s3 cp frontend.zip s3://your-deployment-bucket/frontend.zip

# 3. Deploy/update stack with frontend source parameters
aws cloudformation create-stack \
  --stack-name DRS-Orchestration \
  --template-body file://cfn/master-template.yaml \
  --parameters \
    ParameterKey=AdminEmail,ParameterValue=your@email.com \
    ParameterKey=LambdaCodeBucket,ParameterValue=your-deployment-bucket \
    ParameterKey=FrontendCodeBucket,ParameterValue=your-deployment-bucket \
    ParameterKey=FrontendCodeKey,ParameterValue=frontend.zip \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## How It Works

### CloudFormation Custom Resource Flow

```
CloudFormation Stack
       ↓
   [Create/Update Event]
       ↓
Frontend Builder Lambda (Custom Resource)
       ↓
   [Check for Frontend Source]
       ├─→ Option 1: Lambda Package (/var/task/frontend)
       ├─→ Option 2: S3 Download (FrontendCodeBucket/FrontendCodeKey)
       └─→ Fallback: Deploy Placeholder HTML
       ↓
   [Inject AWS Config]
   - Extract from CloudFormation ResourceProperties
   - Generate aws-config.ts with actual values
       ↓
   [Build React App]
   - npm ci (install dependencies)
   - npm run build (TypeScript + Vite)
       ↓
   [Upload to S3]
   - dist/ → S3 bucket
   - Cache headers: 1-year for assets, no-cache for index.html
       ↓
   [Invalidate CloudFront]
   - Create invalidation for /*
   - Return invalidation ID
       ↓
   [Complete]
   - CloudFormation receives success
   - Frontend available at CloudFront URL
```

### Custom Resource Lambda

Location: `lambda/frontend-builder/build_and_deploy.py`

**Capabilities:**
- Automatic AWS configuration injection
- React build with TypeScript validation
- S3 upload with optimized cache headers
- CloudFront cache invalidation
- Fallback to placeholder HTML if source unavailable

**Lambda Configuration:**
- Memory: 512 MB (configurable)
- Timeout: 900 seconds (15 minutes for build)
- Runtime: Python 3.12
- Dependencies: boto3, crhelper

---

## Configuration Management

### Automatic Configuration Injection

The Lambda Custom Resource automatically generates `aws-config.ts` with values from CloudFormation:

**Generated File** (`frontend/src/aws-config.ts`):
```typescript
// AWS Configuration - Auto-generated by CloudFormation Custom Resource
// DO NOT EDIT - This file is automatically generated during CloudFormation deployment

export const awsConfig = {
  Auth: {
    Cognito: {
      region: 'us-west-2',
      userPoolId: 'us-west-2_ABC123...',
      userPoolClientId: '1234567890abcdefg...',
      identityPoolId: 'us-west-2:12345678-1234-1234-1234-123456789012',
      loginWith: {
        email: true
      }
    }
  },
  API: {
    REST: {
      DRSOrchestration: {
        endpoint: 'https://abc123.execute-api.us-west-2.amazonaws.com/prod',
        region: 'us-west-2'
      }
    }
  }
};
```

**Configuration Sources:**
- CloudFormation Outputs:
  - `UserPoolId` → Cognito User Pool
  - `UserPoolClientId` → Cognito Client
  - `IdentityPoolId` → Cognito Identity Pool
  - `ApiEndpoint` → API Gateway
  - `Region` → AWS Region

**Benefits:**
- ✅ No manual configuration needed
- ✅ Always in sync with infrastructure
- ✅ Environment-specific values automatically injected
- ✅ No config files to manage

---

## Build Optimization

### Vite Configuration

The React app uses Vite with these optimizations:

**Code Splitting** (`frontend/vite.config.ts`):
```typescript
manualChunks: {
  'vendor-react': ['react', 'react-dom', 'react-router-dom'],
  'vendor-mui-core': ['@mui/material', '@mui/icons-material'],
  'vendor-mui-extended': ['@mui/x-data-grid'],
  'vendor-aws': ['aws-amplify', '@aws-amplify/ui-react'],
  'vendor-http': ['axios']
}
```

**Build Features:**
- esbuild minification (fast builds)
- CSS code splitting
- Asset inlining (< 4KB)
- 500KB chunk size warnings
- Dev server on port 3000

**Bundle Size Targets:**
- JavaScript: < 500KB gzipped
- Initial load: < 3 seconds on 3G
- Lighthouse score: > 90

### Cache Strategy

**S3 + CloudFront Caching:**

| File Type | Cache-Control | Duration | Why |
|-----------|---------------|----------|-----|
| `index.html` | `no-cache, no-store, must-revalidate` | None | Always fetch fresh for SPA routing |
| Static assets (JS/CSS) | `public, max-age=31536000, immutable` | 1 year | Hashed filenames enable long-term caching |
| Images/Fonts | `public, max-age=31536000, immutable` | 1 year | Immutable static resources |

**Benefits:**
- Fast subsequent page loads (cached assets)
- Always fresh app shell (index.html)
- Efficient bandwidth usage
- CloudFront edge caching

---

## Troubleshooting

### Issue 1: Stack Creation Fails on FrontendBuildResource

**Symptom**: CloudFormation stack creation fails with Custom Resource error.

**Causes**:
1. Lambda timeout (build takes > 15 minutes)
2. npm dependencies installation failure
3. TypeScript compilation errors
4. Missing frontend source code

**Solutions**:

```bash
# Check Lambda logs
aws logs tail /aws/lambda/DRS-Orchestration-FrontendBuilder --follow

# Common fixes:
# 1. Increase Lambda timeout in lambda-stack.yaml
Timeout: 900  # 15 minutes

# 2. Pre-install node_modules in Lambda package
cd frontend && npm ci && cd ..
./scripts/package-lambdas.sh your-bucket

# 3. Fix TypeScript errors locally first
cd frontend
npx tsc --noEmit
npm run build
```

### Issue 2: Placeholder HTML Deployed Instead of React App

**Symptom**: CloudFront shows placeholder page with "React App Not Yet Deployed" message.

**Cause**: Frontend source code not available to Lambda.

**Solution**:

```bash
# Option 1: Include frontend in Lambda package
# Ensure package-lambdas.sh includes frontend source

# Option 2: Upload frontend to S3
zip -r frontend.zip frontend/ -x "frontend/node_modules/*"
aws s3 cp frontend.zip s3://your-bucket/frontend.zip

# Update stack with parameters
aws cloudformation update-stack \
  --stack-name DRS-Orchestration \
  --use-previous-template \
  --parameters \
    ParameterKey=FrontendCodeBucket,ParameterValue=your-bucket \
    ParameterKey=FrontendCodeKey,ParameterValue=frontend.zip \
    --capabilities CAPABILITY_NAMED_IAM
```

### Issue 3: Changes Not Visible After Stack Update

**Symptom**: Frontend changes not reflected after CloudFormation update.

**Solutions**:

```bash
# 1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

# 2. Check CloudFront invalidation status
INVALIDATION_ID=$(aws cloudformation describe-stacks \
  --stack-name DRS-Orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`InvalidationId`].OutputValue' \
  --output text)

aws cloudfront get-invalidation \
  --distribution-id YOUR-DIST-ID \
  --id $INVALIDATION_ID

# 3. Manual invalidation if needed
aws cloudfront create-invalidation \
  --distribution-id YOUR-DIST-ID \
  --paths "/*"
```

### Issue 4: TypeScript Compilation Errors

**Symptom**: Build fails with TypeScript errors.

**Solution**:

```bash
# Validate TypeScript locally before deploying
cd frontend
npx tsc --noEmit

# Fix all errors, then rebuild
npm run build

# Verify dist/ created successfully
ls -la dist/
```

### Issue 5: Lambda Out of Memory

**Symptom**: Lambda fails with "Task timed out" or memory errors.

**Solution**:

Update Lambda memory in `cfn/lambda-stack.yaml`:

```yaml
FrontendBuilderFunction:
  Type: AWS::Lambda::Function
  Properties:
    MemorySize: 1024  # Increase from 512MB
    Timeout: 900      # Keep 15 minutes
```

---

## Advanced Topics

### Custom Lambda Layer for Node.js

For faster builds, create a Lambda Layer with Node.js and npm pre-installed:

```bash
# Create layer with Node.js 18
mkdir -p layer/bin
cd layer/bin
wget https://nodejs.org/dist/v18.18.0/node-v18.18.0-linux-x64.tar.xz
tar xf node-v18.18.0-linux-x64.tar.xz
mv node-v18.18.0-linux-x64 nodejs
cd ../..

# Package layer
zip -r nodejs-layer.zip layer/

# Upload and create layer
aws lambda publish-layer-version \
  --layer-name nodejs-18 \
  --zip-file fileb://nodejs-layer.zip \
  --compatible-runtimes python3.12
```

### CI/CD Integration

**GitHub Actions Example**:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'
      - 'cfn/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Package Lambdas
        run: ./scripts/package-lambdas.sh ${{ secrets.DEPLOYMENT_BUCKET }}
      
      - name: Update CloudFormation Stack
        run: |
          aws cloudformation update-stack \
            --stack-name DRS-Orchestration \
            --template-body file://cfn/master-template.yaml \
            --parameters \
              ParameterKey=AdminEmail,UsePreviousValue=true \
              ParameterKey=LambdaCodeBucket,UsePreviousValue=true \
            --capabilities CAPABILITY_NAMED_IAM
```

### Monitoring and Logging

**CloudWatch Logs**:
```bash
# View Lambda build logs
aws logs tail /aws/lambda/DRS-Orchestration-FrontendBuilder --follow --format short

# Filter for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/DRS-Orchestration-FrontendBuilder \
  --filter-pattern "ERROR"
```

**Custom Metrics**:
- Build duration
- Bundle size
- Deployment success/failure rate

---

## Summary

### Key Takeaways

✅ **Fully Automated** - No manual configuration or deployment scripts  
✅ **CloudFormation-Native** - Deployment via Custom Resource  
✅ **Always In Sync** - AWS config automatically injected from CloudFormation outputs  
✅ **Production-Ready** - Optimized build, proper caching, CloudFront CDN  
✅ **Simple Updates** - Just update the CloudFormation stack to redeploy  

### Quick Reference

```bash
# Initial deployment
./scripts/package-lambdas.sh YOUR-BUCKET
aws cloudformation create-stack --stack-name DRS-Orchestration ...

# Update frontend
./scripts/package-lambdas.sh YOUR-BUCKET
aws cloudformation update-stack --stack-name DRS-Orchestration ...

# Get frontend URL
aws cloudformation describe-stacks --stack-name DRS-Orchestration \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontUrl`].OutputValue' \
  --output text
```

---

**Last Updated**: November 8, 2025  
**Version**: 2.0.0 (CloudFormation-First Architecture)
