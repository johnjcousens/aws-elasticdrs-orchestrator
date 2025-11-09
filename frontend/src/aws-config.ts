/**
 * AWS Amplify Configuration
 * 
 * These values should be replaced with actual CloudFormation stack outputs after deployment.
 * To get these values, run:
 * aws cloudformation describe-stacks --stack-name DRS-Orchestration --query 'Stacks[0].Outputs'
 */

export const awsConfig = {
  Auth: {
    Cognito: {
      // AWS Region where resources are deployed
      region: 'us-west-2',
      
      // Cognito User Pool ID (from CloudFormation output: UserPoolId)
      userPoolId: 'us-west-2_PLACEHOLDER',
      
      // Cognito User Pool App Client ID (from CloudFormation output: UserPoolClientId)
      userPoolClientId: 'PLACEHOLDER_CLIENT_ID',
      
      // Cognito Identity Pool ID (from CloudFormation output: IdentityPoolId)
      identityPoolId: 'us-west-2:PLACEHOLDER-IDENTITY-POOL-ID',
      
      // Sign-in options
      loginWith: {
        email: true,
      },
    }
  },
  
  API: {
    REST: {
      DRSOrchestration: {
        // API Gateway endpoint (from CloudFormation output: ApiEndpoint)
        endpoint: 'https://PLACEHOLDER_API_ID.execute-api.us-west-2.amazonaws.com/prod',
        region: 'us-west-2',
      }
    }
  }
};

// Export region for convenience
export const AWS_REGION = awsConfig.Auth.Cognito.region;

// Export API name for convenience
export const API_NAME = 'DRSOrchestration';
