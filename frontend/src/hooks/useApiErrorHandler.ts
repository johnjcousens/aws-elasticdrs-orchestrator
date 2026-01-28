/**
 * API Error Handler Hook
 * 
 * Provides centralized error handling for API calls, including
 * authentication error handling that preserves React Router state.
 */

import { useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const useApiErrorHandler = () => {
  const { handleAuthError } = useAuth();

  const handleError = useCallback(async (error: Error) => {
    // Handle authentication errors
    if (error.message.includes('Authentication required') || 
        error.message.includes('token expired') ||
        error.message.includes('Unauthorized')) {
      await handleAuthError(error);
      return;
    }

    // For other errors, just re-throw to let components handle them
    throw error;
  }, [handleAuthError]);

  return { handleError };
};