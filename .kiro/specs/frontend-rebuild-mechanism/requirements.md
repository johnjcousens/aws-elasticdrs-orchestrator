# Frontend Rebuild Mechanism - Requirements

## Overview
The frontend deployment mechanism needs to be properly triggered to rebuild and deploy the React application after backend Lambda changes. Currently, the frontend is serving cached JavaScript files that reference the old monolithic API structure, causing runtime errors when viewing executions.

## Problem Statement
After decomposing the monolithic API handler into specialized handlers (execution-handler, query-handler, data-management-handler), the backend Lambda functions were successfully deployed but the frontend was not rebuilt. This causes the frontend to serve old cached JavaScript files from CloudFront that expect the old API response structure.

**Current Error**:
```
TypeError: Cannot read properties of undefined (reading 'find')
at WaveProgress.tsx:137
```

**Root Cause**: Frontend code tries to access `jobLogs.jobLogs.find()` but the backend now returns `{executionId: "...", jobLogs: [...]}` where `jobLogs` is already the array, not an object with a nested `jobLogs` property.

## User Stories

### 1. As a DevOps engineer, I need to understand how to trigger frontend rebuilds
**Acceptance Criteria**:
- Documentation exists explaining the frontend deployment mechanism
- Clear instructions on how to trigger a frontend rebuild manually
- Understanding of when frontend rebuilds happen automatically

### 2. As a developer, I need the frontend to automatically rebuild when backend APIs change
**Acceptance Criteria**:
- Frontend rebuild is triggered as part of the deployment pipeline
- CloudFront cache is invalidated after frontend rebuild
- New JavaScript files are served to users after deployment

### 3. As a user, I need the executions page to work correctly after deployment
**Acceptance Criteria**:
- Executions page loads without JavaScript errors
- Wave progress displays correctly with job logs
- All execution details are visible and functional

## Technical Requirements

### 1. Frontend Deployment Investigation
- Identify the correct CloudFormation stack name for dev environment
- Understand how frontend-deployer Lambda is triggered
- Document the frontend build and deployment process

### 2. Frontend Code Fix
- Fix `WaveProgress.tsx` line 137 to correctly access `jobLogs` array
- Ensure type definitions match backend response structure
- Verify all other frontend code expecting job logs data

### 3. Deployment Process
- Trigger frontend rebuild through proper mechanism
- Invalidate CloudFront cache to serve new files
- Verify new JavaScript files are deployed and served

## Non-Functional Requirements

### Performance
- Frontend rebuild should complete within 5 minutes
- CloudFront cache invalidation should complete within 15 minutes
- No downtime during frontend deployment

### Reliability
- Frontend deployment should be idempotent
- Failed deployments should not break existing frontend
- Rollback mechanism should be available

## Out of Scope
- Changing the backend API response structure (already correct)
- Modifying the Lambda function deployment process (already working)
- Adding new frontend features

## Success Criteria
1. Frontend rebuild mechanism is documented and understood
2. Frontend code is fixed to match backend response structure
3. Frontend is successfully rebuilt and deployed to dev
4. Executions page works without errors
5. Job logs display correctly in wave progress component
