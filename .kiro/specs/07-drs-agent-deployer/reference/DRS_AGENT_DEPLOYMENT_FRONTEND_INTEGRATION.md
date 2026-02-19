# DRS Agent Deployment - Frontend Integration Guide

## Overview

This guide provides a complete plan for integrating DRS agent deployment functionality into the React frontend, allowing users to deploy agents through the UI.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  DRS Management Page                                    │ │
│  │  - View source servers                                  │ │
│  │  - Deploy agents button                                 │ │
│  │  - Deployment status                                    │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │  DRSAgentDeployDialog Component                        │ │
│  │  - Account selection                                    │ │
│  │  - Region selection                                     │ │
│  │  - Deploy button                                        │ │
│  │  - Progress indicator                                   │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │  API Service (api.ts)                                   │ │
│  │  - deployDRSAgents()                                    │ │
│  │  - getDRSAgentDeploymentStatus()                       │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
└─────────────────────┼────────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                               │
│  POST /drs/agents/deploy                                    │
│  GET  /drs/agents/deploy/{deployment_id}                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              DRS Agent Deployer Lambda                       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Add API Endpoints (Backend)

#### 1.1 Add API Gateway Resources

**File**: `cfn/api-gateway-resources-stack.yaml`

Add after existing DRS resources:

```yaml
# DRS Agent Deployment Resources
DRSAgentsResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApiId
    ParentId: !Ref DRSResource
    PathPart: agents

DRSAgentsDeployResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApiId
    ParentId: !Ref DRSAgentsResource
    PathPart: deploy

DRSAgentsDeployStatusResource:
  Type: AWS::ApiGateway::Resource
  Properties:
    RestApiId: !Ref RestApiId
    ParentId: !Ref DRSAgentsDeployResource
    PathPart: '{deployment_id}'
```

Add to Outputs:

```yaml
DRSAgentsDeployResourceId:
  Description: DRS agents deploy resource ID
  Value: !Ref DRSAgentsDeployResource
  Export:
    Name: !Sub '${AWS::StackName}-DRSAgentsDeployResourceId'

DRSAgentsDeployStatusResourceId:
  Description: DRS agents deploy status resource ID
  Value: !Ref DRSAgentsDeployStatusResource
  Export:
    Name: !Sub '${AWS::StackName}-DRSAgentsDeployStatusResourceId'
```

#### 1.2 Add API Gateway Methods

**File**: `cfn/api-gateway-infrastructure-methods-stack.yaml`

Add new parameter:

```yaml
Parameters:
  # ... existing parameters ...
  
  DRSAgentDeployerFunctionArn:
    Type: String
    Description: DRS Agent Deployer Lambda Function ARN
  
  DrsAgentsDeployResourceId:
    Type: String
    Description: DRS agents deploy resource ID
  
  DrsAgentsDeployStatusResourceId:
    Type: String
    Description: DRS agents deploy status resource ID
```

Add methods:

```yaml
# POST /drs/agents/deploy
DRSAgentsDeployMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApiId
    ResourceId: !Ref DrsAgentsDeployResourceId
    HttpMethod: POST
    AuthorizationType: COGNITO_USER_POOLS
    AuthorizerId: !Ref ApiAuthorizerId
    RequestValidatorId: !Ref ApiRequestValidatorId
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${DRSAgentDeployerFunctionArn}/invocations'
    MethodResponses:
      - StatusCode: 200
        ResponseModels:
          application/json: Empty
      - StatusCode: 400
        ResponseModels:
          application/json: Empty
      - StatusCode: 500
        ResponseModels:
          application/json: Empty

# Lambda permission for POST /drs/agents/deploy
DRSAgentsDeployMethodPermission:
  Type: AWS::Lambda::Permission
  Properties:
    FunctionName: !Ref DRSAgentDeployerFunctionArn
    Action: lambda:InvokeFunction
    Principal: apigateway.amazonaws.com
    SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApiId}/*/*/*'

# GET /drs/agents/deploy/{deployment_id}
DRSAgentsDeployStatusMethod:
  Type: AWS::ApiGateway::Method
  Properties:
    RestApiId: !Ref RestApiId
    ResourceId: !Ref DrsAgentsDeployStatusResourceId
    HttpMethod: GET
    AuthorizationType: COGNITO_USER_POOLS
    AuthorizerId: !Ref ApiAuthorizerId
    Integration:
      Type: AWS_PROXY
      IntegrationHttpMethod: POST
      Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${QueryHandlerArn}/invocations'
      RequestTemplates:
        application/json: |
          {
            "operation": "get_drs_agent_deployment_status",
            "deployment_id": "$input.params('deployment_id')"
          }
    MethodResponses:
      - StatusCode: 200
        ResponseModels:
          application/json: Empty
```

