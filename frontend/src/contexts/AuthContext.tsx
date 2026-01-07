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
import { registerActivityRecorder, unregisterActivityRecorder } from '../utils/activityTracker';

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
          userPoolId: 'us-east-1_7ClH0e1NS',
          userPoolClientId: '6fepnj59rp7qup2k3n6uda5p19',
          loginWith: {
            email: true
          }
        }
      },
      API: {
        REST: {
          DRSOrchestration: {
            endpoint: 'https://bu05wxn2ci.execute-api.us-east-1.amazonaws.com/dev',
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
  recordActivity: () => void;
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

  // Inactivity timeout (4 hours) - only logout after extended inactivity
  const INACTIVITY_TIMEOUT = 4 * 60 * 60 * 1000; // 4 hours in milliseconds
  
  // Token refresh timer (50 minutes - before 60 minute expiry)
  const TOKEN_REFRESH_TIME = 50 * 60 * 1000; // 50 minutes in milliseconds
  
  // Use refs to avoid dependency cycles that cause infinite re-renders
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);
  const tokenRefreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  const authCheckInProgressRef = useRef(false);
  const hasCheckedAuthRef = useRef(false);
  const lastActivityRef = useRef<number>(Date.now());

  /**
   * Clear inactivity timer
   */
  const clearInactivityTimer = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
  }, []);

  /**
   * Record user activity and reset inactivity timer
   */
  const recordActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    
    // Only restart inactivity timer if user is authenticated
    if (authState.isAuthenticated) {
      startInactivityTimer();
    }
  }, [authState.isAuthenticated]);

  /**
   * Start inactivity timer - logout after extended inactivity
   */
  const startInactivityTimer = useCallback(() => {
    clearInactivityTimer();
    
    inactivityTimerRef.current = setTimeout(() => {
      console.log('🕐 User inactive for 4 hours - signing out for security');
      // Sign out due to inactivity
      signOut().then(() => {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
      }).catch(console.error);
    }, INACTIVITY_TIMEOUT);
  }, [clearInactivityTimer, INACTIVITY_TIMEOUT]);

  /**
   * Clear token refresh timer
   */
  const clearTokenRefreshTimer = useCallback(() => {
    if (tokenRefreshTimerRef.current) {
      clearTimeout(tokenRefreshTimerRef.current);
      tokenRefreshTimerRef.current = null;
    }
  }, []);

  /**
   * Refresh authentication tokens
   */
  const refreshTokens = useCallback(async () => {
    try {
      console.log('🔄 Refreshing authentication tokens...');
      
      // Get fresh session which will automatically refresh tokens if needed
      const session = await fetchAuthSession({ forceRefresh: true });
      
      if (session.tokens) {
        console.log('✅ Tokens refreshed successfully');
        
        // Restart both timers with fresh tokens
        startTokenRefreshTimer();
        startInactivityTimer();
      } else {
        console.warn('⚠️ Token refresh failed - no tokens in session');
        // Sign out if token refresh fails - will be defined later
        handleSignOut();
      }
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      // Sign out if token refresh fails - will be defined later
      handleSignOut();
    }
  }, [startTokenRefreshTimer, startInactivityTimer]);

  /**
   * Start token refresh timer
   */
  const startTokenRefreshTimer = useCallback(() => {
    clearTokenRefreshTimer();
    
    tokenRefreshTimerRef.current = setTimeout(() => {
      refreshTokens();
    }, TOKEN_REFRESH_TIME);
  }, [clearTokenRefreshTimer, refreshTokens, TOKEN_REFRESH_TIME]);

  /**
   * Start both authentication timers (inactivity and token refresh)
   */
  const startAuthTimers = useCallback(() => {
    startInactivityTimer();
    startTokenRefreshTimer();
  }, [startInactivityTimer, startTokenRefreshTimer]);

  /**
   * Clear both authentication timers
   */
  const clearAuthTimers = useCallback(() => {
    clearInactivityTimer();
    clearTokenRefreshTimer();
  }, [clearInactivityTimer, clearTokenRefreshTimer]);

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
        
        // Start both authentication timers
        startAuthTimers();
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
      // Clear both authentication timers on auth failure
      clearAuthTimers();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    } finally {
      authCheckInProgressRef.current = false;
    }
  }, [clearAuthTimers, startAuthTimers]);

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
   * Set up global activity listeners to track user interactions
   */
  useEffect(() => {
    // Activity events to track
    const activityEvents = [
      'mousedown',
      'mousemove', 
      'keypress',
      'scroll',
      'touchstart',
      'click'
    ];

    // Throttle activity recording to avoid excessive calls
    let activityThrottle: NodeJS.Timeout | null = null;
    
    const handleActivity = () => {
      if (activityThrottle) return;
      
      activityThrottle = setTimeout(() => {
        recordActivity();
        activityThrottle = null;
      }, 30000); // Throttle to once per 30 seconds
    };

    // Add event listeners
    activityEvents.forEach(event => {
      document.addEventListener(event, handleActivity, true);
    });

    // Cleanup event listeners
    return () => {
      if (activityThrottle) {
        clearTimeout(activityThrottle);
      }
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity, true);
      });
    };
  }, [recordActivity]);

  /**
   * Clean up timers on unmount
   */
  useEffect(() => {
    // Register the activity recorder
    registerActivityRecorder(recordActivity);
    
    return () => {
      // Cleanup timers
      if (inactivityTimerRef.current) {
        clearTimeout(inactivityTimerRef.current);
      }
      if (tokenRefreshTimerRef.current) {
        clearTimeout(tokenRefreshTimerRef.current);
      }
      
      // Unregister the activity recorder
      unregisterActivityRecorder();
    };
  }, [recordActivity]);

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
        clearAuthTimers();
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
        return;
      }

      await signOut();

      // Clear both authentication timers
      clearAuthTimers();
      
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    } catch (error) {
      console.error('Sign out failed:', error);
      // Clear timers even if sign out fails
      clearAuthTimers();
      
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
    recordActivity,
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
