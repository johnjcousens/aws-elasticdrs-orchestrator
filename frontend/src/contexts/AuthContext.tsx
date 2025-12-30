/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the application.
 * Uses AWS Amplify for Cognito integration.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Amplify } from 'aws-amplify';
import {
  signIn,
  signOut,
  getCurrentUser,
  fetchAuthSession,
  fetchUserAttributes,
} from 'aws-amplify/auth';
import type { SignInInput, SignInOutput } from 'aws-amplify/auth';
import { awsConfig } from '../aws-config';
import type { User, AuthState } from '../types';

// Configure Amplify with explicit region validation
const amplifyConfig = {
  Auth: {
    Cognito: {
      region: awsConfig.Auth?.Cognito?.region || 'us-east-1',
      userPoolId: awsConfig.Auth?.Cognito?.userPoolId,
      userPoolClientId: awsConfig.Auth?.Cognito?.userPoolClientId,
      identityPoolId: awsConfig.Auth?.Cognito?.identityPoolId,
      loginWith: {
        email: true
      }
    }
  },
  API: awsConfig.API
};

console.log('🔧 Amplify configuration:', JSON.stringify(amplifyConfig, null, 2));
Amplify.configure(amplifyConfig);

interface AuthContextType extends AuthState {
  signIn: (username: string, password: string) => Promise<SignInOutput>;
  signOut: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication Provider Component
 * 
 * Wraps the application and provides authentication context to all child components.
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: undefined,
  });

  // Auto-logout timer (45 minutes)
  const AUTO_LOGOUT_TIME = 45 * 60 * 1000; // 45 minutes in milliseconds
  const [logoutTimer, setLogoutTimer] = useState<NodeJS.Timeout | null>(null);

  /**
   * Start auto-logout timer
   */
  const startLogoutTimer = () => {
    if (logoutTimer) {
      clearTimeout(logoutTimer);
    }
    
    const timer = setTimeout(() => {
      console.log('Auto-logout: Session expired');
      handleSignOut();
    }, AUTO_LOGOUT_TIME);
    
    setLogoutTimer(timer);
  };

  /**
   * Clear auto-logout timer
   */
  const clearLogoutTimer = () => {
    if (logoutTimer) {
      clearTimeout(logoutTimer);
      setLogoutTimer(null);
    }
  };

  /**
   * Check if user is authenticated on mount
   */
  useEffect(() => {
    checkAuth();
  }, []);

  /**
   * Clean up timer on unmount
   */
  useEffect(() => {
    return () => {
      clearLogoutTimer();
    };
  }, []);

  /**
   * Check current authentication status
   */
  const checkAuth = async (): Promise<void> => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Check if we're in local development mode AND using localhost API
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiEndpoint = awsConfig.API?.REST?.DRSOrchestration?.endpoint || '';
      const isUsingLocalAPI = apiEndpoint.includes('localhost') || apiEndpoint.includes('127.0.0.1');
      
      if (isLocalDev && isUsingLocalAPI) {
        // Mock authentication only when using local API
        console.log('🔧 Local development mode with local API - using mock authentication');
        setAuthState({
          isAuthenticated: true,
          user: {
            username: 'local-dev-user',
            email: 'dev@localhost.com',
          },
          loading: false,
          error: undefined,
        });
        return;
      }

      // Get current authenticated user
      const user = await getCurrentUser();
      
      // Get auth session to verify token is valid
      const session = await fetchAuthSession();
      
      if (user && session.tokens) {
        // Fetch user attributes to get email
        let email = user.signInDetails?.loginId;
        try {
          const attributes = await fetchUserAttributes();
          email = attributes.email || email;
        } catch (attrError) {
          console.warn('Could not fetch user attributes:', attrError);
        }
        
        setAuthState({
          isAuthenticated: true,
          user: {
            username: user.username,
            email: email,
          },
          loading: false,
          error: undefined,
        });
        
        // Start auto-logout timer
        startLogoutTimer();
      } else {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
      }
    } catch (error) {
      // Not logged in is expected on login page - don't log as error
      // Clear auto-logout timer on auth failure
      clearLogoutTimer();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    }
  };

  /**
   * Sign in user with username and password
   */
  const handleSignIn = async (
    username: string,
    password: string
  ): Promise<SignInOutput> => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Check if we're in local development mode AND using localhost API
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiEndpoint = awsConfig.API?.REST?.DRSOrchestration?.endpoint || '';
      const isUsingLocalAPI = apiEndpoint.includes('localhost') || apiEndpoint.includes('127.0.0.1');
      
      if (isLocalDev && isUsingLocalAPI) {
        // Mock sign-in only when using local API
        console.log('🔧 Local development mode with local API - mock sign-in successful');
        setAuthState({
          isAuthenticated: true,
          user: {
            username: username,
            email: `${username}@localhost.com`,
          },
          loading: false,
          error: undefined,
        });
        
        // Return mock successful sign-in result
        return {
          isSignedIn: true,
          nextStep: { signInStep: 'DONE' }
        } as SignInOutput;
      }

      const signInInput: SignInInput = {
        username,
        password,
      };

      const result = await signIn(signInInput);

      // Check if sign-in was successful
      if (result.isSignedIn) {
        // Refresh auth state
        await checkAuth();
      }

      return result;
    } catch (error: any) {
      console.error('Sign in failed:', error);
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: error.message || 'Sign in failed',
      }));
      throw error;
    }
  };

  /**
   * Sign out current user
   */
  const handleSignOut = async (): Promise<void> => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Check if we're in local development mode
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      if (isLocalDev) {
        // Mock sign-out for local development
        console.log('🔧 Local development mode - mock sign-out');
        clearLogoutTimer();
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
        return;
      }

      await signOut();

      // Clear auto-logout timer
      clearLogoutTimer();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    } catch (error: any) {
      console.error('Sign out failed:', error);
      // Clear timer even if sign out fails
      clearLogoutTimer();
      
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: error.message || 'Sign out failed',
      }));
      throw error;
    }
  };

  const value: AuthContextType = {
    ...authState,
    signIn: handleSignIn,
    signOut: handleSignOut,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Custom hook to use authentication context
 * 
 * @throws Error if used outside of AuthProvider
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthContext;