#### 1.3 Update Master Template

**File**: `cfn/master-template.yaml`

Update LambdaStack parameters to pass DRS Agent Deployer ARN to API Gateway stack:

```yaml
ApiGatewayInfrastructureMethodsStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    Parameters:
      # ... existing parameters ...
      DRSAgentDeployerFunctionArn: !GetAtt LambdaStack.Outputs.DRSAgentDeployerFunctionArn
      DrsAgentsDeployResourceId: !GetAtt ApiGatewayResourcesStack.Outputs.DRSAgentsDeployResourceId
      DrsAgentsDeployStatusResourceId: !GetAtt ApiGatewayResourcesStack.Outputs.DRSAgentsDeployStatusResourceId
```

### Step 2: Add Frontend Types

**File**: `frontend/src/types/index.ts`

Add to exports:

```typescript
export * from './drs-agent-deployment';
```

### Step 3: Add API Service Methods

**File**: `frontend/src/services/api.ts`

Add import:

```typescript
import type {
  DRSAgentDeploymentRequest,
  DRSAgentDeploymentResult,
  DRSAgentDeploymentStatus,
} from '../types/drs-agent-deployment';
```

Add methods to ApiClient class:

```typescript
/**
 * Deploy DRS agents to target account
 */
async deployDRSAgents(
  request: DRSAgentDeploymentRequest
): Promise<DRSAgentDeploymentResult> {
  const response = await this.axiosInstance.post<DRSAgentDeploymentResult>(
    '/drs/agents/deploy',
    request
  );
  return response.data;
}

/**
 * Get DRS agent deployment status
 */
async getDRSAgentDeploymentStatus(
  deploymentId: string
): Promise<DRSAgentDeploymentStatus> {
  const response = await this.axiosInstance.get<DRSAgentDeploymentStatus>(
    `/drs/agents/deploy/${deploymentId}`
  );
  return response.data;
}
```

### Step 4: Create React Components

#### 4.1 DRS Agent Deploy Dialog Component

**File**: `frontend/src/components/DRSAgentDeployDialog.tsx`

