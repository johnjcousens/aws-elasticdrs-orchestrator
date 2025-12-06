# API Gateway Authentication Investigation

**Date**: December 6, 2024  
**Status**: ✅ RESOLVED - Authentication Working

---

## Issue Summary

**Initial Problem**: API Gateway returning 401 Unauthorized  
**Root Cause**: Testing without proper JWT token from Cognito  
**Resolution**: Implemented correct USER_PASSWORD_AUTH flow  
**Result**: ✅ Authentication fully operational

---

## Working Authentication Flow

### Step 1: Obtain JWT Token from Cognito

```bash
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 48fk7bjefk88aejr1rc7dvmbv0 \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD='IiG2b1o+D$' \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)
```

**Token Details**:
- Type: JWT ID Token
- Issuer: Cognito User Pool us-east-1_wfyuacMBX
- Expiration: 1 hour (3600 seconds)
- Claims: sub, email, cognito:username, token_use=id

### Step 2: Call API with Bearer Token

```bash
curl -X GET \
  "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json"
```

**Response**: HTTP 200 with full server list

---

## Test Results

### ✅ Successful API Call

**Endpoint**: GET /drs/source-servers?region=us-east-1  
**Status Code**: 200  
**Response Time**: <500ms  

**Response Data**:
```json
{
  "region": "us-east-1",
  "initialized": true,
  "servers": [
    {
      "sourceServerID": "s-3c1730a9e0771ea14",
      "hostname": "EC2AMAZ-4IMB9PN",
      "state": "READY_FOR_RECOVERY",
      "replicationState": "CONTINUOUS",
      "lagDuration": "P0D",
      "lastSeen": "2025-12-06T19:40:28.422993+00:00",
      "assignedToProtectionGroup": null,
      "selectable": true
    }
    // ... 5 more servers
  ],
  "totalCount": 6,
  "availableCount": 6,
  "assignedCount": 0
}
```

---

## Configuration Details

### Cognito User Pool
- **Pool ID**: us-east-1_wfyuacMBX
- **Region**: us-east-1
- **Client ID**: 48fk7bjefk88aejr1rc7dvmbv0
- **Client Name**: drs-orchestration-client
- **Auth Flow**: USER_PASSWORD_AUTH
- **MFA**: Disabled

### API Gateway
- **API ID**: 9cowuz4azi
- **API Name**: drs-orchestration-api-test
- **Stage**: test
- **Authorizer**: Cognito User Pool Authorizer
- **Authorization**: Bearer token in Authorization header

### Test User
- **Username**: testuser@example.com
- **Password**: IiG2b1o+D$
- **Status**: CONFIRMED
- **Email Verified**: true

---

## Frontend Integration

The frontend uses AWS Amplify for Cognito authentication:

**Configuration** (`frontend/public/aws-config.js`):
```javascript
window.AWS_CONFIG = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_wfyuacMBX',
  userPoolWebClientId: '48fk7bjefk88aejr1rc7dvmbv0',
  apiEndpoint: 'https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test'
};
```

**Authentication Flow**:
1. User enters credentials on LoginPage
2. Amplify calls Cognito InitiateAuth
3. Cognito returns JWT tokens (IdToken, AccessToken, RefreshToken)
4. Frontend stores tokens in AuthContext
5. API client includes IdToken in Authorization header
6. API Gateway validates token with Cognito

---

## Key Learnings

### What Worked
✅ USER_PASSWORD_AUTH flow for programmatic access  
✅ Bearer token in Authorization header  
✅ Cognito User Pool Authorizer on API Gateway  
✅ JWT ID Token (not Access Token) for API calls  

### Common Pitfalls Avoided
❌ Using Access Token instead of ID Token  
❌ Missing "Bearer " prefix in Authorization header  
❌ Expired tokens (1 hour expiration)  
❌ Wrong User Pool or Client ID  

---

## Testing Commands

### Quick Test Script
```bash
#!/bin/bash
# test-api-auth.sh

# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 48fk7bjefk88aejr1rc7dvmbv0 \
  --auth-parameters USERNAME=testuser@example.com,PASSWORD='IiG2b1o+D$' \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# Test API endpoints
echo "Testing /drs/source-servers..."
curl -s -X GET \
  "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/drs/source-servers?region=us-east-1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  | jq '.totalCount'

echo "Testing /protection-groups..."
curl -s -X GET \
  "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/protection-groups" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  | jq 'length'

echo "Testing /recovery-plans..."
curl -s -X GET \
  "https://9cowuz4azi.execute-api.us-east-1.amazonaws.com/test/recovery-plans" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  | jq 'length'
```

---

## Next Steps

### ✅ Authentication Resolved - Proceed with Testing

**Phase 4C**: Create test data (Protection Groups, Recovery Plans)  
**Phase 4D**: Run automated E2E test  
**Phase 4E**: Manual UI testing  
**Phase 4F**: Playwright E2E tests  

---

## Conclusion

**Status**: ✅ RESOLVED  
**Impact**: Unblocks all Phase 4 testing  
**Confidence**: HIGH - Authentication working as designed  

The authentication system is fully operational. The initial 401 errors were due to testing without proper JWT tokens. Once the correct Cognito authentication flow was implemented, all API calls succeeded.

**Ready to proceed with comprehensive E2E testing.**
