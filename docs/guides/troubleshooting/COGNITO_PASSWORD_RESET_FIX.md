# Cognito Password Reset Fix

## Issue Description

Users are unable to reset their passwords in the AWS DRS Orchestration application. The password reset functionality shows "Additional authentication steps required" but doesn't work properly.

## Root Cause Analysis

The Cognito User Pool is configured correctly with email-based account recovery, but there are several potential issues that can prevent password reset from working:

### 1. User Pool Configuration Issues

From the CloudFormation template (`cfn/api-stack-rbac.yaml`), the User Pool is configured with:

```yaml
UserPool:
  Properties:
    AutoVerifiedAttributes:
      - email
    UsernameAttributes:
      - email
    AccountRecoverySetting:
      RecoveryMechanisms:
        - Name: verified_email
          Priority: 1
```

This configuration is correct, but there are common issues that can prevent password reset:

### 2. Common Password Reset Issues

#### Issue A: User Email Not Verified
- **Symptom**: Password reset fails with "Additional authentication steps required"
- **Cause**: The user's email address is not verified in Cognito
- **Solution**: Admin must verify the user's email or user must complete email verification

#### Issue B: Missing SES Configuration
- **Symptom**: Password reset emails are not sent
- **Cause**: Cognito is using the default email service which has limitations
- **Solution**: Configure Amazon SES for email delivery

#### Issue C: User Pool Client Configuration
- **Symptom**: Password reset flow doesn't complete properly
- **Cause**: User Pool Client missing required auth flows
- **Solution**: Ensure proper auth flows are enabled

## Solutions

### Solution 1: Verify User Email Status (Immediate Fix)

**For AWS Console Access:**

1. **Check User Status**:
   ```bash
   # Refresh AWS credentials first
   export AWS_PROFILE=777788889999_AdministratorAccess
   
   # List users in the test environment User Pool
   aws cognito-idp list-users \
     --user-pool-id us-east-1_11Ciomg6j \
     --query 'Users[*].{Username:Username,Email:Attributes[?Name==`email`].Value|[0],EmailVerified:Attributes[?Name==`email_verified`].Value|[0],UserStatus:UserStatus}' \
     --output table
   ```

2. **Manually Verify User Email** (if needed):
   ```bash
   # Replace USERNAME with the actual username
   aws cognito-idp admin-update-user-attributes \
     --user-pool-id us-east-1_11Ciomg6j \
     --username USERNAME \
     --user-attributes Name=email_verified,Value=true
   ```

3. **Reset User Password** (admin override):
   ```bash
   # Set temporary password and force password change on next login
   aws cognito-idp admin-set-user-password \
     --user-pool-id us-east-1_11Ciomg6j \
     --username USERNAME \
     --password TempPassword123! \
     --temporary
   ```

### Solution 2: Configure Amazon SES (Recommended for Production)

**Current Issue**: Cognito uses default email service with limitations (200 emails/day)

**Solution**: Configure Amazon SES for reliable email delivery

1. **Verify SES Domain/Email**:
   ```bash
   # Verify the domain or email address in SES
   aws ses verify-email-identity --email-address admin@yourdomain.com
   ```

2. **Update Cognito User Pool** to use SES:
   ```bash
   # This requires CloudFormation template update
   # Add EmailConfiguration to UserPool resource
   ```

**CloudFormation Template Update** (add to `cfn/api-stack-rbac.yaml`):

```yaml
UserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    # ... existing properties ...
    EmailConfiguration:
      EmailSendingAccount: DEVELOPER
      SourceArn: !Sub 'arn:aws:ses:${AWS::Region}:${AWS::AccountId}:identity/admin@yourdomain.com'
      ReplyToEmailAddress: 'noreply@yourdomain.com'
```

### Solution 3: User Pool Client Configuration Fix

**Check Current Configuration**:
```bash
aws cognito-idp describe-user-pool-client \
  --user-pool-id us-east-1_11Ciomg6j \
  --client-id CLIENT_ID \
  --query 'UserPoolClient.{ExplicitAuthFlows:ExplicitAuthFlows,PreventUserExistenceErrors:PreventUserExistenceErrors}'
```

**Required Auth Flows** (already configured correctly):
- `ALLOW_USER_PASSWORD_AUTH`
- `ALLOW_REFRESH_TOKEN_AUTH`
- `ALLOW_USER_SRP_AUTH`
- `ALLOW_ADMIN_USER_PASSWORD_AUTH`

### Solution 4: Frontend Configuration Check

**Verify Amplify Configuration** in the frontend:

1. **Check `frontend/src/aws-exports.js`** (generated file):
   ```javascript
   const awsconfig = {
     Auth: {
       region: 'us-east-1',
       userPoolId: 'us-east-1_11Ciomg6j',
       userPoolWebClientId: 'CLIENT_ID',
       // Ensure these are set correctly
       authenticationFlowType: 'USER_SRP_AUTH',
       // Password reset configuration
       passwordResetRequired: false,
       passwordResetOptional: true
     }
   };
   ```

