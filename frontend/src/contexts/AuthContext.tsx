/**
 * Authentication Context
 * 
 * Provides authentication state and methods throughout the application.
 * Uses AWS Amplify for Cognito integration.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
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
import type { AuthState } from '../types';

// Flag to track if Amplify has been configured
let amplifyConfigured = false;

// Function to configure Amplify dynamically when config is available
const configureAmplify = () => {
  if (amplifyConfigured) return;
  
  // Get config from window.AWS_CONFIG (loaded by index.html script)
  const config = window.AWS_CONFIG;
  
  if (!config) {
    console.warn('⚠️ AWS_CONFIG not available, using fallback configuration');
    // Fallback configuration for development
    const fallbackConfig = {
      Auth: {
        Cognito: {
          region: 'us-east-1',
          userPoolId: '***REMOVED***',
          userPoolClientId: '***REMOVED***',
          loginWith: {
            email: true
          }
        }
      },
      API: {
        REST: {
          DRSOrchestration: {
            endpoint: 'https://***REMOVED***.execute-api.us-east-1.amazonaws.com/dev',
            region: 'us-east-1'
          }
        }
      }
    };
    Amplify.configure(fallbackConfig);
  } else {
    console.log('✅ Configuring Amplify with loaded AWS config');
    // Create a clean config without optional identityPoolId
    const cleanConfig = {
      Auth: {
        Cognito: {
          region: config.Auth.Cognito.region,
          userPoolId: config.Auth.Cognito.userPoolId,
          userPoolClientId: config.Auth.Cognito.userPoolClientId,
          loginWith: {
            email: true
          }
        }
      },
      API: config.API
    };
    Amplify.configure(cleanConfig);
  }
  
  amplifyConfigured = true;
};

interface AuthContextType extends AuthState {
  signIn: (username: string, password: string) => Promise<SignInOutput>;
  signOut: () => Promise<void>;
  checkAuth: () => Promise<void>;
  needsPasswordChange: boolean;
  currentUsername: string | null;
  handlePasswordChanged: () => Promise<void>;
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

  const [needsPasswordChange, setNeedsPasswordChange] = useState(false);
  const [currentUsername, setCurrentUsername] = useState<string | null>(null);

  // Auto-logout timer (45 minutes)
  const AUTO_LOGOUT_TIME = 45 * 60 * 1000; // 45 minutes in milliseconds
  
  // Use refs to avoid dependency cycles that cause infinite re-renders
  const logoutTimerRef = useRef<NodeJS.Timeout | null>(null);
  const authCheckInProgressRef = useRef(false);
  const hasCheckedAuthRef = useRef(false);

  /**
   * Clear auto-logout timer
   */
  const clearLogoutTimer = useCallback(() => {
    if (logoutTimerRef.current) {
      clearTimeout(logoutTimerRef.current);
      logoutTimerRef.current = null;
    }
  }, []);

  /**
   * Start auto-logout timer
   */
  const startLogoutTimer = useCallback(() => {
    clearLogoutTimer();
    
    logoutTimerRef.current = setTimeout(() => {
      // Sign out when timer expires
      signOut().then(() => {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
      }).catch(console.error);
    }, AUTO_LOGOUT_TIME);
  }, [clearLogoutTimer]);

  /**
   * Check current authentication status
   */
  const checkAuth = useCallback(async (): Promise<void> => {
    // Prevent concurrent auth checks that cause rate limiting
    if (authCheckInProgressRef.current) {
      return;
    }
    
    authCheckInProgressRef.current = true;
    
    try {
      // Ensure Amplify is configured before any operations
      configureAmplify();
      
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Check if we're in local development mode AND using localhost API
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiEndpoint = window.AWS_CONFIG?.API?.REST?.DRSOrchestration?.endpoint || '';
      const isUsingLocalAPI = apiEndpoint.includes('localhost') || apiEndpoint.includes('127.0.0.1');
      
      if (isLocalDev && isUsingLocalAPI) {
        // Mock authentication only when using local API
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
    } catch {
      // Not logged in is expected on login page - don't log as error
      // Clear auto-logout timer on auth failure
      clearLogoutTimer();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    } finally {
      authCheckInProgressRef.current = false;
    }
  }, [clearLogoutTimer, startLogoutTimer]);

  /**
   * Check if user is authenticated on mount only once
   */
  useEffect(() => {
    if (!hasCheckedAuthRef.current) {
      hasCheckedAuthRef.current = true;
      checkAuth();
    }
  }, [checkAuth]);

  /**
   * Clean up timer on unmount
   */
  useEffect(() => {
    return () => {
      if (logoutTimerRef.current) {
        clearTimeout(logoutTimerRef.current);
      }
    };
  }, []);

  /**
   * Sign in user with username and password
   */
  const handleSignIn = async (
    username: string,
    password: string
  ): Promise<SignInOutput> => {
    try {
      // Ensure Amplify is configured before any operations
      configureAmplify();
      
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));
      setNeedsPasswordChange(false);
      setCurrentUsername(null);

      // Check if we're in local development mode AND using localhost API
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiEndpoint = window.AWS_CONFIG?.API?.REST?.DRSOrchestration?.endpoint || '';
      const isUsingLocalAPI = apiEndpoint.includes('localhost') || apiEndpoint.includes('127.0.0.1');
      
      if (isLocalDev && isUsingLocalAPI) {
        // Mock sign-in only when using local API
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
        setNeedsPasswordChange(false);
        setCurrentUsername(null);
      } else if (result.nextStep?.signInStep === 'CONFIRM_SIGN_IN_WITH_NEW_PASSWORD_REQUIRED') {
        // User needs to change password
        setNeedsPasswordChange(true);
        setCurrentUsername(username);
        setAuthState((prev) => ({ ...prev, loading: false }));
      }

      return result;
    } catch (error) {
      console.error('Sign in failed:', error);
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Sign in failed',
      }));
      setNeedsPasswordChange(false);
      setCurrentUsername(null);
      throw error;
    }
  };

  /**
   * Sign out current user
   */
  const handleSignOut = async (): Promise<void> => {
    try {
      // Ensure Amplify is configured before any operations
      configureAmplify();
      
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Check if we're in local development mode
      const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      if (isLocalDev) {
        // Mock sign-out for local development
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
    } catch (error) {
      console.error('Sign out failed:', error);
      // Clear timer even if sign out fails
      clearLogoutTimer();
      
      setAuthState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Sign out failed',
      }));
      throw error;
    }
  };

  /**
   * Handle successful password change
   */
  const handlePasswordChanged = async (): Promise<void> => {
    setNeedsPasswordChange(false);
    setCurrentUsername(null);
    await checkAuth();
  };

  const value: AuthContextType = {
    ...authState,
    signIn: handleSignIn,
    signOut: handleSignOut,
    checkAuth,
    needsPasswordChange,
    currentUsername,
    handlePasswordChanged,
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
