# AWS DRS Orchestration - Enhancement Plan

## Document Overview

This document provides a comprehensive roadmap for completing and enhancing the AWS DRS Orchestration solution. It covers critical gaps, security improvements, operational excellence, and performance optimizations.

**Last Updated**: November 8, 2025  
**Current Implementation**: ~45% complete  
**Target**: Production-ready MVP

---

## Phase 1: Critical Gap Fixes (MVP Requirements)

### Priority: CRITICAL | Timeline: Week 1

These items must be completed before the solution can function as an MVP.

---

### 1.1 API Gateway Integration

**Objective**: Create explicit API Gateway REST API with Cognito authorization

**Current State**: 
- Lambda stack uses SAM implicit API (basic functionality only)
- No Cognito integration
- No custom domain support
- No throttling or request validation

**Required Changes**:

Add to `cfn/master-template.yaml`:

```yaml
  # API Gateway REST API
  RestApi:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: !Sub '${ProjectName}-api'
      Description: 'DRS Orchestration REST API'
      EndpointConfiguration:
        Types:
          - REGIONAL
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # Cognito Authorizer
  ApiAuthorizer:
    Type: AWS::ApiGateway::Authorizer
    Properties:
      Name: CognitoAuthorizer
      Type: COGNITO_USER_POOLS
      RestApiId: !Ref RestApi
      IdentitySource: method.request.header.Authorization
      ProviderARNs:
        - !GetAtt UserPool.Arn

  # API Resources - Protection Groups
  ProtectionGroupsResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref RestApi
      ParentId: !GetAtt RestApi.RootResourceId
      PathPart: protection-groups

  ProtectionGroupResource:
    Type: AWS::ApiGateway::Resource
    Properties:
      RestApiId: !Ref RestApi
      ParentId: !Ref ProtectionGroupsResource
      PathPart: '{id}'

  # Methods - GET /protection-groups
  ProtectionGroupsGetMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref RestApi
      ResourceId: !Ref ProtectionGroupsResource
      HttpMethod: GET
      AuthorizationType: COGNITO_USER_POOLS
      AuthorizerId: !Ref ApiAuthorizer
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaStack.Outputs.ApiHandlerFunctionArn}/invocations'
      MethodResponses:
        - StatusCode: 200
          ResponseParameters:
            method.response.header.Access-Control-Allow-Origin: true

  # Methods - POST /protection-groups
  ProtectionGroupsPostMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref RestApi
      ResourceId: !Ref ProtectionGroupsResource
      HttpMethod: POST
      AuthorizationType: COGNITO_USER_POOLS
      AuthorizerId: !Ref ApiAuthorizer
      RequestValidatorId: !Ref ApiRequestValidator
      Integration:
        Type: AWS_PROXY
        IntegrationHttpMethod: POST
        Uri: !Sub 'arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${LambdaStack.Outputs.ApiHandlerFunctionArn}/invocations'
      MethodResponses:
        - StatusCode: 201
          ResponseParameters:
            method.response.header.Access-Control-Allow-Origin: true

  # Request Validator
  ApiRequestValidator:
    Type: AWS::ApiGateway::RequestValidator
    Properties:
      Name: RequestValidator
      RestApiId: !Ref RestApi
      ValidateRequestBody: true
      ValidateRequestParameters: true

  # CORS - OPTIONS /protection-groups
  ProtectionGroupsOptionsMethod:
    Type: AWS::ApiGateway::Method
    Properties:
      RestApiId: !Ref RestApi
      ResourceId: !Ref ProtectionGroupsResource
      HttpMethod: OPTIONS
      AuthorizationType: NONE
      Integration:
        Type: MOCK
        IntegrationResponses:
          - StatusCode: 200
            ResponseParameters:
              method.response.header.Access-Control-Allow-Headers: "'Content-Type,Authorization'"
              method.response.header.Access-Control-Allow-Methods: "'GET,POST,PUT,DELETE,OPTIONS'"
              method.response.header.Access-Control-Allow-Origin: "'*'"
            ResponseTemplates:
              application/json: ''
        RequestTemplates:
          application/json: '{"statusCode": 200}'
      MethodResponses:
        - StatusCode: 200
          ResponseParameters:
            method.response.header.Access-Control-Allow-Headers: true
            method.response.header.Access-Control-Allow-Methods: true
            method.response.header.Access-Control-Allow-Origin: true

  # Lambda Permission for API Gateway
  ApiGatewayInvokePermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !GetAtt LambdaStack.Outputs.ApiHandlerFunctionArn
      Action: lambda:InvokeFunction
      Principal: apigateway.amazonaws.com
      SourceArn: !Sub 'arn:aws:execute-api:${AWS::Region}:${AWS::AccountId}:${RestApi}/*'

  # API Deployment
  ApiDeployment:
    Type: AWS::ApiGateway::Deployment
    DependsOn:
      - ProtectionGroupsGetMethod
      - ProtectionGroupsPostMethod
      - ProtectionGroupsOptionsMethod
    Properties:
      RestApiId: !Ref RestApi

  # API Stage
  ApiStage:
    Type: AWS::ApiGateway::Stage
    Properties:
      StageName: !Ref Environment
      RestApiId: !Ref RestApi
      DeploymentId: !Ref ApiDeployment
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true
          ThrottlingBurstLimit: 500
          ThrottlingRateLimit: 1000
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # API Gateway Account (for CloudWatch Logs)
  ApiGatewayAccount:
    Type: AWS::ApiGateway::Account
    Properties:
      CloudWatchRoleArn: !GetAtt ApiGatewayCloudWatchRole.Arn

  ApiGatewayCloudWatchRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: apigateway.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs
```

