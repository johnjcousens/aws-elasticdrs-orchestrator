# Manual Test Scripts

Manual test scripts for AWS DRS Orchestration API and UI testing.

## Setup

These test scripts require your stack's configuration values. Get them from CloudFormation outputs:

```bash
# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name your-stack-name \
  --query 'Stacks[0].Outputs' \
  --output table
```

## Configuration

Replace placeholder values in test scripts with your actual values:

| Placeholder | CloudFormation Output | Description |
|-------------|----------------------|-------------|
| `***API_GATEWAY_ID***` | ApiGatewayId | API Gateway REST API ID |
| `***USER_POOL_ID***` | UserPoolId | Cognito User Pool ID |
| `***CLIENT_ID***` | UserPoolClientId | Cognito App Client ID |
| `***CLOUDFRONT_ID***` | CloudFrontDistributionId | CloudFront Distribution ID |
| `***TEST_PASSWORD***` | (your test user password) | Test user password |

## Example: Update test-api-simple.sh

```bash
# Before (placeholder)
USER_POOL_ID="***USER_POOL_ID***"
CLIENT_ID="***CLIENT_ID***"

# After (your values)
USER_POOL_ID="us-east-1_ABC123XYZ"
CLIENT_ID="1a2b3c4d5e6f7g8h9i0j"
```

## Running Tests

### API Tests

```bash
# Simple API test
./test-api-simple.sh

# All endpoints test
./test-all-endpoints.sh

# Protection group API test
./test-protection-group-api.sh
```

### UI Tests (Node.js)

```bash
# Install dependencies
npm install axios

# Run UI CRUD test
node test-ui-crud-comprehensive.js

# Run detailed CRUD test
node test-detailed-crud.js
```

### Python Tests

```bash
# Install dependencies
pip install boto3 requests

# Run SRP authentication test
python test-api-srp.py
```

## Test Categories

### API Endpoint Tests
- `test-all-endpoints.sh` - Test all API endpoints
- `test-critical-endpoints.sh` - Test critical endpoints only
- `test-api-simple.sh` - Simple API connectivity test

### CRUD Tests
- `test-detailed-crud.js` - Detailed CRUD operations test
- `test-ui-crud-comprehensive.js` - Comprehensive UI CRUD test

### Integration Tests
- `test-3tier-recovery-setup.sh` - 3-tier recovery plan setup
- `test-drs-tag-sync.js` - DRS tag synchronization test

### Performance Tests
- `test-api-performance.html` - API performance testing UI

## Notes

- These are manual tests for local development and validation
- Do not commit files with actual credentials
- Use environment variables for sensitive data in production
- Test files use placeholder values by default for security
