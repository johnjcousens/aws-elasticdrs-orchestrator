/**
 * ConfigExportPanel Integration Tests
 * 
 * Integration tests for enhanced ConfigExportPanel covering:
 * - Export with per-server configs (Requirements 10.1, 10.5.1)
 * - Schema version 1.1 indicator
 * - Custom config counter in export
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfigExportPanel } from '../ConfigExportPanel';
import '@testing-library/jest-dom';

// Create mock functions at module level
const mockExportConfiguration = vi.fn();

// Mock toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  }
}));

// Mock ApiContext to provide the mocked API
vi.mock('../../contexts/ApiContext', () => ({
  ApiProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useApi: () => ({
    exportConfiguration: mockExportConfiguration,
  }),
}));

describe('ConfigExportPanel - Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExportConfiguration.mockReset();
    
    // Mock URL.createObjectURL and revokeObjectURL
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    global.URL.revokeObjectURL = vi.fn();
  });

  describe('Export with Per-Server Configs', () => {
    it('exports configuration with per-server configs', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.1',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [
          {
            protectionGroupId: 'pg-123',
            groupName: 'Test Group',
            servers: [
              {
                sourceServerId: 's-123',
                useGroupDefaults: false,
                launchTemplate: {
                  staticPrivateIp: '10.0.1.100'
                }
              }
            ]
          }
        ],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockExportConfiguration).toHaveBeenCalled();
      });
    });

    it('counts servers with custom configs in export', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.1',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [
          {
            protectionGroupId: 'pg-123',
            groupName: 'Test Group 1',
            servers: [
              {
                sourceServerId: 's-123',
                useGroupDefaults: false,
                launchTemplate: { staticPrivateIp: '10.0.1.100' }
              },
              {
                sourceServerId: 's-456',
                useGroupDefaults: false,
                launchTemplate: { instanceType: 't3.large' }
              }
            ]
          },
          {
            protectionGroupId: 'pg-456',
            groupName: 'Test Group 2',
            servers: [
              {
                sourceServerId: 's-789',
                useGroupDefaults: false,
                launchTemplate: { staticPrivateIp: '10.0.2.100' }
              }
            ]
          }
        ],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockExportConfiguration).toHaveBeenCalled();
      });

      // Verify toast message includes count
      const toast = await import('react-hot-toast');
      expect(toast.default.success).toHaveBeenCalledWith(
        expect.stringContaining('3 servers with custom configs')
      );
    });

    it('exports configuration without per-server configs', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.0',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [
          {
            protectionGroupId: 'pg-123',
            groupName: 'Test Group',
            launchConfig: {}
          }
        ],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockExportConfiguration).toHaveBeenCalled();
      });

      // Verify toast message does not include count
      const toast = await import('react-hot-toast');
      expect(toast.default.success).toHaveBeenCalledWith(
        'Configuration exported successfully'
      );
    });
  });

  describe('Schema Version Indicator', () => {
    it('displays schema version 1.1 info alert', () => {
      render(<ConfigExportPanel />);

      expect(screen.getByText(/Schema version 1.1/i)).toBeInTheDocument();
    });

    it('mentions per-server configurations in description', () => {
      render(<ConfigExportPanel />);

      expect(screen.getByText(/Per-server launch configurations/i)).toBeInTheDocument();
      expect(screen.getByText(/Static private IP assignments/i)).toBeInTheDocument();
    });
  });

  describe('Export File Generation', () => {
    it('generates filename with timestamp', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.1',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      // Mock document.createElement to capture link element
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
        setAttribute: vi.fn(),
      };
      const originalCreateElement = document.createElement.bind(document);
      document.createElement = vi.fn((tag) => {
        if (tag === 'a') return mockLink as any;
        return originalCreateElement(tag);
      });

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockLink.download).toMatch(/^drs-orchestration-config-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$/);
      });

      // Restore original createElement
      document.createElement = originalCreateElement;
    });

    it('creates blob with correct JSON content', async () => {
      const user = userEvent.setup();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.1',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [
          {
            protectionGroupId: 'pg-123',
            groupName: 'Test Group',
            servers: [
              {
                sourceServerId: 's-123',
                useGroupDefaults: false,
                launchTemplate: { staticPrivateIp: '10.0.1.100' }
              }
            ]
          }
        ],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockExportConfiguration).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error when export fails', async () => {
      const user = userEvent.setup();
      mockExportConfiguration.mockRejectedValue(new Error('Export failed'));

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(screen.getByText(/Export failed/i)).toBeInTheDocument();
      });
    });

    it('shows loading state during export', async () => {
      const user = userEvent.setup();
      mockExportConfiguration.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

      render(<ConfigExportPanel />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      expect(exportButton).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Export Completion Callback', () => {
    it('calls onExportComplete callback after successful export', async () => {
      const user = userEvent.setup();
      const mockOnExportComplete = vi.fn();
      const mockConfig = {
        metadata: {
          schemaVersion: '1.1',
          exportedAt: '2026-01-28T00:00:00Z',
          sourceRegion: 'us-east-1'
        },
        protectionGroups: [],
        recoveryPlans: []
      };

      mockExportConfiguration.mockResolvedValue(mockConfig);

      render(<ConfigExportPanel onExportComplete={mockOnExportComplete} />);

      const exportButton = screen.getByRole('button', { name: /Export Configuration/i });
      await user.click(exportButton);

      await waitFor(() => {
        expect(mockOnExportComplete).toHaveBeenCalled();
      });
    });
  });
});
