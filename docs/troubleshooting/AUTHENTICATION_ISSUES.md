# Authentication Issues Troubleshooting

## Overview

This guide consolidates all authentication-related troubleshooting for the DR Orchestration platform.

## Common Issues

### 1. 401 Unauthorized Error

**Symptoms**:
- Frontend shows: `GET https://[api-endpoint]/accounts/targets 401 (Unauthorized)`
- Console shows: `Authentication error - token expired or invalid`

**Root Causes**:
1. Not signed in - User session doesn't exist
2. Token expired - Cognito tokens expire after 45 minutes
3. Token refresh failed - Automatic token refresh encountered an error
4. API Gateway misconfiguration - Authorizer not properly configured

**Quick Fix**:
1. Sign out and sign back in
2. If that doesn't work, clear browser cache and sign in again

**Detailed Steps**: See [401 Unauthorized Error](#401-unauthorized-detailed-steps) below

### 2. API Authentication Context String Error

**Symptoms**:
- API returns 500 Internal Server Error
- CloudWatch logs show: `AttributeError: 'str' object has no attribute 'get'`
- Error occurs in `auth_context.get("claims", {})`

**Root Cause**:
API Gateway Cognito authorizer passes `requestContext.authorizer` as a JSON string instead of a parsed dictionary.

**Solution**:
The Lambda handler now includes JSON parsing logic to handle both formats:

```python
# Handle case where authorizer context might be a JSON string
if isinstance(auth_context, str):
    try:
        auth_context = json.loads(auth_context)
    except (json.JSONDecodeError, TypeError):
        print(f"Failed to parse auth_context as JSON: {auth_context}")
        auth_context = {}

claims = auth_context.get("claims", {})
```

**Status**: ✅ Fixed in `lambda/api-handler/index.py`

---

## 401 Unauthorized Detailed Steps

### Diagnostic Steps

#### Check 1: Verify You're Signed In

1. Open DevTools (F12) → Application tab
2. Look under "Local Storage" → your domain
3. Look for keys starting with `CognitoIdentityServiceProvider`
4. If missing → You're not signed in

#### Check 2: Inspect Failed Request

1. Open DevTools (F12) → Network tab
2. Find the failed request (shows red with 401 status)
3. Click on it → Headers tab
4. Look for `Authorization` header under "Request Headers"
5. Should show: `Authorization: Bearer eyJraWQ...` (long JWT token)
6. If missing → Token not being sent

#### Check 3: Verify Token Format

If Authorization header exists:
1. Copy the token value (everything after "Bearer ")
2. Go to https://jwt.io
3. Paste the token
4. Check "exp" (expiration) claim in decoded payload
5. Compare to current Unix timestamp
6. If expired → Token needs refresh

#### Check 4: Check Console for Errors

Look for these error messages:
- `❌ AWS_CONFIG not available` → Configuration loading failed
- `Error fetching auth token` → Amplify authentication issue
- `Invalid JWT format` → Token corruption
- `Authentication required. Please sign in again.` → Session expired

### Common Scenarios

#### Scenario 1: Token Expired After Inactivity

**Symptoms**: 
- Was working fine, then suddenly 401 errors
- Haven't used the app for 45+ minutes

**Solution**:
- Sign out and sign back in
- Tokens automatically refresh every 50 minutes if you're active
- After 4 hours of inactivity, you're automatically signed out

#### Scenario 2: Fresh Deployment

**Symptoms**:
- Just deployed new version
- Getting 401 on all requests

**Solution**:
1. Clear browser cache (DevTools → Application → Clear storage)
2. Hard refresh (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
3. Sign in again

#### Scenario 3: API Gateway Authorizer Issue

**Symptoms**:
- All users getting 401 errors
- Even after fresh sign-in

**Solution**:
Check API Gateway configuration:

```bash
# Get User Pool ID from CloudFormation
aws cloudformation describe-stacks \
  --stack-name hrp-drs-tech-adapter-api-auth-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text

# Verify API Gateway authorizer
aws apigateway get-authorizers \
  --rest-api-id <API_ID> \
  --query 'items[?name==`hrp-drs-tech-adapter-cognito-authorizer-dev`]'
```

Verify:
- Authorizer type is `COGNITO_USER_POOLS`
- ProviderARNs matches your User Pool ARN
- IdentitySource is `method.request.header.Authorization`

### Advanced Debugging

#### Enable Verbose Logging

Add to browser console:
```javascript
localStorage.setItem('aws-amplify-debug', 'true');
```

Refresh page and check console for detailed Amplify logs.

#### Manual Token Test

1. Get your token from DevTools → Application → Local Storage
2. Look for key ending in `.idToken`
3. Copy the value
4. Test with curl:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  https://YOUR_API_ENDPOINT/accounts/targets
```

If curl works but browser doesn't → Frontend issue
If curl also fails → Backend/API Gateway issue

#### Check API Gateway Logs

```bash
# Enable CloudWatch logs for API Gateway
aws apigateway update-stage \
  --rest-api-id <API_ID> \
  --stage-name dev \
  --patch-operations \
    op=replace,path=/accessLogSettings/destinationArn,value=<LOG_GROUP_ARN> \
    op=replace,path=/accessLogSettings/format,value='$context.requestId'

# View logs
aws logs tail /aws/apigateway/drs-orchestration-dev --follow
```

Look for:
- `Unauthorized` → Authorizer rejecting token
- `Missing Authentication Token` → Authorization header not sent
- `Invalid token` → Token format issue

## Configuration Reference

### Token Lifetimes (api-auth-stack.yaml)

```yaml
UserPoolClient:
  Properties:
    RefreshTokenValidity: 30        # 30 days
    AccessTokenValidity: 45         # 45 minutes
    IdTokenValidity: 45             # 45 minutes
```

### Auto-Refresh Settings (AuthContext.tsx)

```typescript
const INACTIVITY_TIMEOUT = 4 * 60 * 60 * 1000;  // 4 hours
const TOKEN_REFRESH_TIME = 50 * 60 * 1000;      // 50 minutes
```

## Prevention

### For Users

1. **Stay active**: The app refreshes tokens every 50 minutes if you're using it
2. **Don't share tabs**: Each browser tab needs its own session
3. **Use one account**: Don't sign in with multiple accounts in same browser

### For Developers

1. **Token refresh is automatic**: AuthContext handles this
2. **Inactivity timeout**: 4 hours (configurable in AuthContext.tsx)
3. **Token lifetime**: 45 minutes (configurable in api-auth-stack.yaml)

## Still Having Issues?

1. Check CloudWatch logs for Lambda function errors
2. Verify Cognito User Pool configuration
3. Ensure API Gateway deployment is up to date
4. Contact your administrator with:
   - Browser console logs
   - Network tab screenshot showing failed request
   - Your username (NOT password)
   - Timestamp when error occurred
