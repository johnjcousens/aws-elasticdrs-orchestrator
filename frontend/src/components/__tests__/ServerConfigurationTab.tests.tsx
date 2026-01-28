/**
 * ServerConfigurationTab Component Tests - Simplified
 * 
 * Simplified tests focusing on core rendering functionality
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ServerConfigurationTab } from '../ServerConfigurationTab';
import type { ResolvedServer, LaunchConfig, ServerLaunchConfig } from '../../types';
import '@testing-library/jest-dom';

describe('ServerConfigurationTab', () => {
  const mockServers: ResolvedServer[] = [
    {
      sourceServerID: 's-123',
      hostname: 'web-server-01',
      state: 'READY',
      replicationState: 'CONTINUOUS',
      lagDuration: '0',
      lastSeen: '2024-01-01T00:00:00Z',
      assignedToProtectionGroup: null,
      selectable: true,
      tags: {},
    },
    {
      sourceServerID: 's-456',
      hostname: 'app-server-01',
      state: 'READY',
      replicationState: 'CONTINUOUS',
      lagDuration: '0',
      lastSeen: '2024-01-01T00:00:00Z',
      assignedToProtectionGroup: null,
      selectable: true,
      tags: {},
    },
  ];

  const mockGroupDefaults: LaunchConfig = {
    subnetId: 'subnet-123',
    securityGroupIds: ['sg-123'],
  };

  const mockServerConfigs = new Map<string, ServerLaunchConfig>();

  const mockOnConfigChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Component Rendering', () => {
    it('renders the component', () => {
      render(
        <ServerConfigurationTab
          protectionGroupId="pg-123"
          servers={mockServers}
          groupDefaults={mockGroupDefaults}
          serverConfigs={mockServerConfigs}
          region="us-east-1"
          onConfigChange={mockOnConfigChange}
          loading={false}
        />
      );

      expect(screen.getByText('web-server-01')).toBeInTheDocument();
      expect(screen.getByText('app-server-01')).toBeInTheDocument();
    });

    it('shows empty state when no servers', () => {
      render(
        <ServerConfigurationTab
          protectionGroupId="pg-123"
          servers={[]}
          groupDefaults={mockGroupDefaults}
          serverConfigs={mockServerConfigs}
          region="us-east-1"
          onConfigChange={mockOnConfigChange}
          loading={false}
        />
      );

      // Use getAllByText since there are multiple "No servers" elements
      const noServersElements = screen.getAllByText(/No servers/i);
      expect(noServersElements.length).toBeGreaterThan(0);
    });

    it('renders Configure buttons for servers', () => {
      render(
        <ServerConfigurationTab
          protectionGroupId="pg-123"
          servers={mockServers}
          groupDefaults={mockGroupDefaults}
          serverConfigs={mockServerConfigs}
          region="us-east-1"
          onConfigChange={mockOnConfigChange}
          loading={false}
        />
      );

      // There are 3 Configure buttons: 1 "Bulk Configure" in header + 2 per-server "Configure" buttons
      const configureButtons = screen.getAllByRole('button', { name: /Configure/i });
      expect(configureButtons).toHaveLength(3);
    });
  });
});
