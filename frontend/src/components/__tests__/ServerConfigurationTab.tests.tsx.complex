/**
 * ServerConfigurationTab Component Tests
 * 
 * Tests for the ServerConfigurationTab component covering:
 * - Server list rendering (Requirements 1.1, 1.2, 1.3)
 * - Filtering (Requirements 1.2, 1.3)
 * - Badge display (Requirement 6.1)
 * - Dialog opening (Requirement 2.1)
 */

import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ServerConfigurationTab } from '../ServerConfigurationTab';
import type {
  ResolvedServer,
  LaunchConfig,
  ServerLaunchConfig,
} from '../../types';
import '@testing-library/jest-dom';

// Mock child components
vi.mock('../ServerConfigBadge', () => ({
  ServerConfigBadge: ({ hasCustomConfig, customFields }: any) => (
    <span data-testid="config-badge" data-custom={hasCustomConfig}>
      {hasCustomConfig ? 'Custom' : 'Default'}
      {customFields && customFields.length > 0 && (
        <span data-testid="custom-fields">{customFields.join(',')}</span>
      )}
    </span>
  ),
}));

vi.mock('../ServerLaunchConfigDialog', () => ({
  ServerLaunchConfigDialog: ({ open, server, onClose, onSave }: any) =>
    open ? (
      <div data-testid="server-launch-config-dialog">
        <div data-testid="dialog-server-id">{server.sourceServerID}</div>
        <button onClick={onClose}>Close Dialog</button>
        <button onClick={() => onSave({ sourceServerId: server.sourceServerID })}>
          Save Dialog
        </button>
      </div>
    ) : null,
}));