```typescript
import React, { useState } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  FormField,
  Select,
  Button,
  Alert,
  ProgressBar,
  StatusIndicator,
  Container,
  Header,
  ColumnLayout,
  KeyValuePairs,
} from '@cloudscape-design/components';
import { useNotifications } from '../contexts/NotificationContext';
import apiClient from '../services/api';
import type {
  DRSAgentDeploymentRequest,
  DRSAgentDeploymentResult,
} from '../types/drs-agent-deployment';

interface DRSAgentDeployDialogProps {
  visible: boolean;
  onDismiss: () => void;
  onSuccess?: (result: DRSAgentDeploymentResult) => void;
  defaultAccountId?: string;
  defaultSourceRegion?: string;
  defaultTargetRegion?: string;
}

export const DRSAgentDeployDialog: React.FC<DRSAgentDeployDialogProps> = ({
  visible,
  onDismiss,
  onSuccess,
  defaultAccountId = '',
  defaultSourceRegion = 'us-east-1',
  defaultTargetRegion = 'us-west-2',
}) => {
  const { addNotification } = useNotifications();
  
  // Form state
  const [accountId, setAccountId] = useState(defaultAccountId);
  const [sourceRegion, setSourceRegion] = useState(defaultSourceRegion);
  const [targetRegion, setTargetRegion] = useState(defaultTargetRegion);
  
  // Deployment state
  const [deploying, setDeploying] = useState(false);
  const [deploymentResult, setDeploymentResult] = useState<DRSAgentDeploymentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Region options
  const regionOptions = [
    { label: 'US East (N. Virginia)', value: 'us-east-1' },
    { label: 'US East (Ohio)', value: 'us-east-2' },
    { label: 'US West (N. California)', value: 'us-west-1' },
    { label: 'US West (Oregon)', value: 'us-west-2' },
    { label: 'EU (Ireland)', value: 'eu-west-1' },
    { label: 'EU (Frankfurt)', value: 'eu-central-1' },
    { label: 'Asia Pacific (Tokyo)', value: 'ap-northeast-1' },
    { label: 'Asia Pacific (Singapore)', value: 'ap-southeast-1' },
  ];
  
  const handleDeploy = async () => {
    if (!accountId) {
      setError('Account ID is required');
      return;
    }
    
    setDeploying(true);
    setError(null);
    setDeploymentResult(null);
    
    try {
      const request: DRSAgentDeploymentRequest = {
        account_id: accountId,
        source_region: sourceRegion,
        target_region: targetRegion,
        wait_for_completion: true,
        timeout_seconds: 600,
      };
      
      const result = await apiClient.deployDRSAgents(request);
      
      setDeploymentResult(result);
      
      if (result.status === 'success') {
        addNotification({
          type: 'success',
          content: `Successfully deployed DRS agents to ${result.instances_deployed} instances`,
          dismissible: true,
        });
        
        if (onSuccess) {
          onSuccess(result);
        }
      } else {
        addNotification({
          type: 'error',
          content: result.message || 'Deployment failed',
          dismissible: true,
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || err.message || 'Failed to deploy agents';
      setError(errorMessage);
      addNotification({
        type: 'error',
        content: errorMessage,
        dismissible: true,
      });
    } finally {
      setDeploying(false);
    }
  };
  
  const handleClose = () => {
    if (!deploying) {
      setAccountId(defaultAccountId);
      setSourceRegion(defaultSourceRegion);
      setTargetRegion(defaultTargetRegion);
      setDeploymentResult(null);
      setError(null);
      onDismiss();
    }
  };
  
  return (
    <Modal
      visible={visible}
      onDismiss={handleClose}
      header="Deploy DRS Agents"
      size="large"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleClose} disabled={deploying}>
              {deploymentResult ? 'Close' : 'Cancel'}
            </Button>
            {!deploymentResult && (
              <Button
                variant="primary"
                onClick={handleDeploy}
                loading={deploying}
                disabled={!accountId || deploying}
              >
                Deploy Agents
              </Button>
            )}
          </SpaceBetween>
        </Box>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Alert type="error" dismissible onDismiss={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {!deploymentResult ? (
          <>
            <Alert type="info">
              This will deploy DRS agents to all EC2 instances tagged with:
              <ul>
                <li><code>dr:enabled=true</code></li>
                <li><code>dr:recovery-strategy=drs</code></li>
              </ul>
              Instances must have SSM agent online and proper IAM permissions.
            </Alert>
            
            <FormField
              label="AWS Account ID"
              description="Target account where instances are located"
              errorText={!accountId ? 'Account ID is required' : undefined}
            >
              <Input
                value={accountId}
                onChange={({ detail }) => setAccountId(detail.value)}
                placeholder="123456789012"
                disabled={deploying}
              />
            </FormField>
            
            <FormField
              label="Source Region"
              description="Region where EC2 instances are located"
            >
              <Select
                selectedOption={regionOptions.find(r => r.value === sourceRegion) || null}
                onChange={({ detail }) => setSourceRegion(detail.selectedOption.value!)}
                options={regionOptions}
                disabled={deploying}
              />
            </FormField>
            
            <FormField
              label="Target Region"
              description="Region to replicate data to"
            >
              <Select
                selectedOption={regionOptions.find(r => r.value === targetRegion) || null}
                onChange={({ detail }) => setTargetRegion(detail.selectedOption.value!)}
                options={regionOptions}
                disabled={deploying}
              />
            </FormField>
            
            {deploying && (
              <Container>
                <SpaceBetween size="m">
                  <Box textAlign="center">
                    <StatusIndicator type="in-progress">
                      Deploying DRS agents...
                    </StatusIndicator>
                  </Box>
                  <ProgressBar
                    value={50}
                    variant="key-value"
                    label="Deployment progress"
                    description="Installing agents via SSM"
                  />
                  <Box variant="small" color="text-body-secondary" textAlign="center">
                    This may take 5-10 minutes. Please wait...
                  </Box>
                </SpaceBetween>
              </Container>
            )}
          </>
        ) : (
          <Container
            header={
              <Header
                variant="h2"
                description={`Deployment ${deploymentResult.status}`}
              >
                Deployment Results
              </Header>
            }
          >
            <SpaceBetween size="l">
              <Alert
                type={deploymentResult.status === 'success' ? 'success' : 'error'}
              >
                {deploymentResult.status === 'success'
                  ? `Successfully deployed agents to ${deploymentResult.instances_deployed} instances`
                  : deploymentResult.message || 'Deployment failed'}
              </Alert>
              
              <ColumnLayout columns={3} variant="text-grid">
                <KeyValuePairs
                  columns={1}
                  items={[
                    {
                      label: 'Instances Discovered',
                      value: deploymentResult.instances_discovered || 0,
                    },
                    {
                      label: 'Instances Online',
                      value: deploymentResult.instances_online || 0,
                    },
                    {
                      label: 'Instances Deployed',
                      value: deploymentResult.instances_deployed || 0,
                    },
                  ]}
                />
              </ColumnLayout>
              
              {deploymentResult.source_servers && deploymentResult.source_servers.length > 0 && (
                <Container header={<Header variant="h3">DRS Source Servers</Header>}>
                  <SpaceBetween size="s">
                    {deploymentResult.source_servers.map((server) => (
                      <Box key={server.source_server_id}>
                        <SpaceBetween direction="horizontal" size="xs">
                          <Box variant="awsui-key-label">{server.hostname}</Box>
                          <StatusIndicator
                            type={
                              server.replication_state === 'INITIAL_SYNC'
                                ? 'in-progress'
                                : server.replication_state === 'CONTINUOUS_REPLICATION'
                                ? 'success'
                                : 'pending'
                            }
                          >
                            {server.replication_state}
                          </StatusIndicator>
                        </SpaceBetween>
                      </Box>
                    ))}
                  </SpaceBetween>
                </Container>
              )}
              
              <Alert type="info">
                <SpaceBetween size="xs">
                  <Box variant="strong">Next Steps:</Box>
                  <ol>
                    <li>Monitor DRS console for replication progress</li>
                    <li>Wait for INITIAL_SYNC to complete</li>
                    <li>Configure launch settings for each source server</li>
                    <li>Test recovery when ready</li>
                  </ol>
                </SpaceBetween>
              </Alert>
            </SpaceBetween>
          </Container>
        )}
      </SpaceBetween>
    </Modal>
  );
};
```