2. **Check Frontend Password Reset Implementation**:
   ```typescript
   // In the login component
   import { Auth } from 'aws-amplify';
   
   const handleForgotPassword = async (username: string) => {
     try {
       await Auth.forgotPassword(username);
       // Should trigger email send
     } catch (error) {
       console.error('Password reset error:', error);
     }
   };
   ```

## Immediate Workaround

**For Testing the Application Right Now:**

1. **Create a new user with verified email**:
   ```bash
   # Create user
   aws cognito-idp admin-create-user \
     --user-pool-id us-east-1_11Ciomg6j \
     --username testuser@example.com \
     --user-attributes Name=email,Value=testuser@example.com Name=email_verified,Value=true \
     --temporary-password TempPass123! \
     --message-action SUPPRESS
   
   # Set permanent password
   aws cognito-idp admin-set-user-password \
     --user-pool-id us-east-1_11Ciomg6j \
     --username testuser@example.com \
     --password TestPassword123! \
     --permanent
   ```

2. **Login with the new credentials**:
   - Username: `testuser@example.com`
   - Password: `TestPassword123!`

## Verification Steps

After implementing the fix:

1. **Test Password Reset Flow**:
   - Go to the login page
   - Click "Forgot Password"
   - Enter email address
   - Check for password reset email
   - Complete password reset process

2. **Check Email Delivery**:
   ```bash
   # Check SES sending statistics (if SES is configured)
   aws ses get-send-statistics
   ```

3. **Monitor Cognito Logs**:
   ```bash
   # Check CloudTrail for Cognito API calls
   aws logs filter-log-events \
     --log-group-name /aws/cognito/userpools \
     --start-time $(date -d '1 hour ago' +%s)000
   ```

## Prevention

To prevent similar issues in the future:

1. **Always Configure SES**: For production environments, always use Amazon SES
2. **Email Verification**: Ensure users complete email verification during signup
3. **Testing**: Include password reset testing in deployment verification
4. **Monitoring**: Set up CloudWatch alarms for failed authentication attempts

## Environment-Specific Information

### Test Environment (Current Issue)
- **User Pool ID**: `us-east-1_11Ciomg6j`
- **User Pool Name**: `aws-elasticdrs-orchestrator-users-test`
- **Region**: `us-east-1`
- **CloudFront URL**: `https://d2tcslzsi48r3z.cloudfront.net`
- **API Gateway**: `https://caderd84ha.execute-api.us-east-1.amazonaws.com/test`

### Dev Environment (Reference)
- **User Pool ID**: Check CloudFormation outputs
- **User Pool Name**: `aws-elasticdrs-orchestrator-users-dev`

## Related Files

- `cfn/api-stack-rbac.yaml` - Cognito User Pool configuration
- `frontend/src/components/auth/LoginPage.tsx` - Frontend login component
- `frontend/src/aws-exports.js` - Amplify configuration (generated)
- `docs/guides/troubleshooting/COGNITO_PASSWORD_RESET_FIX.md` - This documentation

## Security Considerations

When implementing fixes:

1. **Temporary Passwords**: Always set temporary passwords that require change on first login
2. **Email Verification**: Ensure email addresses are verified before allowing password reset
3. **Rate Limiting**: Cognito has built-in rate limiting for password reset attempts
4. **Audit Logging**: All password reset attempts are logged in CloudTrail

## Missing Notification Infrastructure

**IMPORTANT**: The test environment should also have deployed comprehensive notification infrastructure that appears to be missing:

### Expected Notification Components

1. **SNS Topic**: `aws-elasticdrs-orchestrator-pipeline-notifications-test`
2. **Notification Formatter Lambda**: `aws-elasticdrs-orchestrator-notification-formatter-test`
3. **EventBridge Rules**: Pipeline failure and security scan failure triggers
4. **Email Notifications**: Formatted notifications for CI/CD events

### Verify Notification Infrastructure

```bash
# Check if SNS topic exists
aws sns list-topics --query 'Topics[?contains(TopicArn, `pipeline-notifications`)]'

# Check if notification formatter Lambda exists
aws lambda get-function --function-name aws-elasticdrs-orchestrator-notification-formatter-test

# Check EventBridge rules
aws events list-rules --name-prefix aws-elasticdrs-orchestrator
```

### Expected Notification Features

The notification formatter Lambda (`lambda/notification-formatter/index.py`) should:
- Process raw EventBridge JSON events from CodePipeline and CodeBuild
- Format them into user-friendly email notifications with:
  - Pipeline failure alerts with console links
  - Security scan failure alerts
  - Build status notifications
  - Formatted timestamps and execution details

If these components are missing, the CI/CD pipeline notifications won't work properly.

## Next Steps

1. **Immediate**: Use the workaround to create a test user with verified email
2. **Short-term**: Verify existing users' email addresses  
3. **Verify Notifications**: Check if the notification infrastructure is properly deployed
4. **Long-term**: Configure Amazon SES for reliable email delivery
5. **Testing**: Verify the complete password reset flow works end-to-end

This should resolve the password reset issue and allow you to test the application functionality.