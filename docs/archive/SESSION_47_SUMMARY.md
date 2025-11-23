# Session 47: Production Deployment Fixes

**Date:** November 22, 2025
**Status:** ✅ Complete
**Release:** v1.0.3

## Overview

Session 47 resolved three critical production deployment issues discovered after v1.0.2 deployment:
1. Lambda IAM permissions preventing execution history retrieval
2. Frontend vite plugin injecting aws-config.js in dev mode
3. Missing aws-config.js file in S3 bucket

## Issues Resolved

### 1. Lambda IAM Permissions (v1.0.2)

**Problem:** 
- Lambda function couldn't read from DynamoDB ExecutionHistory table
- GET /executions/{id} endpoint returned 500 errors
- Missing DynamoDB:GetItem and DynamoDB:Query permissions

**Solution:**
- Updated `cfn/lambda-stack.yaml` with proper IAM policy
- Deployed via CloudFormation: `make deploy-lambda ENVIRONMENT=test`
- Added both GetItem and Query permissions for ExecutionHistory table

**Files Modified:**
- `cfn/lambda-stack.yaml` - Added DynamoDB read permissions

**Deployment:**
```bash
make deploy-lambda ENVIRONMENT=test
```

### 2. Frontend Vite Plugin Dev Mode Fix (v1.0.3)

**Problem:**
- Vite plugin injected aws-config.js script tag in dev mode
- Caused 404 errors during local development
- Plugin should only inject in production builds

**Solution:**
- Modified `frontend/vite-plugin-inject-config.ts`
- Added `if (isProd)` check to skip injection in dev mode
- Rebuilt and deployed frontend: v1.0.3

**Files Modified:**
- `frontend/vite-plugin-inject-config.ts` - Added dev mode check
- `frontend/package.json` - Bumped to v1.0.3

**Deployment:**
```bash
cd frontend
npm version patch  # v1.0.3
./build.sh
make deploy-frontend ENVIRONMENT=test
```

### 3. Missing aws-config.js File

**Problem:**
- CloudFormation Custom Resource failed to create aws-config.js
- File never uploaded to S3 bucket
- Browser received 404 for aws-config.js, causing "Unexpected token '<'" error

**Solution:**
- Manually created aws-config.js with correct window.AWS_CONFIG format
- Uploaded to S3: `s3://drs-orchestration-fe-438465159935-test/aws-config.js`
- Invalidated CloudFront cache

**Manual Steps:**
```bash
# Create file
cat > /tmp/aws-config.js << 'EOF'
window.AWS_CONFIG = {
  "region": "us-east-1",
  "userPoolId": "us-east-1_wfyuacMBX",
  "userPoolClientId": "48fk7bjefk88aejr1rc7dvmbv0",
  "identityPoolId": "us-east-1:cba6909d-6e78-4dbf-aaf3-a17f9dfc1d46",
  "apiEndpoint": "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test"
};
EOF

# Upload to S3
aws s3 cp /tmp/aws-config.js \
  s3://drs-orchestration-fe-438465159935-test/aws-config.js \
  --content-type "application/javascript"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E46O075T9AHF3 \
  --paths "/*"
```

## Deployment Timeline

1. **Lambda IAM Fix** - Deployed via CloudFormation (v1.0.2 update)
2. **Frontend v1.0.3** - Built and deployed to S3
3. **aws-config.js** - Manually created and uploaded to S3
4. **CloudFront Invalidation** - Full cache clear (/* path)

## Verification

### Lambda IAM Permissions
```bash
# Verify Lambda can read from DynamoDB
aws lambda get-policy --function-name drs-orchestration-api-handler-test

# Check GET /executions/{id} endpoint
curl -H "Authorization: Bearer $TOKEN" \
  https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/executions/{id}
```

### Frontend Deployment
```bash
# Verify aws-config.js exists in S3
aws s3 ls s3://drs-orchestration-fe-438465159935-test/aws-config.js

# Verify CloudFront serves file correctly
curl -I https://d1wfyuosowt0hl.cloudfront.net/aws-config.js
# Should return: HTTP/1.1 200 OK

# Verify file content
curl https://d1wfyuosowt0hl.cloudfront.net/aws-config.js
# Should show: window.AWS_CONFIG = { ... }
```

### Browser Verification
1. Clear browser cache (Cmd+Shift+R or Ctrl+Shift+R)
2. Open: https://d1wfyuosowt0hl.cloudfront.net/login
3. Check console - no "Unexpected token '<'" errors
4. Should see: "✅ AWS Config loaded successfully"

## Git Commits

1. **e2c1f7a** - fix(frontend): Skip aws-config.js injection in dev mode
2. **40cac85** - docs: Document IAM permissions fix for DRS integration
3. **2a5fde8** - docs: Add Session 47 history checkpoint and Azure research

## Technical Improvements

### Custom Resource Issue
The CloudFormation Custom Resource Lambda that should create aws-config.js has a bug. Future fix needed:
- Custom Resource Lambda handler needs debugging
- Should automatically create aws-config.js during stack deployment
- For now, manual creation is documented workaround

### CloudFront Caching
CloudFront aggressive caching caused deployment verification issues:
- Initial invalidation of single file (/aws-config.js) insufficient
- Required full invalidation (/*) including index.html
- Users must clear browser cache after invalidation completes

## Lessons Learned

1. **IAM Permissions:** Always verify Lambda has required DynamoDB permissions in CloudFormation
2. **Dev vs Prod:** Vite plugins must check build environment before injecting assets
3. **Custom Resources:** Manual verification needed when Custom Resources fail silently
4. **Cache Invalidation:** Full CloudFront invalidation (/*) more reliable than single files
5. **Browser Cache:** Users need clear instructions to clear browser cache after deployments

## Production URLs

- **CloudFront:** https://d1wfyuosowt0hl.cloudfront.net/
- **API Gateway:** https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test
- **Cognito User Pool:** us-east-1_wfyuacMBX

## Next Steps

1. **Fix Custom Resource Lambda** - Debug why aws-config.js creation fails
2. **Automated Testing** - Add E2E test for execution history endpoint
3. **Documentation** - Update deployment guide with manual aws-config.js workaround
4. **Monitoring** - Add CloudWatch alarms for Lambda IAM permission errors

## References

- **Previous Session:** [SESSION_46_SUMMARY.md](./SESSION_46_SUMMARY.md)
- **IAM Fix Details:** [SESSION_47_IAM_PERMISSIONS_FIX.md](./SESSION_47_IAM_PERMISSIONS_FIX.md)
- **Issue Resolution:** [SESSION_47_ISSUE_RESOLUTION.md](./SESSION_47_ISSUE_RESOLUTION.md)
- **Session Checkpoint:** [checkpoint_session_20251122_180949_d329da_2025-11-22_18-09-49.md](../history/checkpoints/checkpoint_session_20251122_180949_d329da_2025-11-22_18-09-49.md)