#### 4.2 DRS Agent Status Component

**File**: `frontend/src/components/DRSAgentStatus.tsx`

```typescript
import React from 'react';
import {
  Container,
  Header,
  StatusIndicator,
  Box,
  SpaceBetween,
  Button,
} from '@cloudscape-design/components';
import type { DRSAgentDeploymentResult } from '../types/drs-agent-deployment';

interface DRSAgentStatusProps {
  accountId: string;
  region: string;
  lastDeployment?: DRSAgentDeploymentResult;
  onDeploy: () => void;
}

export const DRSAgentStatus: React.FC<DRSAgentStatusProps> = ({
  accountId,
  region,
  lastDeployment,
  onDeploy,
}) => {
  return (
    <Container
      header={
        <Header
          variant="h2"
          description="DRS agent deployment status"
          actions={
            <Button onClick={onDeploy} iconName="upload">
              Deploy Agents
            </Button>
          }
        >
          DRS Agents
        </Header>
      }
    >
      <SpaceBetween size="m">
        {lastDeployment ? (
          <>
            <Box>
              <SpaceBetween direction="horizontal" size="xs">
                <Box variant="awsui-key-label">Last Deployment:</Box>
                <StatusIndicator
                  type={lastDeployment.status === 'success' ? 'success' : 'error'}
                >
                  {lastDeployment.status}
                </StatusIndicator>
              </SpaceBetween>
            </Box>
            
            <Box>
              <SpaceBetween direction="horizontal" size="xs">
                <Box variant="awsui-key-label">Instances Deployed:</Box>
                <Box>{lastDeployment.instances_deployed || 0}</Box>
              </SpaceBetween>
            </Box>
            
            <Box>
              <SpaceBetween direction="horizontal" size="xs">
                <Box variant="awsui-key-label">Source Servers:</Box>
                <Box>{lastDeployment.source_servers?.length || 0}</Box>
              </SpaceBetween>
            </Box>
            
            {lastDeployment.timestamp && (
              <Box variant="small" color="text-body-secondary">
                Deployed: {new Date(lastDeployment.timestamp).toLocaleString()}
              </Box>
            )}
          </>
        ) : (
          <Box textAlign="center" color="text-body-secondary">
            No agents deployed yet. Click "Deploy Agents" to get started.
          </Box>
        )}
      </SpaceBetween>
    </Container>
  );
};
```

