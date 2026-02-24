/**
 * Launch Configuration Status Polling Hook
 * 
 * Polls the backend for launch configuration sync status and provides
 * real-time updates during async configuration application.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getLaunchConfigStatus } from '../services/api';
import type { LaunchConfigStatus } from '../types';

interface UseLaunchConfigStatusOptions {
  protectionGroupId: string;
  pollInterval?: number;
  enabled?: boolean;
}

interface UseLaunchConfigStatusReturn {
  status: LaunchConfigStatus | null;
  isPolling: boolean;
  error: string | null;
  startPolling: () => void;
  stopPolling: () => void;
  fetchStatus: () => Promise<void>;
}

const TERMINAL_STATUSES = ['ready', 'partial', 'failed'];
const ACTIVE_STATUSES = ['pending', 'syncing'];

export function useLaunchConfigStatus({
  protectionGroupId,
  pollInterval = 2000,
  enabled = false,
}: UseLaunchConfigStatusOptions): UseLaunchConfigStatusReturn {
  const [status, setStatus] = useState<LaunchConfigStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isMountedRef = useRef(true);
  const autoStartedRef = useRef(false);

  // Fetch status from API
  const fetchStatus = useCallback(async () => {
    if (!protectionGroupId) {
      return;
    }

    try {
      const result = await getLaunchConfigStatus(protectionGroupId);
      
      if (isMountedRef.current) {
        setStatus(result);
        setError(null);

        // Auto-stop polling if reached terminal status
        if (TERMINAL_STATUSES.includes(result.status)) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setIsPolling(false);
        }
      }
    } catch (err) {
      if (isMountedRef.current) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch status';
        setError(errorMessage);
        console.error('Error fetching launch config status:', err);
      }
    }
  }, [protectionGroupId]);

  // Start polling
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      return; // Already polling
    }

    setIsPolling(true);
    setError(null);

    // Fetch immediately
    fetchStatus();

    // Set up interval
    pollIntervalRef.current = setInterval(() => {
      fetchStatus();
    }, pollInterval);
  }, [fetchStatus, pollInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
    autoStartedRef.current = false;
  }, []);

  // Auto-start polling when enabled and status is active
  useEffect(() => {
    if (enabled && status && ACTIVE_STATUSES.includes(status.status) && !autoStartedRef.current) {
      autoStartedRef.current = true;
      startPolling();
    }
  }, [enabled, status, startPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [stopPolling]);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling,
    fetchStatus,
  };
}