**Additional Outputs**:

```yaml
  ApiEndpoint:
    Description: 'API Gateway endpoint URL'
    Value: !Sub 'https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${ApiStage}'
    Export:
      Name: !Sub '${AWS::StackName}-ApiEndpoint'

  ApiId:
    Description: 'API Gateway ID'
    Value: !Ref RestApi
    Export:
      Name: !Sub '${AWS::StackName}-ApiId'
```

**Validation Steps**:
1. Deploy CloudFormation stack
2. Verify API Gateway created with correct resources
3. Test with curl using Cognito token
4. Verify CORS headers present
5. Check CloudWatch Logs for API requests

**Dependencies**: None

---

### 1.2 Step Functions State Machine

**Objective**: Create complete state machine for wave-based orchestration

**Current State**:
- Orchestration Lambda designed for Step Functions
- No state machine definition in CloudFormation
- STATE_MACHINE_ARN environment variable not set

**Required Changes**:

Add to `cfn/master-template.yaml`:

```yaml
  # Step Functions State Machine
  OrchestrationStateMachine:
    Type: AWS::StepFunctions::StateMachine
    Properties:
      StateMachineName: !Sub '${ProjectName}-orchestration'
      StateMachineType: STANDARD
      RoleArn: !GetAtt StepFunctionsRole.Arn
      LoggingConfiguration:
        Level: ALL
        IncludeExecutionData: true
        Destinations:
          - CloudWatchLogsLogGroup:
              LogGroupArn: !GetAtt StepFunctionsLogGroup.Arn
      TracingConfiguration:
        Enabled: true
      DefinitionString: !Sub |
        {
          "Comment": "DRS Orchestration State Machine",
          "StartAt": "BeginExecution",
          "States": {
            "BeginExecution": {
              "Type": "Task",
              "Resource": "${LambdaStack.Outputs.OrchestrationFunctionArn}",
              "Parameters": {
                "action": "BEGIN",
                "ExecutionId.$": "$$.Execution.Name",
                "PlanId.$": "$.PlanId",
                "ExecutionType.$": "$.ExecutionType",
                "InitiatedBy.$": "$.InitiatedBy",
                "TopicArn.$": "$.TopicArn",
                "DryRun.$": "$.DryRun"
              },
              "ResultPath": "$",
              "Next": "CheckMoreWaves",
              "Catch": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "ResultPath": "$.Error",
                  "Next": "ExecutionFailed"
                }
              ]
            },
            "CheckMoreWaves": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.Status",
                  "StringEquals": "COMPLETED",
                  "Next": "CompleteExecution"
                }
              ],
              "Default": "ExecuteWave"
            },
            "ExecuteWave": {
              "Type": "Task",
              "Resource": "${LambdaStack.Outputs.OrchestrationFunctionArn}",
              "Parameters": {
                "action": "EXECUTE_WAVE",
                "ExecutionId.$": "$.ExecutionId",
                "PlanId.$": "$.PlanId",
                "Plan.$": "$.Plan",
                "ExecutionType.$": "$.ExecutionType",
                "InitiatedBy.$": "$.InitiatedBy",
                "TopicArn.$": "$.TopicArn",
                "DryRun.$": "$.DryRun",
                "CurrentWaveIndex.$": "$.CurrentWaveIndex",
                "WaveResults.$": "$.WaveResults",
                "Status.$": "$.Status",
                "StartTime.$": "$.StartTime"
              },
              "ResultPath": "$",
              "Next": "CheckWaveDependencies",
              "Catch": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "ResultPath": "$.Error",
                  "Next": "ExecutionFailed"
                }
              ]
            },
            "CheckWaveDependencies": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.WaitingForDependencies",
                  "BooleanEquals": true,
                  "Next": "WaitForDependencies"
                }
              ],
              "Default": "WaitForWaveCompletion"
            },
            "WaitForDependencies": {
              "Type": "Wait",
              "Seconds": 30,
              "Next": "ExecuteWave"
            },
            "WaitForWaveCompletion": {
              "Type": "Wait",
              "Seconds": 30,
              "Next": "UpdateWaveStatus"
            },
            "UpdateWaveStatus": {
              "Type": "Task",
              "Resource": "${LambdaStack.Outputs.OrchestrationFunctionArn}",
              "Parameters": {
                "action": "UPDATE_WAVE_STATUS",
                "ExecutionId.$": "$.ExecutionId",
                "PlanId.$": "$.PlanId",
                "Plan.$": "$.Plan",
                "ExecutionType.$": "$.ExecutionType",
                "InitiatedBy.$": "$.InitiatedBy",
                "TopicArn.$": "$.TopicArn",
                "DryRun.$": "$.DryRun",
                "CurrentWaveIndex.$": "$.CurrentWaveIndex",
                "WaveResults.$": "$.WaveResults",
                "Status.$": "$.Status",
                "StartTime.$": "$.StartTime",
                "WaveInProgress.$": "$.WaveInProgress"
              },
              "ResultPath": "$",
              "Next": "CheckWaveStatus",
              "Catch": [
                {
                  "ErrorEquals": ["States.ALL"],
                  "ResultPath": "$.Error",
                  "Next": "ExecutionFailed"
                }
              ]
            },
            "CheckWaveStatus": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.Status",
                  "StringEquals": "FAILED",
                  "Next": "ExecutionFailed"
                },
                {
                  "Variable": "$.WaitingForJob",
                  "BooleanEquals": true,
                  "Next": "WaitForWaveCompletion"
                },
                {
                  "Variable": "$.WaveInProgress",
                  "BooleanEquals": true,
                  "Next": "WaitForWaveCompletion"
                }
              ],
              "Default": "CheckMoreWaves"
            },
            "CompleteExecution": {
              "Type": "Task",
              "Resource": "${LambdaStack.Outputs.OrchestrationFunctionArn}",
              "Parameters": {
                "action": "COMPLETE",
                "ExecutionId.$": "$.ExecutionId",
                "PlanId.$": "$.PlanId",
                "Plan.$": "$.Plan",
                "ExecutionType.$": "$.ExecutionType",
                "InitiatedBy.$": "$.InitiatedBy",
                "TopicArn.$": "$.TopicArn",
                "CurrentWaveIndex.$": "$.CurrentWaveIndex",
                "WaveResults.$": "$.WaveResults",
                "Status.$": "$.Status",
                "StartTime.$": "$.StartTime"
              },
              "ResultPath": "$",
              "Next": "ExecutionSucceeded"
            },
            "ExecutionSucceeded": {
              "Type": "Succeed"
            },
            "ExecutionFailed": {
              "Type": "Fail",
              "Cause": "Execution failed",
              "Error": "ExecutionError"
            }
          }
        }
      Tags:
        - Key: Project
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # Step Functions IAM Role
  StepFunctionsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub '${ProjectName}-stepfunctions-role'
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: states.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: InvokeLambda
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - lambda:InvokeFunction
                Resource:
                  - !GetAtt LambdaStack.Outputs.OrchestrationFunctionArn
        - PolicyName: CloudWatchLogs
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogDelivery
                  - logs:GetLogDelivery
                  - logs:UpdateLogDelivery
                  - logs:DeleteLogDelivery
                  - logs:ListLogDeliveries
                  - logs:PutResourcePolicy
                  - logs:DescribeResourcePolicies
                  - logs:DescribeLogGroups
                Resource: '*'
        - PolicyName: XRay
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - xray:PutTraceSegments
                  - xray:PutTelemetryRecords
                  - xray:GetSamplingRules
                  - xray:GetSamplingTargets
                Resource: '*'
      Tags:
        - Key: Project
          Value: !Ref ProjectName

  # CloudWatch Log Group for Step Functions
  StepFunctionsLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub '/aws/vendedlogs/states/${ProjectName}-orchestration'
      RetentionInDays: 30
```

