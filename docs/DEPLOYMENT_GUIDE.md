# Frontend Deployment Guide

This guide provides comprehensive instructions for deploying the AWS DRS Orchestration React frontend to S3 and CloudFront.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Deployment Options](#deployment-options)
4. [Configuration Management](#configuration-management)
5. [Build Optimization](#build-optimization)
6. [Troubleshooting](#troubleshooting)
7. [Rollback Procedures](#rollback-procedures)
8. [Performance Tips](#performance-tips)
9. [CI/CD Integration](#cicd-integration)

---

## Prerequisites

### Required Tools

1. **AWS CLI** - Version 2.x or later
   ```bash
   aws --version
   # Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
   ```

2. **Node.js and npm** - Version 18.x or later
   ```bash
   node --version
   npm --version
   # Install: https://nodejs.org/
   ```

3. **jq** - JSON processor (for parsing CloudFormation outputs)
   ```bash
   jq --version
   # macOS: brew install jq
   # Linux: apt-get install jq or yum install jq
   ```

### AWS Prerequisites

1. **AWS Credentials**
   - Configure AWS CLI with credentials:
     ```bash
     aws configure
     ```
   - For Amazon employees using Ada:
     ```bash
     ada credentials update --account=YOUR_ACCOUNT --role=YOUR_ROLE
     ```

2. **CloudFormation Stack**
   - Ensure the CloudFormation stack is deployed and in CREATE_COMPLETE or UPDATE_COMPLETE status
   - Default stack name: `DRS-Orchestration`
   - The stack must have these outputs:
     - `WebsiteBucket` - S3 bucket for hosting
     - `CloudFrontDistributionId` - CloudFront distribution ID
     - `CloudFrontUrl` - CloudFront URL
     - `ApiEndpoint` - API Gateway endpoint
     - `UserPoolId` - Cognito User Pool ID
     - `UserPoolClientId` - Cognito User Pool Client ID
     - `IdentityPoolId` - Cognito Identity Pool ID

3. **IAM Permissions**
   The AWS credentials must have permissions for:
   - `cloudformation:DescribeStacks`
   - `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`
   - `cloudfront:CreateInvalidation`

### Verify Prerequisites

Run this command to verify all prerequisites:

```bash
# Check AWS CLI
aws --version

# Check Node.js and npm
node --version && npm --version

# Check jq
jq --version

# Check AWS credentials
aws sts get-caller-identity

# Check CloudFormation stack
aws cloudformation describe-stacks --stack-name DRS-Orchestration
```

---

## Quick Start

### Option 1: Using npm Scripts (Recommended)

From the `frontend/` directory:

```bash
# Deploy to default stack (DRS-Orchestration) in production mode
npm run deploy

# Deploy to development environment
npm run deploy:dev

# Deploy to staging environment
npm run deploy:staging

# Deploy to production environment (explicit)
npm run deploy:prod
```

### Option 2: Using Deployment Script Directly

From the project root:

```bash
# Deploy with default settings
./scripts/deploy-frontend.sh

# Deploy to specific stack and environment
./scripts/deploy-frontend.sh MY-STACK-NAME dev

# Examples
./scripts/deploy-frontend.sh DRS-Orchestration prod
./scripts/deploy-frontend.sh DRS-Orchestration-Test staging
```

---

## Deployment Options

### Environment Modes

The deployment script supports three environment modes:

1. **Production (prod)** - Default
   - Full optimization enabled
   - Console logs removed
   - No source maps
   - Minification with esbuild

2. **Staging (staging)**
   - Similar to production
   - May include additional debugging options

3. **Development (dev)**
   - Faster builds
   - Debug-friendly
   - May include source maps

### Command Parameters

```bash
./scripts/deploy-frontend.sh [STACK_NAME] [ENVIRONMENT]
```

- **STACK_NAME** - CloudFormation stack name (default: `DRS-Orchestration`)
- **ENVIRONMENT** - Environment mode: `dev`, `staging`, or `prod` (default: `prod`)

### Examples

```bash
# Production deployment to default stack
./scripts/deploy-frontend.sh

# Development deployment
./scripts/deploy-frontend.sh DRS-Orchestration dev

# Staging deployment to custom stack
./scripts/deploy-frontend.sh DRS-Orchestration-Staging staging

# Multiple environments with different stacks
./scripts/deploy-frontend.sh DRS-Dev dev
./scripts/deploy-frontend.sh DRS-Staging staging
./scripts/deploy-frontend.sh DRS-Production prod
```

---

## Configuration Management

### Automated Configuration Injection

The deployment script automatically:

1. **Extracts** CloudFormation stack outputs
2. **Generates** `frontend/src/aws-config.ts` with actual values
3. **Creates** backup as `aws-config.ts.backup`
4. **Builds** frontend with injected configuration
5. **Deploys** to S3 and CloudFront

### Configuration Structure

The generated `aws-config.ts` includes:

```typescript
export const awsConfig = {
  Auth: {
    Cognito: {
      region: 'us-west-2',
      userPoolId: 'us-west-2_ABC123',
      userPoolClientId: '1234567890abcdefghijk',
      identityPoolId: 'us-west-2:12345678-1234-1234-1234-123456789012',
      loginWith: { email: true }
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

### Manual Configuration (Development Only)

For local development without deployment:

1. Get CloudFormation outputs:
   ```bash
   aws cloudformation describe-stacks \
     --stack-name DRS-Orchestration \
     --query 'Stacks[0].Outputs' \
     --output table
   ```

2. Manually edit `frontend/src/aws-config.ts` with the values

3. Run local development server:
   ```bash
   cd frontend
   npm run dev
   ```

---

## Build Optimization

### Optimization Features

The Vite configuration includes:

1. **Code Splitting**
   - Vendor chunks separated by library
   - React/React-DOM in separate chunk
   - Material-UI core and extended in separate chunks
   - AWS Amplify in separate chunk

2. **Minification**
   - esbuild for fast minification
   - Tree-shaking enabled
   - Dead code elimination

3. **Caching Strategy**
   - Static assets: 1-year cache (`public, max-age=31536000, immutable`)
   - index.html: No cache (`no-cache, no-store, must-revalidate`)
   - Source maps: Private, no cache

4. **Bundle Size Targets**
   - JavaScript bundle: < 500KB gzipped
   - Chunk size warning at 500KB
   - Asset inline limit: 4KB

### Build Analysis

To analyze bundle size:

```bash
cd frontend

# Build for production
npm run build

# Check build output
ls -lh dist/assets/

# Get total size
du -sh dist/
```

Expected output structure:
```
dist/
├── assets/
│   ├── index-[hash].js          # Main app bundle
│   ├── vendor-react-[hash].js   # React libraries
│   ├── vendor-mui-core-[hash].js
│   ├── vendor-mui-extended-[hash].js
│   ├── vendor-aws-[hash].js
│   └── vendor-http-[hash].js
└── index.html
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "CloudFormation stack not found"

**Problem**: Stack name is incorrect or doesn't exist.

**Solution**:
```bash
# List available stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[].StackName' \
  --output table

# Verify specific stack
aws cloudformation describe-stacks --stack-name YOUR-STACK-NAME
```

#### 2. "AWS credentials are not configured"

**Problem**: AWS CLI credentials expired or not configured.

**Solution**:
```bash
# For Amazon employees
ada credentials update --account=YOUR_ACCOUNT --role=YOUR_ROLE

# For general AWS users
aws configure

# Verify credentials
aws sts get-caller-identity
```

#### 3. "No outputs found for stack"

**Problem**: CloudFormation stack doesn't have required outputs.

**Solution**:
```bash
# Check stack outputs
aws cloudformation describe-stacks \
  --stack-name DRS-Orchestration \
  --query 'Stacks[0].Outputs'

# If outputs are missing, re-deploy CloudFormation stack
cd cfn
aws cloudformation update-stack \
  --stack-name DRS-Orchestration \
  --template-body file://master-template.yaml \
  --capabilities CAPABILITY_IAM
```

#### 4. "TypeScript compilation failed"

**Problem**: TypeScript errors in frontend code.

**Solution**:
```bash
cd frontend

# Check for TypeScript errors
npx tsc --noEmit

# Fix errors before deploying
# Common fixes:
# - Update type definitions
# - Fix type mismatches
# - Add missing imports
```

#### 5. "Build failed"

**Problem**: npm build command failed.

**Solution**:
```bash
cd frontend

# Clean and reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Try building again
npm run build

# Check for specific errors in output
```

#### 6. "S3 sync failed"

**Problem**: Insufficient S3 permissions or bucket doesn't exist.

**Solution**:
```bash
# Verify bucket exists
aws s3 ls s3://YOUR-BUCKET-NAME/

# Check IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) \
  --action-names s3:PutObject s3:DeleteObject s3:ListBucket \
  --resource-arns arn:aws:s3:::YOUR-BUCKET-NAME/*
```

#### 7. "CloudFront invalidation failed"

**Problem**: Insufficient CloudFront permissions or distribution doesn't exist.

**Solution**:
```bash
# Verify distribution exists
aws cloudfront list-distributions \
  --query 'DistributionList.Items[].Id' \
  --output table

# Check specific distribution
aws cloudfront get-distribution --id YOUR-DISTRIBUTION-ID
```

#### 8. "Changes not visible after deployment"

**Problem**: Browser caching or CloudFront cache not invalidated.

**Solutions**:
```bash
# Hard refresh in browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)

# Check invalidation status
aws cloudfront get-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --id YOUR-INVALIDATION-ID

# Create manual invalidation if needed
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"

# Clear browser cache completely
```

### Debug Mode

For detailed debugging:

```bash
# Enable bash debug mode
bash -x ./scripts/deploy-frontend.sh DRS-Orchestration dev

# Check deployment script logs
cat /tmp/deploy-frontend-*.log  # If logging is enabled
```

---

## Rollback Procedures

### Option 1: Re-deploy Previous Version

If you have the previous code in git:

```bash
# Find previous commit
git log --oneline frontend/

# Checkout previous version
git checkout PREVIOUS_COMMIT_HASH

# Re-deploy
cd frontend
npm run deploy

# Return to current version
git checkout main
```

### Option 2: Use S3 Versioning

If S3 versioning is enabled on the bucket:

```bash
# List object versions
aws s3api list-object-versions \
  --bucket YOUR-BUCKET-NAME \
  --prefix index.html

# Restore specific version
aws s3api copy-object \
  --bucket YOUR-BUCKET-NAME \
  --copy-source YOUR-BUCKET-NAME/index.html?versionId=VERSION_ID \
  --key index.html

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/*"
```

### Option 3: Emergency Static Page

Deploy a maintenance page:

```bash
# Create simple maintenance page
cat > /tmp/maintenance.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Maintenance</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; }
        h1 { color: #FF9900; }
    </style>
</head>
<body>
    <h1>System Maintenance</h1>
    <p>We'll be back shortly. Thank you for your patience.</p>
</body>
</html>
EOF

# Upload to S3
aws s3 cp /tmp/maintenance.html s3://YOUR-BUCKET-NAME/index.html

# Invalidate cache
aws cloudfront create-invalidation \
  --distribution-id YOUR-DISTRIBUTION-ID \
  --paths "/index.html"
```

---

## Performance Tips

### 1. Bundle Size Optimization

- **Audit bundle size**:
  ```bash
  cd frontend
  npm run build
  npx vite-bundle-visualizer dist/stats.html
  ```

- **Tree-shake unused code**:
  - Import only needed components
  - Use named imports: `import { Button } from '@mui/material'`
  - Avoid importing entire libraries

### 2. Caching Strategy

- **Leverage CloudFront caching**:
  - Static assets cached for 1 year
  - index.html never cached (always fresh)
  - Update cache headers in deployment script if needed

### 3. Image Optimization

- Use WebP format when possible
- Compress images before deployment
- Consider using CloudFront image optimization

### 4. Code Splitting

Current configuration splits:
- React libraries (vendor-react)
- Material-UI core (vendor-mui-core)
- Material-UI extended (vendor-mui-extended)
- AWS Amplify (vendor-aws)
- HTTP client (vendor-http)

### 5. Monitoring

Monitor key metrics:
- **Time to First Byte (TTFB)**: < 200ms
- **First Contentful Paint (FCP)**: < 1.5s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Total Bundle Size**: < 500KB gzipped

Use CloudWatch to monitor CloudFront metrics:
- Requests
- Bytes downloaded
- Error rates
- Cache hit ratio

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Deploy Frontend
        run: |
          cd frontend
          npm ci
          npm run deploy:prod
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        AWS_REGION = 'us-west-2'
        STACK_NAME = 'DRS-Orchestration'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                }
            }
        }
        
        stage('Deploy') {
            steps {
                withAWS(credentials: 'aws-credentials') {
                    sh './scripts/deploy-frontend.sh ${STACK_NAME} prod'
                }
            }
        }
    }
    
    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed!'
        }
    }
}
```

---

## Additional Resources

- [AWS CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Vite Build Optimization](https://vitejs.dev/guide/build.html)
- [React Production Build](https://react.dev/learn/start-a-new-react-project#building-for-production)
- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudFormation stack events for infrastructure issues
3. Check CloudWatch logs for application errors
4. Review browser console for frontend errors

---

**Last Updated**: November 8, 2025
**Version**: 1.0.0
