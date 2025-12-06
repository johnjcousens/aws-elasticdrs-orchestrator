/**
 * Login Page Component
 * 
 * Authentication page with username/password form.
 * Uses AWS Amplify Cognito for authentication.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Alert,
  Container,
  Header,
} from '@cloudscape-design/components';

/**
 * Login Page
 * 
 * Provides authentication form for users to sign in with Cognito credentials.
 */
export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { signIn, isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await signIn(username, password);
      
      if (result.isSignedIn) {
        // Navigate to dashboard on successful login
        navigate('/');
      } else {
        // Handle additional authentication steps if needed
        setError('Additional authentication steps required');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #232F3E 0%, #FF9900 100%)',
      }}
    >
      <Container>
        <div
          style={{
            maxWidth: '400px',
            margin: '0 auto',
            padding: '2rem',
            backgroundColor: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          <SpaceBetween size="l">
            {/* Header */}
            <div style={{ textAlign: 'center' }}>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: '#232F3E',
                  marginBottom: '1rem',
                }}
              >
                <span style={{ fontSize: '32px' }}>🔒</span>
              </div>
              <Header variant="h1">AWS DRS Orchestration</Header>
              <p style={{ color: '#5f6b7a', marginTop: '0.5rem' }}>
                Sign in to access the platform
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <Alert type="error">
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <SpaceBetween size="l">
                <FormField label="Username">
                  <Input
                    value={username}
                    onChange={({ detail }) => setUsername(detail.value)}
                    placeholder="Enter your username"
                    disabled={loading}
                    autoFocus
                  />
                </FormField>

                <FormField label="Password">
                  <Input
                    value={password}
                    onChange={({ detail }) => setPassword(detail.value)}
                    type="password"
                    placeholder="Enter your password"
                    disabled={loading}
                  />
                </FormField>

                <Button
                  variant="primary"
                  formAction="submit"
                  fullWidth
                  disabled={loading}
                  loading={loading}
                >
                  Sign In
                </Button>
              </SpaceBetween>
            </form>

            {/* Footer */}
            <div style={{ textAlign: 'center', fontSize: '12px', color: '#5f6b7a' }}>
              Powered by AWS Cognito
            </div>
          </SpaceBetween>
        </div>
      </Container>
    </div>
  );
};