### Step 5: Integrate into Existing Pages

#### 5.1 Add to Protection Groups Page

**File**: `frontend/src/pages/ProtectionGroupsPage.tsx`

Add imports:

```typescript
import { DRSAgentDeployDialog } from '../components/DRSAgentDeployDialog';
import { DRSAgentStatus } from '../components/DRSAgentStatus';
```

Add state:

```typescript
const [showAgentDeployDialog, setShowAgentDeployDialog] = useState(false);
const [lastAgentDeployment, setLastAgentDeployment] = useState<DRSAgentDeploymentResult | null>(null);
```

Add to page content:

```typescript
<SpaceBetween size="l">
  {/* Existing content */}
  
  <DRSAgentStatus
    accountId={currentAccount?.accountId || ''}
    region={selectedRegion}
    lastDeployment={lastAgentDeployment}
    onDeploy={() => setShowAgentDeployDialog(true)}
  />
  
  {/* Existing protection groups table */}
</SpaceBetween>

<DRSAgentDeployDialog
  visible={showAgentDeployDialog}
  onDismiss={() => setShowAgentDeployDialog(false)}
  onSuccess={(result) => {
    setLastAgentDeployment(result);
    setShowAgentDeployDialog(false);
  }}
  defaultAccountId={currentAccount?.accountId}
  defaultSourceRegion={selectedRegion}
/>
```

#### 5.2 Add to Dashboard

**File**: `frontend/src/pages/Dashboard.tsx`

Add a new card for DRS agent deployment status in the dashboard grid.

### Step 6: Add Permissions

**File**: `frontend/src/types/permissions.ts`

Add new permission:

