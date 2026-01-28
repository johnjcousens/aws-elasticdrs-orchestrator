/**
 * Login Page Component
 *
 * Authentication page with username/password form.
 * Uses AWS Amplify Cognito for authentication.
 * Styled to match AWS IAM Identity Center login standards.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { SpaceBetween, Alert, Link } from '@cloudscape-design/components';
import { PasswordChangeForm } from '../components/PasswordChangeForm';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { 
    signIn, 
    isAuthenticated, 
    loading: authLoading, 
    needsPasswordChange, 
    currentUsername,
    handlePasswordChanged 
  } = useAuth();
  const navigate = useNavigate();

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
      } else if (result.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
        // Password change will be handled by the needsPasswordChange state
        console.log('Password change required');
      } else {
        setError('Additional authentication steps required');
      }
    } catch (err: unknown) {
      console.error('Login error:', err);
      const message = err instanceof Error ? err.message : 'Authentication failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChangeComplete = async () => {
    try {
      await handlePasswordChanged();
      navigate('/');
    } catch (err: unknown) {
      console.error('Password change completion error:', err);
      const message = err instanceof Error ? err.message : 'Password change completion failed.';
      setError(message);
    }
  };

  const handlePasswordChangeCancel = () => {
    // Reset form state
    setUsername('');
    setPassword('');
    setError(null);
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 12px',
    fontSize: '14px',
    fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
    border: '1px solid #aab7b8',
    borderRadius: '3px',
    boxSizing: 'border-box' as const,
    outline: 'none',
  };

  const buttonStyle: React.CSSProperties = {
    width: '100%',
    padding: '8px 16px',
    fontSize: '14px',
    fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
    backgroundColor: '#ec7211',
    color: '#fff',
    border: 'none',
    borderRadius: '3px',
    cursor: loading ? 'not-allowed' : 'pointer',
    opacity: loading ? 0.6 : 1,
  };

  // Cube component for cleaner JSX
  const Cube = ({ color, lightColor, darkColor, sideColor }: { color: string; lightColor: string; darkColor: string; sideColor: string }) => (
    <svg width="80" height="92" viewBox="0 0 80 92" style={{ filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))' }}>
      <polygon points="40,0 80,23 80,69 40,92 0,69 0,23" fill={color} />
      <polygon points="40,0 80,23 40,46 0,23" fill={lightColor} />
      <polygon points="0,23 40,46 40,92 0,69" fill={darkColor} />
      <polygon points="80,23 40,46 40,92 80,69" fill={sideColor} />
    </svg>
  );

  const cubeColors = [
    { color: '#FF9900', lightColor: '#FFB84D', darkColor: '#CC7A00', sideColor: '#E68A00' },
    { color: '#1DC7B4', lightColor: '#4DD9CA', darkColor: '#17A090', sideColor: '#1AB3A2' },
    { color: '#9469D6', lightColor: '#B08DE6', darkColor: '#7654AB', sideColor: '#855EC0' },
    { color: '#527FFF', lightColor: '#7A9FFF', darkColor: '#4266CC', sideColor: '#4A72E6' },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#232f3e',
      fontFamily: '"Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif',
    }}>
      {/* Main content area */}
      <div style={{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '40px 20px',
      }}>
        <div style={{ width: '100%', maxWidth: '400px' }}>
          {/* AWS Logo and Title */}
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <img
              src="/aws-logo@2x.png"
              alt="AWS"
              style={{ height: '50px', marginBottom: '16px' }}
            />
            <div style={{
              color: '#ffffff',
              fontSize: '20px',
              fontWeight: 700,
              letterSpacing: '0.5px',
            }}>
              Elastic Disaster Recovery Orchestrator
            </div>
          </div>

          {/* Login Card or Password Change Form */}
          {needsPasswordChange && currentUsername ? (
            <PasswordChangeForm
              username={currentUsername}
              onPasswordChanged={handlePasswordChangeComplete}
              onCancel={handlePasswordChangeCancel}
            />
          ) : (
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
                margin: '0 0 24px 0',
                textAlign: 'center',
              }}>
                Sign in
              </h1>

              <form 
                onSubmit={handleSubmit}
                method="post"
                action="#"
                autoComplete="on"
              >
                <SpaceBetween direction="vertical" size="l">
                  {error && (
                    <Alert type="error" dismissible onDismiss={() => setError(null)}>
                      {error}
                    </Alert>
                  )}

                  <div>
                    <label htmlFor="login-username" style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: 600, color: '#16191f' }}>
                      Username or email
                    </label>
                    <input
                      id="login-username"
                      name="username"
                      type="email"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      style={inputStyle}
                      placeholder="Enter your username"
                      required
                      autoComplete="username"
                      autoFocus
                    />
                  </div>

                  <div>
                    <label htmlFor="login-password" style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: 600, color: '#16191f' }}>
                      Password
                    </label>
                    <input
                      id="login-password"
                      name="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      style={inputStyle}
                      placeholder="Enter your password"
                      required
                      autoComplete="current-password"
                      data-lpignore="false"
                    />
                  </div>

                  <button type="submit" style={buttonStyle} disabled={loading}>
                    {loading ? 'Signing in...' : 'Sign in'}
                  </button>
                </SpaceBetween>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* 3D Isometric Cubes */}
      <div style={{
        height: '120px',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        gap: '20px',
        paddingBottom: '20px',
      }}>
        {[...Array(12)].map((_, i) => (
          <Cube key={i} {...cubeColors[i % 4]} />
        ))}
      </div>

      {/* Disclaimer Footer - Compact */}
      <div style={{
        backgroundColor: '#1a242f',
        padding: '12px 40px',
        borderTop: '1px solid #3d4f5f',
      }}>
        <div style={{
          maxWidth: '1100px',
          margin: '0 auto',
          color: '#8d9ba8',
          fontSize: '10px',
          lineHeight: '1.5',
        }}>
          <span style={{ fontWeight: 600, color: '#aab7b8' }}>Disclaimer: </span>
          This AWS Elastic Disaster Recovery Orchestrator is a sample implementation provided by AWS Professional Services as a reference architecture. 
          <strong> This tool is provided "AS IS" without warranty of any kind.</strong> Amazon Web Services is not responsible for any damages, data loss, or service disruptions arising from its use. 
          This is not an official AWS product and is not covered by AWS Support plans. By using this tool, you acknowledge that you are responsible for testing, validating, and maintaining it within your environment. 
          For continued development, we recommend{' '}
          <Link
            href="https://aws.amazon.com/q/developer/"
            external
            variant="secondary"
            fontSize="inherit"
          >
            Amazon Q Developer
          </Link>.
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
