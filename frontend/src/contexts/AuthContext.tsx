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
} from 'aws-amplify/auth';
import type { SignInInput, SignInOutput } from 'aws-amplify/auth';
import { awsConfig } from '../aws-config';
import type { User, AuthState } from '../types';

// Configure Amplify
Amplify.configure(awsConfig);

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

  /**
   * Check if user is authenticated on mount
   */
  useEffect(() => {
    checkAuth();
  }, []);

  /**
   * Check current authentication status
   */
  const checkAuth = async (): Promise<void> => {
    try {
      setAuthState((prev) => ({ ...prev, loading: true, error: undefined }));

      // Get current authenticated user
      const user = await getCurrentUser();
      
      // Get auth session to verify token is valid
      const session = await fetchAuthSession();
      
      if (user && session.tokens) {
        setAuthState({
          isAuthenticated: true,
          user: {
            username: user.username,
            email: user.signInDetails?.loginId,
          },
          loading: false,
          error: undefined,
        });
      } else {
        setAuthState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: undefined,
        });
      }
    } catch (error) {
      console.error('Auth check failed:', error);
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

      await signOut();

      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: undefined,
      });
    } catch (error: any) {
      console.error('Sign out failed:', error);
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