```typescript
export const PERMISSIONS = {
  // ... existing permissions ...
  DRS_AGENT_DEPLOY: 'drs:agent:deploy',
  DRS_AGENT_VIEW: 'drs:agent:view',
} as const;
```

### Step 7: Update Documentation

Update API documentation to include new endpoints:

**File**: `docs/reference/API_ENDPOINTS_CURRENT.md`

Add section:

```markdown
## DRS Agent Deployment

### Deploy DRS Agents
**POST** `/drs/agents/deploy`

Deploy DRS agents to EC2 instances in target account.

**Request Body:**
```json
{
  "account_id": "160885257264",
  "source_region": "us-east-1",
  "target_region": "us-west-2",
  "wait_for_completion": true
}
```

**Response:**
```json
{
  "status": "success",
  "instances_deployed": 6,
  "source_servers": [...]
}
```

### Get Deployment Status
**GET** `/drs/agents/deploy/{deployment_id}`

Get status of a DRS agent deployment.
```

## Testing Plan

### Unit Tests

1. **API Service Tests**
   - Test `deployDRSAgents()` method
   - Test `getDRSAgentDeploymentStatus()` method
   - Test error handling

2. **Component Tests**
   - Test `DRSAgentDeployDialog` rendering
   - Test form validation
   - Test deployment flow
   - Test `DRSAgentStatus` component

### Integration Tests

1. **End-to-End Flow**
   - Open deploy dialog
   - Fill in account details
   - Submit deployment
   - Verify success notification
   - Check deployment status

2. **Error Scenarios**
   - Invalid account ID
   - Network errors
   - Deployment failures
   - Permission denied

### Manual Testing Checklist

- [ ] Deploy dialog opens correctly
- [ ] Form validation works
- [ ] Deployment initiates successfully
- [ ] Progress indicator shows during deployment
- [ ] Results display correctly
- [ ] Success notification appears
- [ ] Error handling works
- [ ] Dialog closes properly
- [ ] Status component updates
- [ ] Permissions are enforced

## Deployment Steps

1. **Backend First**:
   ```bash
   # Deploy API Gateway changes
   ./scripts/deploy.sh dev --quick
   ```

2. **Test API**:
   ```bash
   # Test endpoint directly
   curl -X POST https://api.example.com/drs/agents/deploy \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"account_id":"160885257264","source_region":"us-east-1","target_region":"us-west-2"}'
   ```

3. **Frontend**:
   ```bash
   # Deploy frontend changes
   ./scripts/deploy.sh dev --frontend-only
   ```

4. **Verify**:
   - Open UI
   - Navigate to Protection Groups page
   - Click "Deploy Agents"
   - Complete deployment
   - Verify results

## Security Considerations

1. **Authentication**: All endpoints require Cognito authentication
2. **Authorization**: Check user permissions before showing deploy button
3. **Input Validation**: Validate account ID format (12 digits)
4. **Rate Limiting**: Consider adding rate limits for deployment endpoint
5. **Audit Logging**: Log all deployment attempts with user info

## Performance Considerations

1. **Async Deployment**: Consider async deployment for large accounts
2. **Progress Updates**: Use WebSocket or polling for real-time updates
3. **Caching**: Cache deployment status for 30 seconds
4. **Timeout Handling**: Handle long-running deployments gracefully

## Future Enhancements

1. **Bulk Deployment**: Deploy to multiple accounts simultaneously
2. **Scheduled Deployment**: Schedule agent deployments
3. **Deployment History**: Show history of all deployments
4. **Rollback**: Ability to rollback agent deployments
5. **Notifications**: Email/SNS notifications for deployment completion
6. **Deployment Templates**: Save deployment configurations as templates

## Related Documentation

- [DRS Agent Deployment Guide](DRS_AGENT_DEPLOYMENT_GUIDE.md)
- [API Development Quick Reference](API_DEVELOPMENT_QUICK_REFERENCE.md)
- [UX Component Library](../requirements/UX_COMPONENT_LIBRARY.md)
