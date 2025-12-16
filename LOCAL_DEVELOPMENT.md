# Local Development Setup

This guide explains how to run the AWS DRS Orchestration application locally for development and testing, avoiding the need for repeated AWS deployments.

## Overview

The local development setup includes:
- **Mock API Server** (`mock-api-server.js`) - Simulates the AWS Lambda API endpoints
- **Frontend Dev Server** - React app with Vite dev server
- **Authentication Bypass** - Automatic mock authentication for localhost
- **CORS Configuration** - Proper CORS headers for local development

## Quick Start

### 1. Start Development Environment

```bash
# Start both mock API server and frontend dev server
./start-local-dev.sh
```

This will:
- Install dependencies if needed
- Start mock API server on `http://localhost:8000`
- Start frontend dev server on `http://localhost:5173`
- Display available endpoints and usage instructions

### 2. Access the Application

Open your browser to: **http://localhost:5173**

The application will automatically:
- Use local configuration (`aws-config.local.json`)
- Bypass Cognito authentication
- Connect to the mock API server
- Show you as logged in with mock user credentials

### 3. Test Multi-Account Functionality

The mock API includes a default "Current Account" and supports full CRUD operations for target accounts. You can:

- Open Settings (gear icon) → Account Management
- Add new target accounts
- Edit existing accounts
- Validate account configurations
- Delete accounts (except current account)

## Manual Testing

### Test API Endpoints Directly

```bash
# Test the mock API server endpoints
./test-local-api.sh
```

This script tests all target account endpoints and verifies the mock API is working correctly.

### Test Individual Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get target accounts
curl -H "Authorization: Bearer test-token" http://localhost:8000/accounts/targets

# Create target account
curl -X POST -H "Authorization: Bearer test-token" -H "Content-Type: application/json" \
  -d '{
    "accountId": "987654321098",
    "name": "Test Account",
    "description": "Test target account",
    "crossAccountRoleArn": "arn:aws:iam::987654321098:role/TestRole"
  }' \
  http://localhost:8000/accounts/targets
```

## Configuration Files

### Frontend Configuration

**`frontend/public/aws-config.local.json`**
```json
{
  "region": "us-east-1",
  "userPoolId": "us-east-1_LOCALHOST",
  "userPoolClientId": "localhost-client-id",
  "apiEndpoint": "http://localhost:8000"
}
```

### Mock API Server

**`mock-api-server.js`**
- Express.js server with CORS enabled
- Mock authentication middleware
- Full target accounts CRUD API
- DRS quotas and tag sync endpoints
- Request/response logging

## Available Endpoints

### Target Accounts Management
- `GET /accounts/targets` - List all target accounts
- `POST /accounts/targets` - Create new target account
- `PUT /accounts/targets/:id` - Update target account
- `DELETE /accounts/targets/:id` - Delete target account
- `POST /accounts/targets/:id/validate` - Validate target account

### DRS Operations
- `GET /drs/quotas?accountId=:id` - Get DRS quotas for account
- `POST /drs/tag-sync` - Trigger tag synchronization

### Health Check
- `GET /health` - API server health status

## Authentication

### Local Development Mode

When running on `localhost` or `127.0.0.1`, the application automatically:

1. **Frontend**: Uses mock authentication in `AuthContext.tsx`
   - Bypasses Cognito sign-in
   - Creates mock user credentials
   - Skips token validation

2. **API Client**: Uses mock tokens in `api.ts`
   - Sends `Bearer mock-local-dev-token` header
   - Bypasses AWS Amplify session fetching

3. **Mock Server**: Accepts any Bearer token
   - Validates Authorization header exists
   - Creates mock user context
   - Logs all requests for debugging

### Production Mode

When deployed to AWS, the application uses:
- Cognito User Pool authentication
- JWT token validation
- AWS Lambda API Gateway integration

## Development Workflow

### 1. Make Frontend Changes

```bash
# Frontend files are automatically reloaded
# Edit files in frontend/src/
vim frontend/src/components/AccountManagementPanel.tsx
```

### 2. Make API Changes

```bash
# Restart mock server after changes
pkill -f "node mock-api-server.js"
node mock-api-server.js &
```

### 3. Test Changes

```bash
# Test API endpoints
./test-local-api.sh

# Test frontend in browser
open http://localhost:5173
```

## Troubleshooting

### Mock API Server Won't Start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing processes
pkill -f "node mock-api-server.js"

# Check dependencies
npm list express cors
```

### Frontend Won't Connect to API

1. Check browser console for CORS errors
2. Verify API server is running: `curl http://localhost:8000/health`
3. Check `aws-config.local.json` has correct endpoint
4. Verify browser is using localhost (not 127.0.0.1)

### Authentication Issues

1. Check browser console for auth bypass messages
2. Verify you're accessing `http://localhost:5173` (not deployed URL)
3. Clear browser cache and cookies
4. Check `AuthContext.tsx` local development detection

### CORS Issues

The mock server includes comprehensive CORS configuration:
```javascript
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:5173'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'Origin', 'Accept']
}));
```

## Stopping Development Environment

```bash
# Stop all development servers
# Press Ctrl+C in the terminal running start-local-dev.sh

# Or manually kill processes
pkill -f "node mock-api-server.js"
pkill -f "vite"
```

## Benefits of Local Development

1. **Faster Iteration** - No AWS deployment delays
2. **Cost Savings** - No AWS resource usage during development
3. **Offline Development** - Works without internet connection
4. **Easy Debugging** - Full request/response logging
5. **Isolated Testing** - No impact on AWS resources
6. **CORS-Free** - No cross-origin issues

## Next Steps

Once you've tested your changes locally:

1. **Deploy to AWS** using the normal deployment process
2. **Test in AWS environment** to ensure compatibility
3. **Update documentation** if needed
4. **Commit changes** to version control

## Mock Data

The mock server starts with one default target account:

```json
{
  "accountId": "123456789012",
  "name": "Current Account",
  "description": "The account where this solution is deployed",
  "crossAccountRoleArn": "",
  "stagingAccountId": "",
  "isCurrentAccount": true
}
```

You can add additional accounts through the UI or API calls for testing multi-account scenarios.