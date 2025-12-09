/**
 * Login Page Component
 * 
 * Authentication page with username/password form.
 * Uses AWS Amplify Cognito for authentication.
 * Styled to match AWS Console login standards.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  SpaceBetween,
  FormField,
  Alert,
} from '@cloudscape-design/components';

/**
 * Login Page
 * 
 * Provides authentication form for users to sign in with Cognito credentials.
 * Styled to match AWS Console login experience.
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
        navigate('/');
      } else {
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
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f2f3f3',
        fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
        margin: 0,
        padding: '20px',
        boxSizing: 'border-box',
      }}
    >
      {/* AWS Logo */}
      <div style={{ marginBottom: '32px' }}>
        <svg width="76" height="46" viewBox="0 0 76 46" xmlns="http://www.w3.org/2000/svg">
          <path d="M21.5 25.5c0 .8.1 1.5.2 2 .2.5.4 1 .7 1.6.1.2.2.3.2.5 0 .2-.1.4-.4.6l-1.2.8c-.2.1-.3.2-.5.2-.2 0-.4-.1-.6-.3-.3-.3-.5-.6-.7-1-.2-.4-.4-.8-.6-1.3-1.5 1.8-3.4 2.7-5.7 2.7-1.6 0-2.9-.5-3.9-1.4-1-.9-1.5-2.2-1.5-3.7 0-1.6.6-3 1.8-3.9 1.2-1 2.8-1.5 4.8-1.5.7 0 1.4 0 2.1.1.7.1 1.5.2 2.3.4v-1.4c0-1.5-.3-2.5-.9-3.1-.6-.6-1.7-.9-3.2-.9-.7 0-1.4.1-2.1.3-.7.2-1.4.4-2.1.7-.3.1-.5.2-.7.3-.2 0-.3.1-.4.1-.3 0-.5-.2-.5-.7v-1c0-.4.1-.6.2-.8.1-.2.4-.3.7-.5.7-.4 1.5-.7 2.5-.9 1-.3 2-.4 3.1-.4 2.4 0 4.1.5 5.2 1.6 1.1 1.1 1.6 2.7 1.6 4.9v6.5h.1zm-7.9 3c.7 0 1.4-.1 2.1-.4.7-.3 1.4-.7 1.9-1.3.3-.4.6-.8.7-1.3.1-.5.2-1.1.2-1.8v-.9c-.6-.1-1.2-.2-1.9-.3-.7-.1-1.3-.1-2-.1-1.3 0-2.3.3-2.9.8-.6.5-1 1.3-1 2.3 0 .9.2 1.6.7 2.1.5.6 1.2.9 2.2.9zm15.6 2.1c-.4 0-.7-.1-.9-.2-.2-.2-.4-.5-.5-.9l-5.7-18.8c-.1-.4-.2-.7-.2-.9 0-.4.2-.6.6-.6h1.9c.4 0 .7.1.9.2.2.2.3.5.4.9l4.1 16.1 3.8-16.1c.1-.5.2-.7.4-.9.2-.2.5-.2.9-.2h1.5c.4 0 .7.1.9.2.2.2.4.5.4.9l3.8 16.3 4.2-16.3c.1-.5.2-.7.4-.9.2-.2.5-.2.9-.2h1.8c.4 0 .6.2.6.6 0 .1 0 .3-.1.4 0 .2-.1.3-.2.6l-5.8 18.8c-.1.5-.3.7-.5.9-.2.2-.5.2-.9.2h-1.7c-.4 0-.7-.1-.9-.2-.2-.2-.4-.5-.4-.9l-3.7-15.7-3.7 15.6c-.1.5-.2.7-.4.9-.2.2-.5.2-.9.2h-1.7zm25 .5c-1 0-2-.1-3-.4-1-.3-1.7-.5-2.2-.9-.3-.2-.5-.4-.6-.6-.1-.2-.1-.4-.1-.6v-1c0-.5.2-.7.5-.7.1 0 .3 0 .4.1.1.1.3.1.5.2.7.3 1.4.6 2.2.7.8.2 1.6.3 2.4.3 1.3 0 2.2-.2 2.9-.7.7-.5 1-1.1 1-1.9 0-.6-.2-1-.5-1.4-.4-.4-1-.7-1.9-1l-2.8-.9c-1.4-.4-2.4-1.1-3-2-.6-.8-.9-1.8-.9-2.8 0-.8.2-1.5.5-2.2.4-.6.8-1.2 1.4-1.6.6-.5 1.3-.8 2.1-1 .8-.2 1.7-.3 2.6-.3.5 0 .9 0 1.4.1.5.1.9.2 1.4.3.4.1.8.3 1.2.4.4.2.7.3.9.5.3.2.5.4.6.6.1.2.2.5.2.8v.9c0 .5-.2.7-.5.7-.2 0-.5-.1-.9-.3-1.3-.6-2.8-.9-4.4-.9-1.1 0-2 .2-2.6.6-.6.4-.9 1-.9 1.8 0 .6.2 1.1.6 1.4.4.4 1.1.7 2.1 1.1l2.7.9c1.4.4 2.3 1.1 2.9 1.9.6.8.8 1.7.8 2.7 0 .8-.2 1.6-.5 2.2-.4.7-.8 1.2-1.5 1.7-.6.5-1.4.8-2.2 1-.9.3-1.8.4-2.8.4z" fill="#252F3E"/>
          <path d="M43.6 35.5c-5.3 3.9-13 6-19.6 6-9.3 0-17.6-3.4-23.9-9.1-.5-.5-.1-1.1.5-.7 6.8 4 15.2 6.3 23.9 6.3 5.9 0 12.3-1.2 18.2-3.7.9-.4 1.6.6.9 1.2z" fill="#FF9900"/>
          <path d="M45.9 32.8c-.7-.9-4.4-.4-6.1-.2-.5.1-.6-.4-.1-.7 3-2.1 7.9-1.5 8.4-.8.6.7-.2 5.7-2.9 8.1-.4.4-.8.2-.6-.3.6-1.5 2-4.8 1.3-6.1z" fill="#FF9900"/>
        </svg>
      </div>

      {/* Login Card */}
      <div
        style={{
          width: '100%',
          maxWidth: '350px',
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)',
          border: '1px solid #d5dbdb',
          overflow: 'hidden',
        }}
      >
        {/* Card Header */}
        <div
          style={{
            padding: '24px 24px 0 24px',
            borderBottom: 'none',
          }}
        >
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: 400, 
            color: '#16191f',
            margin: '0 0 8px 0',
            fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
          }}>
            Sign in
          </h1>
          <p style={{ 
            color: '#545b64', 
            margin: 0, 
            fontSize: '14px',
            fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
          }}>
            Elastic Disaster Recovery Orchestrator
          </p>
        </div>

        {/* Card Body */}
        <div style={{ padding: '24px' }}>
          <SpaceBetween size="l">
            {/* Error Alert */}
            {error && (
              <Alert type="error">
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <SpaceBetween size="l">
                <FormField label="Username or email">
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    autoFocus
                    autoComplete="username"
                    style={{
                      width: '100%',
                      padding: '8px 36px 8px 12px',
                      fontSize: '14px',
                      fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                      border: '1px solid #aab7b8',
                      borderRadius: '3px',
                      boxSizing: 'border-box',
                      outline: 'none',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#0073bb';
                      e.currentTarget.style.boxShadow = '0 0 0 1px #0073bb';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#aab7b8';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                </FormField>

                <FormField label="Password">
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    autoComplete="current-password"
                    style={{
                      width: '100%',
                      padding: '8px 36px 8px 12px',
                      fontSize: '14px',
                      fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                      border: '1px solid #aab7b8',
                      borderRadius: '3px',
                      boxSizing: 'border-box',
                      outline: 'none',
                    }}
                    onFocus={(e) => {
                      e.currentTarget.style.borderColor = '#0073bb';
                      e.currentTarget.style.boxShadow = '0 0 0 1px #0073bb';
                    }}
                    onBlur={(e) => {
                      e.currentTarget.style.borderColor = '#aab7b8';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  />
                </FormField>

                {/* AWS Orange Sign In Button */}
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: '100%',
                    padding: '8px 20px',
                    fontSize: '14px',
                    fontWeight: 700,
                    fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
                    color: '#16191f',
                    backgroundColor: loading ? '#f2a64d' : '#ff9900',
                    border: '1px solid #a88734',
                    borderRadius: '3px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.4)',
                    transition: 'background-color 0.1s ease',
                  }}
                  onMouseOver={(e) => {
                    if (!loading) {
                      e.currentTarget.style.backgroundColor = '#ec8b00';
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!loading) {
                      e.currentTarget.style.backgroundColor = '#ff9900';
                    }
                  }}
                >
                  {loading ? 'Signing in...' : 'Sign in'}
                </button>
              </SpaceBetween>
            </form>
          </SpaceBetween>
        </div>
      </div>

      {/* Footer */}
      <div style={{ marginTop: '24px', textAlign: 'center' }}>
        <p style={{ 
          color: '#545b64', 
          fontSize: '12px',
          fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
          margin: 0,
        }}>
          © 2024, Amazon Web Services, Inc. or its affiliates.
        </p>
      </div>
    </div>
  );
};