**Update Lambda Stack Environment Variables**:

In `cfn/lambda-stack.yaml`, update ApiHandlerFunction:

```yaml
  ApiHandlerFunction:
    Type: AWS::Serverless::Function
    Properties:
      Environment:
        Variables:
          STATE_MACHINE_ARN: !Sub 'arn:aws:states:${AWS::Region}:${AWS::AccountId}:stateMachine:${ProjectName}-orchestration'
```

**Additional Outputs**:

```yaml
  StateMachineArn:
    Description: 'Step Functions State Machine ARN'
    Value: !Ref OrchestrationStateMachine
    Export:
      Name: !Sub '${AWS::StackName}-StateMachineArn'
```

**Validation Steps**:
1. Deploy CloudFormation stack
2. Verify state machine created
3. Test execution with sample input
4. Check CloudWatch Logs for state machine execution
5. Verify X-Ray traces captured

**Dependencies**: Lambda Stack must be deployed first

---

### 1.3 Custom Resource Implementations

**Objective**: Create Lambda functions for CloudFormation custom resources

#### 1.3.1 S3 Cleanup Custom Resource

**Purpose**: Empty S3 bucket on stack deletion to allow clean removal

**Implementation**: Create `lambda/custom-resources/s3_cleanup.py`

```python
"""
S3 Cleanup Custom Resource
Empties S3 bucket on CloudFormation stack deletion
"""

import boto3
import json
from crhelper import CfnResource

s3 = boto3.client('s3')
helper = CfnResource()


@helper.create
def create(event, context):
    """No-op for Create"""
    return None


@helper.update
def update(event, context):
    """No-op for Update"""
    return None


@helper.delete
def delete(event, context):
    """Empty S3 bucket on Delete"""
    bucket_name = event['ResourceProperties']['BucketName']
    print(f"Emptying bucket: {bucket_name}")
    
    try:
        # Delete all objects
        paginator = s3.get_paginator('list_object_versions')
        for page in paginator.paginate(Bucket=bucket_name):
            objects = []
            
            # Get regular objects
            for obj in page.get('Versions', []):
                objects.append({
                    'Key': obj['Key'],
                    'VersionId': obj['VersionId']
                })
            
            # Get delete markers
            for obj in page.get('DeleteMarkers', []):
                objects.append({
                    'Key': obj['Key'],
                    'VersionId': obj['VersionId']
                })
            
            # Delete in batches of 1000
            if objects:
                s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects}
                )
        
        print(f"Successfully emptied bucket: {bucket_name}")
    except Exception as e:
        print(f"Error emptying bucket: {str(e)}")
        # Don't fail - allow stack deletion to proceed
    
    return None


def lambda_handler(event, context):
    """Main handler for CloudFormation custom resource"""
    helper(event, context)
```

