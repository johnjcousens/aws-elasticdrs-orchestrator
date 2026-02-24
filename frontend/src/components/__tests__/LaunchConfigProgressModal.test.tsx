/**
 * Unit tests for LaunchConfigProgressModal component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LaunchConfigProgressModal } from '../LaunchConfigProgressModal';
import type { LaunchConfigStatus } from '../../types';

describe('LaunchConfigProgressModal', () => {
  const mockOnDismiss = vi.fn();
  const mockOnRetry = vi.fn();

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

  describe('Progress Bar Display', () => {
    it('should show progress bar during syncing', () => {
      const status = createMockStatus({
        status: 'syncing',
        completedServers: 5,
        totalServers: 10,
        startTime: Date.now() - 5000,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
      expect(screen.getByText(/5 of 10 servers completed/i)).toBeInTheDocument();
    });

    it('should not show progress bar when status is ready', () => {
      const status = createMockStatus({
        status: 'ready',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    it('should show estimated time remaining during syncing', () => {
      const status = createMockStatus({
        status: 'syncing',
        completedServers: 5,
        totalServers: 10,
        startTime: Date.now() - 10000, // 10 seconds ago
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      // Should show some time estimate (either seconds or minutes)
      const timeText = screen.getByText(/~\d+[sm] remaining/i);
      expect(timeText).toBeInTheDocument();
    });
  });

  describe('Retry Button Visibility', () => {
    it('should show retry button for partial status', () => {
      const status = createMockStatus({
        status: 'partial',
        completedServers: 8,
        failedServers: 2,
        servers: [
          { sourceServerId: 's-1', status: 'failed', error: 'Error 1' },
          { sourceServerId: 's-2', status: 'failed', error: 'Error 2' },
        ],
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByRole('button', { name: /Retry Failed/i })).toBeInTheDocument();
    });

    it('should show retry button for failed status', () => {
      const status = createMockStatus({
        status: 'failed',
        completedServers: 0,
        failedServers: 10,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.getByRole('button', { name: /Retry Failed/i })).toBeInTheDocument();
    });

    it('should not show retry button for ready status', () => {
      const status = createMockStatus({
        status: 'ready',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
          onRetry={mockOnRetry}
        />
      );

      expect(screen.queryByRole('button', { name: /Retry Failed/i })).not.toBeInTheDocument();
    });

    it('should not show retry button when onRetry is not provided', () => {
      const status = createMockStatus({
        status: 'partial',
        failedServers: 2,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.queryByRole('button', { name: /Retry Failed/i })).not.toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', async () => {
      const user = userEvent.setup();
      const status = createMockStatus({
        status: 'partial',
        failedServers: 2,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
          onRetry={mockOnRetry}
        />
      );

      const retryButton = screen.getByRole('button', { name: /Retry Failed/i });
      await user.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Dismiss Prevention', () => {
    it('should disable close button during pending', () => {
      const status = createMockStatus({
        status: 'pending',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole('button', { name: /Syncing.../i });
      expect(closeButton).toBeDisabled();
    });

    it('should disable close button during syncing', () => {
      const status = createMockStatus({
        status: 'syncing',
        completedServers: 5,
        totalServers: 10,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole('button', { name: /Syncing.../i });
      expect(closeButton).toBeDisabled();
    });

    it('should enable close button when status is ready', () => {
      const status = createMockStatus({
        status: 'ready',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole('button', { name: /Close/i });
      expect(closeButton).not.toBeDisabled();
    });

    it('should enable close button when status is partial', () => {
      const status = createMockStatus({
        status: 'partial',
        failedServers: 2,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole('button', { name: /Close/i });
      expect(closeButton).not.toBeDisabled();
    });

    it('should enable close button when status is failed', () => {
      const status = createMockStatus({
        status: 'failed',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      const closeButton = screen.getByRole('button', { name: /Close/i });
      expect(closeButton).not.toBeDisabled();
    });
  });

  describe('Status Indicators', () => {
    it('should show pending status indicator', () => {
      const status = createMockStatus({
        status: 'pending',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/Preparing to sync configurations/i)).toBeInTheDocument();
    });

    it('should show syncing status indicator', () => {
      const status = createMockStatus({
        status: 'syncing',
        completedServers: 5,
        totalServers: 10,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/Syncing configurations to DRS and EC2/i)).toBeInTheDocument();
    });

    it('should show success status indicator', () => {
      const status = createMockStatus({
        status: 'ready',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/All configurations applied successfully/i)).toBeInTheDocument();
    });

    it('should show warning status indicator for partial', () => {
      const status = createMockStatus({
        status: 'partial',
        failedServers: 2,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/Some configurations failed to apply/i)).toBeInTheDocument();
    });

    it('should show error status indicator for failed', () => {
      const status = createMockStatus({
        status: 'failed',
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      // Use getAllByText since both StatusIndicator and Alert header show this text
      const failedTexts = screen.getAllByText(/Configuration sync failed/i);
      expect(failedTexts.length).toBeGreaterThan(0);
    });
  });

  describe('Error Details', () => {
    it('should show failed server details for partial status', () => {
      const status = createMockStatus({
        status: 'partial',
        completedServers: 8,
        failedServers: 2,
        servers: [
          { sourceServerId: 's-001', status: 'failed', error: 'Network timeout' },
          { sourceServerId: 's-002', status: 'failed', error: 'Permission denied' },
        ],
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/s-001: Network timeout/i)).toBeInTheDocument();
      expect(screen.getByText(/s-002: Permission denied/i)).toBeInTheDocument();
    });

    it('should limit failed server list to 5 items', () => {
      const servers = Array.from({ length: 10 }, (_, i) => ({
        sourceServerId: `s-${String(i).padStart(3, '0')}`,
        status: 'failed' as const,
        error: `Error ${i}`,
      }));

      const status = createMockStatus({
        status: 'failed',
        failedServers: 10,
        servers,
      });

      render(
        <LaunchConfigProgressModal
          visible={true}
          status={status}
          onDismiss={mockOnDismiss}
        />
      );

      expect(screen.getByText(/...and 5 more/i)).toBeInTheDocument();
    });
  });
});
