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
  SpaceBetween,
  Button,
  FormField,
  Input,
  Alert,
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
        width: '100vw',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #232F3E 0%, #1a242f 100%)',
        fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
        margin: 0,
        padding: 0,
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '40px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
        }}
      >
        <SpaceBetween size="l">
          {/* Header with AWS Logo */}
          <div style={{ textAlign: 'center' }}>
            <img 
              src="https://d0.awsstatic.com/logos/powered-by-aws.png" 
              alt="Powered by AWS"
              style={{ height: '40px', marginBottom: '20px' }}
            />
            <h1 style={{ 
              fontSize: '20px', 
              fontWeight: 700, 
              color: '#232F3E',
              margin: '0 0 8px 0',
              fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
            }}>
              Elastic Disaster Recovery Orchestrator
            </h1>
            <p style={{ 
              color: '#5f6b7a', 
              margin: 0, 
              fontSize: '14px',
              fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
            }}>
              Enterprise Disaster Recovery Management
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
        </SpaceBetween>
      </div>
    </div>
  );
};