**Requirements**: Create `lambda/custom-resources/requirements.txt`

```
boto3>=1.34.0
crhelper>=2.0.0
```

#### 1.3.2 Frontend Builder Custom Resource

**Purpose**: Build and deploy React frontend on stack create/update

**Implementation**: Create `lambda/frontend-builder/build_and_deploy.py`

```python
"""
Frontend Builder Custom Resource
Builds React application and deploys to S3
"""

import boto3
import json
import os
import subprocess
import shutil
from crhelper import CfnResource

s3 = boto3.client('s3')
cloudfront = boto3.client('cloudfront')
helper = CfnResource()


@helper.create
@helper.update
def create_or_update(event, context):
    """Build and deploy frontend"""
    properties = event['ResourceProperties']
    bucket_name = properties['BucketName']
    distribution_id = properties['DistributionId']
    api_endpoint = properties.get('ApiEndpoint', '')
    user_pool_id = properties.get('UserPoolId', '')
    user_pool_client_id = properties.get('UserPoolClientId', '')
    identity_pool_id = properties.get('IdentityPoolId', '')
    region = properties.get('Region', os.environ.get('AWS_REGION', 'us-west-2'))
    
    print(f"Building and deploying frontend to bucket: {bucket_name}")
    
    try:
        # Create temporary build directory
        build_dir = '/tmp/frontend-build'
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)
        
        # Create basic index.html for now
        # In production, this would clone repo and run npm build
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS DRS Orchestration</title>
</head>
<body>
    <div id="root">
        <h1>AWS DRS Orchestration</h1>
        <p>Frontend placeholder - React app will be deployed here</p>
        <p>API Endpoint: {api_endpoint}</p>
        <p>Region: {region}</p>
    </div>
    <script>
        console.log('AWS Config:', {{
            apiEndpoint: '{api_endpoint}',
            userPoolId: '{user_pool_id}',
            userPoolClientId: '{user_pool_client_id}',
            identityPoolId: '{identity_pool_id}',
            region: '{region}'
        }});
    </script>
</body>
</html>"""
        
        with open(f'{build_dir}/index.html', 'w') as f:
            f.write(index_html)
        
        # Upload to S3
        print("Uploading to S3...")
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, build_dir)
                s3_key = relative_path.replace('\\', '/')
                
                # Determine content type
                content_type = 'text/html'
                if file.endswith('.js'):
                    content_type = 'application/javascript'
                elif file.endswith('.css'):
                    content_type = 'text/css'
                elif file.endswith('.json'):
                    content_type = 'application/json'
                
                s3.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'max-age=31536000' if file != 'index.html' else 'no-cache'
                    }
                )
        
        print("Upload complete. Invalidating CloudFront cache...")
        
        # Invalidate CloudFront cache
        cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': str(context.request_id)
            }
        )
        
        print("Frontend deployment complete")
        return bucket_name
        
    except Exception as e:
        print(f"Error deploying frontend: {str(e)}")
        raise


@helper.delete
def delete(event, context):
    """No-op for Delete - S3 cleanup handles bucket emptying"""
    return None


def lambda_handler(event, context):
    """Main handler for CloudFormation custom resource"""
    helper(event, context)
```