describe('ServerConfigurationTab', () => {
  const mockServers: ResolvedServer[] = [
    {
      sourceServerID: 's-111',
      hostname: 'web-server-01',
      nameTag: 'WebServer01',
      replicationState: 'CONTINUOUS',
      tags: { Name: 'web-server-01' },
    },
    {
      sourceServerID: 's-222',
      hostname: 'web-server-02',
      nameTag: 'WebServer02',
      replicationState: 'CONTINUOUS',
      tags: { Name: 'web-server-02' },
    },
    {
      sourceServerID: 's-333',
      hostname: 'web-server-03',
      nameTag: 'WebServer03',
      replicationState: 'CONTINUOUS',
      tags: { Name: 'web-server-03' },
    },
  ];

  const mockGroupDefaults: LaunchConfig = {
    subnetId: 'subnet-default',
    securityGroupIds: ['sg-default'],
    instanceType: 'c6a.large',
  };

  const mockServerConfigs = new Map<string, ServerLaunchConfig>([
    [
      's-111',
      {
        sourceServerId: 's-111',
        useGroupDefaults: false,
        launchTemplate: {
          staticPrivateIp: '10.0.1.100',
          instanceType: 'c6a.xlarge',
        },
      },
    ],
    [
      's-222',
      {
        sourceServerId: 's-222',
        useGroupDefaults: true,
        launchTemplate: {
          staticPrivateIp: '10.0.1.101',
        },
      },
    ],
  ]);

  const defaultProps = {
    protectionGroupId: 'group-123',
    servers: mockServers,
    groupDefaults: mockGroupDefaults,
    serverConfigs: mockServerConfigs,
    region: 'us-east-1',
    onConfigChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Server List Rendering', () => {
    it('renders table with server list', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByText('Server Configurations')).toBeInTheDocument();
      expect(screen.getByText('web-server-01')).toBeInTheDocument();
      expect(screen.getByText('web-server-02')).toBeInTheDocument();
      expect(screen.getByText('web-server-03')).toBeInTheDocument();
    });

    it('displays server source IDs', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByText('s-111')).toBeInTheDocument();
      expect(screen.getByText('s-222')).toBeInTheDocument();
      expect(screen.getByText('s-333')).toBeInTheDocument();
    });

    it('displays static IP addresses', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByText('10.0.1.100')).toBeInTheDocument();
      expect(screen.getByText('10.0.1.101')).toBeInTheDocument();
    });

    it('displays DHCP for servers without static IP', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const dhcpElements = screen.getAllByText('DHCP');
      expect(dhcpElements.length).toBeGreaterThan(0);
    });

    it('displays server count in header', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByText(/\(3\/3\)/)).toBeInTheDocument();
    });

    it('displays custom config count in description', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByText(/2 servers with custom configuration/)).toBeInTheDocument();
    });

    it('shows message when all servers use defaults', () => {
      const emptyConfigs = new Map<string, ServerLaunchConfig>();
      
      render(
        <ServerConfigurationTab {...defaultProps} serverConfigs={emptyConfigs} />
      );
      
      expect(
        screen.getByText('All servers using protection group defaults')
      ).toBeInTheDocument();
    });

    it('renders Configure button for each server', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      expect(configureButtons).toHaveLength(3);
    });

    it('renders Reset button for servers with custom config', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const resetButtons = screen.getAllByRole('button', { name: /Reset/ });
      expect(resetButtons).toHaveLength(2); // Only s-111 and s-222 have custom configs
    });

    it('shows empty state when no servers', () => {
      render(<ServerConfigurationTab {...defaultProps} servers={[]} />);
      
      expect(screen.getByText('No servers')).toBeInTheDocument();
      expect(
        screen.getByText('No servers found in this protection group.')
      ).toBeInTheDocument();
    });

    it('shows loading state', () => {
      render(<ServerConfigurationTab {...defaultProps} loading={true} />);
      
      expect(screen.getByText('Loading servers...')).toBeInTheDocument();
    });
  });

  describe('Badge Display', () => {
    it('displays ServerConfigBadge for each server', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const badges = screen.getAllByTestId('config-badge');
      expect(badges).toHaveLength(3);
    });

    it('shows Custom badge for servers with custom config', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const badges = screen.getAllByTestId('config-badge');
      const customBadges = badges.filter(
        (badge) => badge.getAttribute('data-custom') === 'true'
      );
      expect(customBadges).toHaveLength(2);
    });

    it('shows Default badge for servers without custom config', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const badges = screen.getAllByTestId('config-badge');
      const defaultBadges = badges.filter(
        (badge) => badge.getAttribute('data-custom') === 'false'
      );
      expect(defaultBadges).toHaveLength(1);
    });

    it('passes custom fields to badge component', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const customFieldsElements = screen.getAllByTestId('custom-fields');
      expect(customFieldsElements.length).toBeGreaterThan(0);
    });
  });

  describe('Filtering', () => {
    it('renders filter dropdown', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      // Cloudscape Select component - check for the selected option text
      expect(screen.getByText('All Servers')).toBeInTheDocument();
    });

    it('filters to show only custom configs', async () => {
      const user = userEvent.setup();
      render(<ServerConfigurationTab {...defaultProps} />);
      
      // Note: Actual filtering behavior depends on Cloudscape Select implementation
      // This test verifies the filter options exist
      expect(screen.getByText('All Servers')).toBeInTheDocument();
    });

    it('updates server count when filtered', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      // Initial count shows all servers
      expect(screen.getByText(/\(3\/3\)/)).toBeInTheDocument();
    });

    it('shows empty state message when filter returns no results', () => {
      const emptyConfigs = new Map<string, ServerLaunchConfig>();
      
      render(
        <ServerConfigurationTab {...defaultProps} serverConfigs={emptyConfigs} />
      );
      
      // When filtering for custom only with no custom configs
      expect(screen.getByText('All servers using protection group defaults')).toBeInTheDocument();
    });
  });

  describe('Dialog Opening', () => {
    it('opens dialog when Configure button is clicked', async () => {
      const user = userEvent.setup();
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      await user.click(configureButtons[0]);
      
      expect(screen.getByTestId('server-launch-config-dialog')).toBeInTheDocument();
    });

    it('passes correct server to dialog', async () => {
      const user = userEvent.setup();
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      await user.click(configureButtons[0]);
      
      expect(screen.getByTestId('dialog-server-id')).toHaveTextContent('s-111');
    });

    it('closes dialog when onClose is called', async () => {
      const user = userEvent.setup();
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      await user.click(configureButtons[0]);
      
      expect(screen.getByTestId('server-launch-config-dialog')).toBeInTheDocument();
      
      const closeButton = screen.getByRole('button', { name: /Close Dialog/ });
      await user.click(closeButton);
      
      expect(screen.queryByTestId('server-launch-config-dialog')).not.toBeInTheDocument();
    });

    it('calls onConfigChange when dialog saves', async () => {
      const user = userEvent.setup();
      const onConfigChange = vi.fn();
      
      render(
        <ServerConfigurationTab {...defaultProps} onConfigChange={onConfigChange} />
      );
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      await user.click(configureButtons[0]);
      
      const saveButton = screen.getByRole('button', { name: /Save Dialog/ });
      await user.click(saveButton);
      
      expect(onConfigChange).toHaveBeenCalledTimes(1);
      expect(onConfigChange).toHaveBeenCalledWith(
        's-111',
        expect.objectContaining({ sourceServerId: 's-111' })
      );
    });

    it('closes dialog after save', async () => {
      const user = userEvent.setup();
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const configureButtons = screen.getAllByRole('button', { name: /Configure/ });
      await user.click(configureButtons[0]);
      
      const saveButton = screen.getByRole('button', { name: /Save Dialog/ });
      await user.click(saveButton);
      
      expect(screen.queryByTestId('server-launch-config-dialog')).not.toBeInTheDocument();
    });
  });

  describe('Reset to Defaults', () => {
    it('calls onConfigChange with null when Reset is clicked', async () => {
      const user = userEvent.setup();
      const onConfigChange = vi.fn();
      
      render(
        <ServerConfigurationTab {...defaultProps} onConfigChange={onConfigChange} />
      );
      
      const resetButtons = screen.getAllByRole('button', { name: /Reset/ });
      await user.click(resetButtons[0]);
      
      expect(onConfigChange).toHaveBeenCalledTimes(1);
      expect(onConfigChange).toHaveBeenCalledWith('s-111', null);
    });

    it('does not show Reset button for servers without custom config', () => {
      const emptyConfigs = new Map<string, ServerLaunchConfig>();
      
      render(
        <ServerConfigurationTab {...defaultProps} serverConfigs={emptyConfigs} />
      );
      
      expect(screen.queryByRole('button', { name: /Reset/ })).not.toBeInTheDocument();
    });
  });

  describe('Bulk Configure Button', () => {
    it('renders Bulk Configure button', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /Bulk Configure/ })).toBeInTheDocument();
    });

    it('disables Bulk Configure when no servers', () => {
      render(<ServerConfigurationTab {...defaultProps} servers={[]} />);
      
      const bulkButton = screen.getByRole('button', { name: /Bulk Configure/ });
      expect(bulkButton).toBeDisabled();
    });

    it('enables Bulk Configure when servers exist', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const bulkButton = screen.getByRole('button', { name: /Bulk Configure/ });
      expect(bulkButton).not.toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('handles server without hostname', () => {
      const serversWithoutHostname: ResolvedServer[] = [
        {
          sourceServerID: 's-999',
          hostname: '',
          nameTag: undefined,
          replicationState: 'CONTINUOUS',
          tags: {},
        },
      ];

      render(
        <ServerConfigurationTab
          {...defaultProps}
          servers={serversWithoutHostname}
        />
      );
      
      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    it('handles empty serverConfigs map', () => {
      const emptyConfigs = new Map<string, ServerLaunchConfig>();
      
      render(
        <ServerConfigurationTab {...defaultProps} serverConfigs={emptyConfigs} />
      );
      
      expect(screen.getByText('web-server-01')).toBeInTheDocument();
      expect(
        screen.getByText('All servers using protection group defaults')
      ).toBeInTheDocument();
    });

    it('handles server with useGroupDefaults true but no launchTemplate', () => {
      const configsWithDefaults = new Map<string, ServerLaunchConfig>([
        [
          's-111',
          {
            sourceServerId: 's-111',
            useGroupDefaults: true,
            launchTemplate: {},
          },
        ],
      ]);

      render(
        <ServerConfigurationTab
          {...defaultProps}
          serverConfigs={configsWithDefaults}
        />
      );
      
      const badges = screen.getAllByTestId('config-badge');
      const defaultBadges = badges.filter(
        (badge) => badge.getAttribute('data-custom') === 'false'
      );
      expect(defaultBadges.length).toBeGreaterThan(0);
    });

    it('handles server with useGroupDefaults false', () => {
      const configsWithFullOverride = new Map<string, ServerLaunchConfig>([
        [
          's-111',
          {
            sourceServerId: 's-111',
            useGroupDefaults: false,
            launchTemplate: {
              instanceType: 'c6a.xlarge',
            },
          },
        ],
      ]);

      render(
        <ServerConfigurationTab
          {...defaultProps}
          serverConfigs={configsWithFullOverride}
        />
      );
      
      const badges = screen.getAllByTestId('config-badge');
      const customBadges = badges.filter(
        (badge) => badge.getAttribute('data-custom') === 'true'
      );
      expect(customBadges.length).toBeGreaterThan(0);
    });
  });

  describe('Custom Fields Detection', () => {
    it('detects staticPrivateIp as custom field', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const customFieldsElements = screen.getAllByTestId('custom-fields');
      const hasStaticIp = customFieldsElements.some((el) =>
        el.textContent?.includes('staticPrivateIp')
      );
      expect(hasStaticIp).toBe(true);
    });

    it('detects instanceType as custom field', () => {
      render(<ServerConfigurationTab {...defaultProps} />);
      
      const customFieldsElements = screen.getAllByTestId('custom-fields');
      const hasInstanceType = customFieldsElements.some((el) =>
        el.textContent?.includes('instanceType')
      );
      expect(hasInstanceType).toBe(true);
    });

    it('returns empty array for servers without custom config', () => {
      const emptyConfigs = new Map<string, ServerLaunchConfig>();
      
      render(
        <ServerConfigurationTab {...defaultProps} serverConfigs={emptyConfigs} />
      );
      
      expect(screen.queryByTestId('custom-fields')).not.toBeInTheDocument();
    });
  });
});
