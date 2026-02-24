/**
 * Unit tests for useLaunchConfigStatus hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useLaunchConfigStatus } from '../useLaunchConfigStatus';
import * as api from '../../services/api';
import type { LaunchConfigStatus } from '../../types';

vi.mock('../../services/api');

describe('useLaunchConfigStatus', () => {
  const mockGetLaunchConfigStatus = vi.mocked(api.getLaunchConfigStatus);

  const createMockStatus = (overrides: Partial<LaunchConfigStatus> = {}): LaunchConfigStatus => ({
    status: 'ready',
    syncJobId: null,
    totalServers: 10,
    completedServers: 10,
    failedServers: 0,
    startTime: null,
    completionTime: Date.now(),
    servers: [],
    ...overrides,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Polling Behavior', () => {
    it('should start polling when startPolling is called', async () => {
      const mockStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 2000,
        })
      );

      expect(result.current.isPolling).toBe(false);

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });

      expect(mockGetLaunchConfigStatus).toHaveBeenCalledWith('pg-123');
    });

    it('should stop polling when stopPolling is called', async () => {
      const mockStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 2000,
        })
      );

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });

      result.current.stopPolling();

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false);
      });
    });

    it('should auto-stop polling when status reaches terminal state', async () => {
      const syncingStatus = createMockStatus({ status: 'syncing' });
      const readyStatus = createMockStatus({ status: 'ready' });

      mockGetLaunchConfigStatus
        .mockResolvedValueOnce(syncingStatus)
        .mockResolvedValueOnce(readyStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 100, // Use shorter interval for testing
        })
      );

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('syncing');
      });

      // Wait for next poll
      await waitFor(() => {
        expect(result.current.status?.status).toBe('ready');
        expect(result.current.isPolling).toBe(false);
      }, { timeout: 500 });
    });

    it('should stop polling for partial status', async () => {
      const partialStatus = createMockStatus({ status: 'partial', failedServers: 2 });
      mockGetLaunchConfigStatus.mockResolvedValue(partialStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 2000,
        })
      );

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('partial');
        expect(result.current.isPolling).toBe(false);
      });
    });

    it('should stop polling for failed status', async () => {
      const failedStatus = createMockStatus({ status: 'failed' });
      mockGetLaunchConfigStatus.mockResolvedValue(failedStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 2000,
        })
      );

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('failed');
        expect(result.current.isPolling).toBe(false);
      });
    });
  });

  describe('Polling Interval', () => {
    it('should poll at the specified interval', async () => {
      const mockStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 100, // Use shorter interval for testing
        })
      );

      result.current.startPolling();

      // First call happens immediately
      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).toHaveBeenCalledTimes(1);
      });

      // Wait for second poll
      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).toHaveBeenCalledTimes(2);
      }, { timeout: 300 });

      // Wait for third poll
      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).toHaveBeenCalledTimes(3);
      }, { timeout: 300 });
    });

    it('should respect custom poll interval', async () => {
      const mockStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 150, // Use shorter interval for testing
        })
      );

      result.current.startPolling();

      // First call happens immediately
      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).toHaveBeenCalledTimes(1);
      });

      // Wait for second poll
      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).toHaveBeenCalledTimes(2);
      }, { timeout: 400 });
    });
  });

  describe('Auto-start Polling', () => {
    it('should auto-start polling when enabled and status is pending', async () => {
      const pendingStatus = createMockStatus({ status: 'pending' });
      mockGetLaunchConfigStatus.mockResolvedValue(pendingStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          enabled: true,
        })
      );

      // Set initial status
      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('pending');
      });

      // Should auto-start polling
      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });
    });

    it('should auto-start polling when enabled and status is syncing', async () => {
      const syncingStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(syncingStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          enabled: true,
        })
      );

      // Set initial status
      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('syncing');
      });

      // Should auto-start polling
      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });
    });

    it('should not auto-start polling when enabled is false', async () => {
      const syncingStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(syncingStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          enabled: false,
        })
      );

      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('syncing');
      });

      // Should not auto-start
      expect(result.current.isPolling).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should set error state when API call fails', async () => {
      mockGetLaunchConfigStatus.mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
        })
      );

      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });
    });

    it('should clear error on successful fetch', async () => {
      const mockStatus = createMockStatus({ status: 'ready' });
      mockGetLaunchConfigStatus
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
        })
      );

      // First call fails
      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.error).toBe('Network error');
      });

      // Second call succeeds
      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.error).toBeNull();
        expect(result.current.status?.status).toBe('ready');
      });
    });
  });

  describe('Cleanup', () => {
    it('should stop polling on unmount', async () => {
      const mockStatus = createMockStatus({ status: 'syncing' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result, unmount } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
          pollInterval: 100,
        })
      );

      result.current.startPolling();

      await waitFor(() => {
        expect(result.current.isPolling).toBe(true);
      });

      const callCountBeforeUnmount = mockGetLaunchConfigStatus.mock.calls.length;

      unmount();

      // Wait a bit to ensure no more calls are made after unmount
      await new Promise(resolve => setTimeout(resolve, 250));

      // Should not have made any additional calls after unmount
      expect(mockGetLaunchConfigStatus.mock.calls.length).toBe(callCountBeforeUnmount);
    });
  });

  describe('Manual Fetch', () => {
    it('should fetch status when fetchStatus is called', async () => {
      const mockStatus = createMockStatus({ status: 'ready' });
      mockGetLaunchConfigStatus.mockResolvedValue(mockStatus);

      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: 'pg-123',
        })
      );

      expect(result.current.status).toBeNull();

      result.current.fetchStatus();

      await waitFor(() => {
        expect(result.current.status?.status).toBe('ready');
      });

      expect(mockGetLaunchConfigStatus).toHaveBeenCalledWith('pg-123');
    });

    it('should not fetch when protectionGroupId is empty', async () => {
      const { result } = renderHook(() =>
        useLaunchConfigStatus({
          protectionGroupId: '',
        })
      );

      result.current.fetchStatus();

      await waitFor(() => {
        expect(mockGetLaunchConfigStatus).not.toHaveBeenCalled();
      });
    });
  });
});