**Requirements**: Create `lambda/frontend-builder/requirements.txt`

```
boto3>=1.34.0
crhelper>=2.0.0
```

**Add Custom Resources to Master Template**:

```yaml
  # S3 Cleanup Custom Resource
  S3CleanupResource:
    Type: Custom::S3Cleanup
    Properties:
      ServiceToken: !GetAtt LambdaStack.Outputs.S3CleanupFunctionArn
      BucketName: !Ref FrontendBucket

  # Frontend Build Custom Resource
  FrontendBuildResource:
    Type: Custom::FrontendBuild
    DependsOn:
      - FrontendBucket
      - CloudFrontDistribution
      - RestApi
    Properties:
      ServiceToken: !GetAtt LambdaStack.Outputs.FrontendBuilderFunctionArn
      BucketName: !Ref FrontendBucket
      DistributionId: !Ref CloudFrontDistribution
      ApiEndpoint: !Sub 'https://${RestApi}.execute-api.${AWS::Region}.amazonaws.com/${ApiStage}'
      UserPoolId: !Ref UserPool
      UserPoolClientId: !Ref UserPoolClient
      IdentityPoolId: !Ref IdentityPool
      Region: !Ref AWS::Region
```

**Validation Steps**:
1. Deploy stack and verify custom resources execute
2. Check S3 bucket has index.html
3. Access CloudFront URL
4. Delete stack and verify bucket empties successfully

**Dependencies**: S3 bucket, CloudFront distribution must exist

---

### 1.4 Lambda Deployment Fix

**Objective**: Fix Lambda CodeUri configuration for proper deployment

**Current State**:
- CodeUri points to relative paths that don't exist during deployment
- No S3 bucket strategy for Lambda code
- SAM needs either inline code or S3 location

**Solution Options**:

**Option A: Use SAM CLI (Recommended)**

Update `cfn/lambda-stack.yaml` to package code automatically:

```yaml
  ApiHandlerFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${ProjectName}-api-handler'
      CodeUri: ../lambda/api-handler/
      Handler: index.lambda_handler
      # SAM CLI will package this automatically
```

Deploy with SAM CLI:
```bash
sam build -t cfn/lambda-stack.yaml
sam package --s3-bucket <deployment-bucket> --output-template-file packaged.yaml
sam deploy --template-file packaged.yaml --stack-name drs-lambda
```

