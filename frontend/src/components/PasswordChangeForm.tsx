/**
 * Password Change Form Component
 * 
 * Handles the NEW_PASSWORD_REQUIRED challenge from Cognito
 * when a user needs to change their temporary password.
 */

import React, { useState } from 'react';
import { SpaceBetween, Alert, FormField, Input, Button, Box } from '@cloudscape-design/components';
import { confirmSignIn } from 'aws-amplify/auth';
import type { ConfirmSignInInput } from 'aws-amplify/auth';

interface PasswordChangeFormProps {
  username: string;
  onPasswordChanged: () => void;
  onCancel: () => void;
}

export const PasswordChangeForm: React.FC<PasswordChangeFormProps> = ({
  username,
  onPasswordChanged,
  onCancel,
}) => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const validatePassword = (password: string): string | null => {
    if (password.length < 8) {
      return 'Password must be at least 8 characters long';
    }
    if (!/(?=.*[a-z])/.test(password)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/(?=.*[A-Z])/.test(password)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/(?=.*\d)/.test(password)) {
      return 'Password must contain at least one number';
    }
    if (!/(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])/.test(password)) {
      return 'Password must contain at least one special character';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate new password
    const passwordError = validatePassword(newPassword);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    // Check password confirmation
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      // Ensure Amplify is configured (in case it wasn't configured yet)
      if (window.AWS_CONFIG) {
        const { Amplify } = await import('aws-amplify');
        const cleanConfig = {
          Auth: {
            Cognito: {
              region: window.AWS_CONFIG.Auth.Cognito.region,
              userPoolId: window.AWS_CONFIG.Auth.Cognito.userPoolId,
              userPoolClientId: window.AWS_CONFIG.Auth.Cognito.userPoolClientId,
              loginWith: {
                email: true
              }
            }
          },
          API: window.AWS_CONFIG.API
        };
        Amplify.configure(cleanConfig);
      }

      const confirmSignInInput: ConfirmSignInInput = {
        challengeResponse: newPassword,
      };

      const result = await confirmSignIn(confirmSignInInput);

      if (result.isSignedIn) {
        onPasswordChanged();
      } else {
        setError('Password change failed. Please try again.');
      }
    } catch (err: unknown) {
      console.error('Password change error:', err);
      const message = err instanceof Error ? err.message : 'Password change failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleButtonClick = () => {
    const form = document.getElementById('password-change-form') as HTMLFormElement;
    if (form) {
      form.requestSubmit();
    }
  };

  return (
    <div style={{
      backgroundColor: '#ffffff',
      borderRadius: '8px',
      padding: '32px',
      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.3)',
    }}>
      <h1 style={{
        fontSize: '24px',
        fontWeight: 700,
        color: '#16191f',
        margin: '0 0 8px 0',
        textAlign: 'center',
      }}>
        Change Password
      </h1>
      
      <p style={{
        fontSize: '14px',
        color: '#5f6b7a',
        textAlign: 'center',
        margin: '0 0 24px 0',
      }}>
        Your password needs to be changed before you can continue.
      </p>

      <form id="password-change-form" onSubmit={handleSubmit}>
        <SpaceBetween direction="vertical" size="l">
          {error && (
            <Alert type="error" dismissible onDismiss={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box>
            <div style={{
              fontSize: '14px',
              fontWeight: 600,
              color: '#16191f',
              marginBottom: '8px',
            }}>
              User: {username}
            </div>
          </Box>

          <FormField
            label="New Password"
            description="Password must be at least 8 characters with uppercase, lowercase, number, and special character"
          >
            <Input
              type="password"
              value={newPassword}
              onChange={({ detail }) => setNewPassword(detail.value)}
              placeholder="Enter your new password"
              autoComplete="new-password"
              autoFocus
            />
          </FormField>

          <FormField
            label="Confirm New Password"
          >
            <Input
              type="password"
              value={confirmPassword}
              onChange={({ detail }) => setConfirmPassword(detail.value)}
              placeholder="Confirm your new password"
              autoComplete="new-password"
            />
          </FormField>

          <SpaceBetween direction="horizontal" size="xs">
            <Button
              variant="link"
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleButtonClick}
              loading={loading}
              disabled={!newPassword || !confirmPassword}
            >
              Change Password
            </Button>
          </SpaceBetween>
        </SpaceBetween>
      </form>
    </div>
  );
};

export default PasswordChangeForm;