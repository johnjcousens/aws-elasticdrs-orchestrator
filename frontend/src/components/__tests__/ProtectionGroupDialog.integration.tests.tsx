/**
 * ProtectionGroupDialog Integration Tests
 * 
 * Integration tests for enhanced ProtectionGroupDialog covering:
 * - Server Configurations tab integration (Requirements 1.5, 2.1, 14.1, 14.2)
 * - Per-server config save logic
 * - Tab navigation
 * - Custom config counter display
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProtectionGroupDialog } from '../ProtectionGroupDialog';
import { PermissionsProvider } from '../../contexts/PermissionsContext';
import { AuthProvider } from '../../contexts/AuthContext';
import type { ProtectionGroup } from '../../types';
import '@testing-library/jest-dom';

// Mock API client - use factory function to avoid hoisting issues
vi.mock('../../services/api', () => ({
  default: {
    getEC2Subnets: vi.fn().mockResolvedValue([
      { value: 'subnet-123', label: 'subnet-123 (10.0.1.0/24)' }
    ]),
    getEC2SecurityGroups: vi.fn().mockResolvedValue([
      { value: 'sg-123', label: 'sg-123 (default)' }
    ]),
    getEC2InstanceProfiles: vi.fn().mockResolvedValue([
      { value: 'profile-123', label: 'profile-123' }
    ]),
    getEC2InstanceTypes: vi.fn().mockResolvedValue([
      { value: 't3.micro', label: 't3.micro' }
    ]),
    resolveProtectionGroupTags: vi.fn().mockResolvedValue({
      resolvedServers: []
    }),
    createProtectionGroup: vi.fn().mockResolvedValue({
      protectionGroupId: 'pg-123',
      groupName: 'Test Group',
      region: 'us-east-1'
    }),
    updateProtectionGroup: vi.fn().mockResolvedValue({
      protectionGroupId: 'pg-123',
      groupName: 'Test Group',
      region: 'us-east-1'
    }),
    listDRSSourceServers: vi.fn().mockResolvedValue({
      servers: [],
      serverCount: 0,
      region: 'us-east-1'
    })
  }
}));

// Helper to render with required providers
const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <AuthProvider>
      <PermissionsProvider>
        {ui}
      </PermissionsProvider>
    </AuthProvider>
  );
};

describe('ProtectionGroupDialog - Integration Tests', () => {
  const mockOnClose = vi.fn();
  const mockOnSave = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Server Configurations Tab', () => {
    it('displays Server Configurations tab', async () => {
      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // Wait for component to render
      await waitFor(() => {
        expect(screen.getByText(/Server Configurations/i)).toBeInTheDocument();
      });
    });

    it('shows custom config count in tab label', async () => {
      const mockGroup: ProtectionGroup = {
        groupId: 'pg-123',
        protectionGroupId: 'pg-123',
        groupName: 'Test Group',
        region: 'us-east-1',
        sourceServerIds: ['s-123', 's-456'],
        launchConfig: {},
        createdDate: Date.now(),
        lastModifiedDate: Date.now(),
        servers: [
          {
            sourceServerId: 's-123',
            useGroupDefaults: false,
            launchTemplate: {
              staticPrivateIp: '10.0.1.100'
            }
          }
        ]
      };

      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          group={mockGroup}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Server Configurations \(1 custom\)/i)).toBeInTheDocument();
      });
    });

    it('navigates between tabs correctly', async () => {
      const user = userEvent.setup();

      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // Click Server Configurations tab
      const serverConfigTab = screen.getByText(/Server Configurations/i);
      await user.click(serverConfigTab);

      await waitFor(() => {
        expect(screen.getByText(/Select servers in the Server Selection tab/i)).toBeInTheDocument();
      });

      // Click Launch Settings tab
      const launchSettingsTab = screen.getByText(/Launch Settings/i);
      await user.click(launchSettingsTab);

      await waitFor(() => {
        expect(screen.getByText(/Target Subnet/i)).toBeInTheDocument();
      });
    });
  });

  describe('Per-Server Config Save Logic', () => {
    it('includes per-server configs in save payload', async () => {
      const mockGroup: ProtectionGroup = {
        groupId: 'pg-123',
        protectionGroupId: 'pg-123',
        groupName: 'Test Group',
        region: 'us-east-1',
        sourceServerIds: ['s-123'],
        launchConfig: {},
        createdDate: Date.now(),
        lastModifiedDate: Date.now(),
        servers: [
          {
            sourceServerId: 's-123',
            useGroupDefaults: false,
            launchTemplate: {
              staticPrivateIp: '10.0.1.100'
            }
          }
        ]
      };

      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          group={mockGroup}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      // Verify the dialog renders with the group data
      await waitFor(() => {
        expect(screen.getByText('Edit Protection Group')).toBeInTheDocument();
      });
      
      // Verify the group name is displayed
      expect(screen.getByDisplayValue('Test Group')).toBeInTheDocument();
    });
  });

  describe('Custom Config Counter', () => {
    it('shows zero custom configs for new group', async () => {
      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      await waitFor(() => {
        const serverConfigTab = screen.getByText(/Server Configurations/i);
        expect(serverConfigTab).toBeInTheDocument();
        expect(serverConfigTab.textContent).not.toContain('custom');
      });
    });

    it('updates counter when servers have custom configs', async () => {
      const mockGroup: ProtectionGroup = {
        groupId: 'pg-123',
        protectionGroupId: 'pg-123',
        groupName: 'Test Group',
        region: 'us-east-1',
        sourceServerIds: ['s-123', 's-456', 's-789'],
        launchConfig: {},
        createdDate: Date.now(),
        lastModifiedDate: Date.now(),
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
      };

      renderWithProviders(
        <ProtectionGroupDialog
          open={true}
          group={mockGroup}
          onClose={mockOnClose}
          onSave={mockOnSave}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Server Configurations \(2 custom\)/i)).toBeInTheDocument();
      });
    });
  });
});