**Option B: Manual S3 Upload**

1. Create deployment script `scripts/package-lambdas.sh`:

```bash
#!/bin/bash
set -e

DEPLOYMENT_BUCKET=$1
if [ -z "$DEPLOYMENT_BUCKET" ]; then
    echo "Usage: $0 <deployment-bucket>"
    exit 1
fi

echo "Packaging Lambda functions..."

# Package API Handler
cd lambda/api-handler
pip install -r requirements.txt -t .
zip -r ../../api-handler.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package Orchestration
cd lambda/orchestration
pip install -r requirements.txt -t .
zip -r ../../orchestration.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package Custom Resources
cd lambda/custom-resources
pip install -r requirements.txt -t .
zip -r ../../s3-cleanup.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package Frontend Builder
cd lambda/frontend-builder
pip install -r requirements.txt -t .
zip -r ../../frontend-builder.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

echo "Uploading to S3..."
aws s3 cp api-handler.zip s3://${DEPLOYMENT_BUCKET}/lambda/
aws s3 cp orchestration.zip s3://${DEPLOYMENT_BUCKET}/lambda/
aws s3 cp s3-cleanup.zip s3://${DEPLOYMENT_BUCKET}/lambda/
aws s3 cp frontend-builder.zip s3://${DEPLOYMENT_BUCKET}/lambda/

echo "Cleaning up..."
rm -f *.zip

echo "Lambda packaging complete!"
```

2. Update `cfn/lambda-stack.yaml`:

```yaml
  ApiHandlerFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${ProjectName}-api-handler'
      CodeUri:
        Bucket: !Ref DeploymentBucket
        Key: lambda/api-handler.zip
      Handler: index.lambda_handler
```

3. Add DeploymentBucket parameter to master template.

**Recommended Approach**: Use Option A with SAM CLI for simplicity

**Validation Steps**:
1. Package Lambda functions
2. Deploy CloudFormation stack
3. Verify Lambda functions exist with code
4. Test function invocation
5. Check CloudWatch Logs

**Dependencies**: None

---

### 1.5 SSM Documents

**Objective**: Create SSM automation documents for post-recovery actions

**Current State**:
- Example SSM document exists in `ssm-documents/`
- Not defined in CloudFormation
- Not automatically deployed

**Required Changes**:

Add to `cfn/master-template.yaml`:

```yaml
  # SSM Document - Health Check
  HealthCheckDocument:
    Type: AWS::SSM::Document
    Properties:
      Name: !Sub '${ProjectName}-health-check'
      DocumentType: Command
      Content:
        schemaVersion: '2.2'
        description: 'Post-recovery health check for Windows and Linux instances'
        parameters:
          workingDirectory:
            type: String
            description: 'Working directory'
            default: '/tmp'
        mainSteps:
          - action: aws:runShellScript
            name: linuxHealthCheck
            precondition:
              StringEquals:
                - platformType
                - Linux
            inputs:
              runCommand:
                - |
                  #!/bin/bash
                  echo "=== Linux Health Check ==="
                  echo "Hostname: $(hostname)"
                  echo "Uptime: $(uptime)"
                  echo "Disk Usage:"
                  df -h
                  echo "Memory Usage:"
                  free -m
                  echo "CPU Info:"
                  top -bn1 | head -5
                  echo "Network Connectivity:"
                  ping -c 3 8.8.8.8
                  echo "Health check completed"
          - action: aws:runPowerShellScript
            name: windowsHealthCheck
            precondition:
              StringEquals:
                - platformType
                - Windows
            inputs:
              runCommand:
                - |
                  Write-Host "=== Windows Health Check ==="
                  Write-Host "Hostname: $env:COMPUTERNAME"
                  Write-Host "Uptime:"
                  Get-CimInstance Win32_OperatingSystem | Select-Object LastBootUpTime
                  Write-Host "Disk Usage:"
                  Get-PSDrive -PSProvider FileSystem
                  Write-Host "Memory Usage:"
                  Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize
                  Write-Host "Network Connectivity:"
                  Test-Connection -ComputerName 8.8.8.8 -Count 3
                  Write-Host "Health check completed"
      Tags:
        - Key: Project
          Value: !Ref ProjectName

  # SSM Document - Application Startup
  ApplicationStartupDocument:
    Type: AWS::SSM::Document
    Properties:
      Name: !Sub '${ProjectName}-app-startup'
      DocumentType: Command
      Content:
        schemaVersion: '2.2'
        description: 'Start application services after recovery'
        parameters:
          serviceName:
            type: String
            description: 'Service name to start'
            default: 'app'
        mainSteps:
          - action: aws:runShellScript
            name: linuxStartService
            precondition:
              StringEquals:
                - platformType
                - Linux
            inputs:
              runCommand:
                - |
                  #!/bin/bash
                  SERVICE_NAME="{{ serviceName }}"
                  echo "Starting service: $SERVICE_NAME"
                  systemctl start $SERVICE_NAME
                  systemctl status $SERVICE_NAME
          - action: aws:runPowerShellScript
            name: windowsStartService
            precondition:
              StringEquals:
                - platformType
                - Windows
            inputs:
              runCommand:
                - |
                  $ServiceName = "{{ serviceName }}"
                  Write-Host "Starting service: $ServiceName"
                  Start-Service -Name $ServiceName
                  Get-Service -Name $ServiceName
      Tags:
        - Key: Project
          Value: !Ref ProjectName

  # SSM Document - Network Validation
  NetworkValidationDocument:
    Type: AWS::SSM::Document
    Properties:
      Name: !Sub '${ProjectName}-network-validation'
      DocumentType: Command
      Content:
        schemaVersion: '2.2'
        description: 'Validate network connectivity after recovery'
        parameters:
          targetHost:
            type: String
            description: 'Target host to test connectivity'
            default: '8.8.8.8'
        mainSteps:
          - action: aws:runShellScript
            name: linuxNetworkTest
            precondition:
              StringEquals:
                - platformType
                - Linux
            inputs:
              runCommand:
                - |
                  #!/bin/bash
                  TARGET="{{ targetHost }}"
                  echo "Testing connectivity to: $TARGET"
                  ping -c 5 $TARGET
                  echo "DNS Resolution:"
                  nslookup google.com
                  echo "Route Table:"
                  route -n
          - action: aws:runPowerShellScript
            name: windowsNetworkTest
            precondition:
              StringEquals:
                - platformType
                - Windows
            inputs:
              runCommand:
                - |
                  $Target = "{{ targetHost }}"
                  Write-Host "Testing connectivity to: $Target"
                  Test-Connection -ComputerName $Target -Count 5
                  Write-Host "DNS Resolution:"
                  Resolve-DnsName google.com
                  Write-Host "Route Table:"
                  route print
      Tags:
        - Key: Project
          Value: !Ref ProjectName
```

**Validation Steps**:
1. Deploy CloudFormation stack
2. Verify SSM documents created
3. Test execution on sample instance
4. Check SSM Run Command output
5. Verify cross-platform compatibility

**Dependencies**: None

---

## Phase 2: Security Hardening

### Priority: HIGH | Timeline: Week 2

*[Detailed sections for security improvements to be added based on review findings]*

---

## Phase 3: Operational Excellence

### Priority: MEDIUM | Timeline: Week 3

*[Detailed sections for monitoring, alerting, observability to be added]*

---

## Phase 4: Performance Optimization

### Priority: MEDIUM | Timeline: Week 4

*[Detailed sections for performance improvements to be added]*

---

## Implementation Tracking

| Phase | Component | Status | Priority | ETA |
|-------|-----------|--------|----------|-----|
| 1 | API Gateway Integration | Pending | Critical | Week 1 |
| 1 | Step Functions State Machine | Pending | Critical | Week 1 |
| 1 | Custom Resources | Pending | Critical | Week 1 |
| 1 | Lambda Deployment Fix | Pending | Critical | Week 1 |
| 1 | SSM Documents | Pending | Critical | Week 1 |
| 2 | Security Hardening | Pending | High | Week 2 |
| 3 | Operational Excellence | Pending | Medium | Week 3 |
| 4 | Performance Optimization | Pending | Medium | Week 4 |

---

## Next Steps

1. ✅ Review completed - gaps identified
2. 📝 Enhancement plan created (this document)
3. ⏭️ Begin Phase 1 implementation
4. ⏭️ Create missing custom resource Lambda functions
5. ⏭️ Update CloudFormation templates with new resources
6. ⏭️ Test and validate each component

**Ready for implementation!**
