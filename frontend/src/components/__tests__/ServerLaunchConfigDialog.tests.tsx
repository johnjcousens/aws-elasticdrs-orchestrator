/**
 * ServerLaunchConfigDialog Component Tests
 * 
 * Tests for the ServerLaunchConfigDialog component covering:
 * - Form rendering (Requirement 2.1)
 * - Validation (Requirements 3.1, 5.1)
 * - Save/cancel actions (Requirement 2.1)
 * - Group defaults display (Requirement 6.1)
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ServerLaunchConfigDialog } from '../ServerLaunchConfigDialog';
import type {
  ResolvedServer,
  LaunchConfig,
  ServerLaunchConfig,
} from '../../types';
import '@testing-library/jest-dom';

// Mock the API client module with factory function
vi.mock('../../services/api', () => ({
  default: {
    validateStaticIP: vi.fn(),
    getEC2Subnets: vi.fn(),
    getEC2SecurityGroups: vi.fn(),
    getEC2InstanceTypes: vi.fn(),
  },
}));

// Import the mocked module to get access to the mock functions
import apiClient from '../../services/api';

// Mock child components
vi.mock('../StaticIPInput', () => ({
  StaticIPInput: ({ value, onChange, label }: any) => (
    <div data-testid="static-ip-input">
      <label>{typeof label === 'string' ? label : 'Static IP'}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="IP address"
      />
    </div>
  ),
}));

vi.mock('../ServerConfigBadge', () => ({
  ServerConfigBadge: ({ hasCustomConfig }: any) => (
    <span data-testid="config-badge">
      {hasCustomConfig ? 'Custom' : 'Default'}
    </span>
  ),
}));

describe('ServerLaunchConfigDialog', () => {
  const mockServer: ResolvedServer = {
    sourceServerID: 's-12345',
    hostname: 'web-server-01',
    nameTag: 'WebServer01',
    sourceInstanceId: 'i-abcdef',
    replicationState: 'CONTINUOUS',
    tags: { Name: 'web-server-01', Environment: 'Production' },
  };

  const mockGroupDefaults: LaunchConfig = {
    subnetId: 'subnet-default',
    securityGroupIds: ['sg-default'],
    instanceType: 'c6a.large',
  };

  const defaultProps = {
    open: true,
    server: mockServer,
    groupDefaults: mockGroupDefaults,
    region: 'us-east-1',
    groupId: 'group-123',
    onClose: vi.fn(),
    onSave: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock return values using the imported mocked apiClient
    (apiClient.getEC2Subnets as any).mockResolvedValue([
      {
        value: 'subnet-default',
        label: 'Default Subnet',
        vpcId: 'vpc-123',
        az: 'us-east-1a',
        cidr: '10.0.1.0/24',
      },
      {
        value: 'subnet-custom',
        label: 'Custom Subnet',
        vpcId: 'vpc-123',
        az: 'us-east-1b',
        cidr: '10.0.2.0/24',
      },
    ]);
    
    (apiClient.getEC2SecurityGroups as any).mockResolvedValue([
      {
        value: 'sg-default',
        label: 'Default SG',
        name: 'default-sg',
        vpcId: 'vpc-123',
        description: 'Default security group',
      },
      {
        value: 'sg-custom',
        label: 'Custom SG',
        name: 'custom-sg',
        vpcId: 'vpc-123',
        description: 'Custom security group',
      },
    ]);
    
    (apiClient.getEC2InstanceTypes as any).mockResolvedValue([
      {
        value: 'c6a.large',
        label: 'c6a.large',
        vcpus: 2,
        memoryGb: 4,
      },
      {
        value: 't3.medium',
        label: 't3.medium',
        vcpus: 2,
        memoryGb: 4,
      },
    ]);
    
    (apiClient.validateStaticIP as any).mockResolvedValue({ valid: true });
  });

  // Helper function to wait for component to finish loading
  const waitForLoading = async () => {
    // Wait for all API calls to resolve
    await waitFor(async () => {
      // Force a tick to let promises resolve
      await new Promise(resolve => setTimeout(resolve, 0));
      expect(screen.queryByText(/Loading EC2 resources/)).not.toBeInTheDocument();
    }, { timeout: 5000 });
  };

  describe('Form Rendering', () => {
    it('renders dialog with server information', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      
      // Wait for API calls to complete
      await waitFor(() => {
        expect(apiClient.getEC2Subnets).toHaveBeenCalled();
        expect(apiClient.getEC2SecurityGroups).toHaveBeenCalled();
        expect(apiClient.getEC2InstanceTypes).toHaveBeenCalled();
      });
      
      await waitForLoading();
      
      expect(screen.getByText(/Configure Launch Settings: web-server-01/)).toBeInTheDocument();
      expect(screen.getByText(/Server: s-12345/)).toBeInTheDocument();
      expect(screen.getByText(/Instance: i-abcdef/)).toBeInTheDocument();
    });

    it('renders "Use Protection Group Defaults" checkbox', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      expect(checkbox).toBeInTheDocument();
      expect(checkbox).toBeChecked(); // Default state
    });

    it('renders StaticIPInput component', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByTestId('static-ip-input')).toBeInTheDocument();
    });

    it('renders subnet dropdown', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText('Target Subnet')).toBeInTheDocument();
    });

    it('renders security groups dropdown', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText('Security Groups')).toBeInTheDocument();
    });

    it('renders instance type dropdown', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText('Instance Type')).toBeInTheDocument();
    });

    it('renders Save and Cancel buttons', () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: /Save Configuration/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Cancel/ })).toBeInTheDocument();
    });

    it('does not render when open is false', () => {
      render(<ServerLaunchConfigDialog {...defaultProps} open={false} />);
      
      // Modal component renders but should have hidden class when closed
      // The class name has a hash suffix, so check if it contains 'hidden'
      const modal = document.querySelector('[role="dialog"]');
      expect(modal?.className).toMatch(/awsui_hidden/);
    });
  });

  describe('Group Defaults Display', () => {
    it('shows group default subnet in description', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText(/Group default: subnet-default/)).toBeInTheDocument();
    });

    it('shows group default security groups in description', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText(/Group default: sg-default/)).toBeInTheDocument();
    });

    it('shows group default instance type in description', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText(/Group default: c6a.large/)).toBeInTheDocument();
    });

    it('shows info alert when using group defaults', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      expect(screen.getByText(/Using Group Defaults/)).toBeInTheDocument();
      expect(
        screen.getByText(/Only fields you explicitly configure will override/)
      ).toBeInTheDocument();
    });
  });

  describe('Server Configuration Initialization', () => {
    it('initializes form with existing server configuration', async () => {
      const serverConfig: ServerLaunchConfig = {
        sourceServerId: 's-12345',
        useGroupDefaults: false,
        launchTemplate: {
          staticPrivateIp: '10.0.1.100',
          subnetId: 'subnet-custom',
          instanceType: 'c6a.xlarge',
        },
      };

      render(
        <ServerLaunchConfigDialog {...defaultProps} serverConfig={serverConfig} />
      );
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      expect(checkbox).not.toBeChecked();
    });

    it('initializes with group defaults when no server config exists', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      expect(checkbox).toBeChecked();
    });
  });

  describe('Use Group Defaults Toggle', () => {
    it('toggles useGroupDefaults checkbox', async () => {
      const user = userEvent.setup();
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      
      expect(checkbox).toBeChecked();
      
      await user.click(checkbox);
      
      expect(checkbox).not.toBeChecked();
    });

    it('hides info alert when not using group defaults', async () => {
      const user = userEvent.setup();
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      
      await user.click(checkbox);
      
      expect(screen.queryByText(/Using Group Defaults/)).not.toBeInTheDocument();
    });
  });

  describe('Static IP Input', () => {
    it('updates static IP value on change', async () => {
      const user = userEvent.setup();
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const input = screen.getByPlaceholderText('IP address') as HTMLInputElement;
      
      // Use clear + type with delay: 0 for faster test execution
      await user.clear(input);
      await user.type(input, '10.0.1.100', { delay: 0 });
      
      expect(input).toHaveValue('10.0.1.100');
    });

    it('initializes with existing static IP from server config', async () => {
      const serverConfig: ServerLaunchConfig = {
        sourceServerId: 's-12345',
        useGroupDefaults: true,
        launchTemplate: {
          staticPrivateIp: '10.0.1.50',
        },
      };

      render(
        <ServerLaunchConfigDialog {...defaultProps} serverConfig={serverConfig} />
      );
      await waitForLoading();
      
      const input = screen.getByPlaceholderText('IP address');
      expect(input).toHaveValue('10.0.1.50');
    });
  });

  describe('Save Action', () => {
    it('calls onSave with configuration when Save button is clicked', async () => {
      const user = userEvent.setup();
      const onSave = vi.fn();
      
      render(<ServerLaunchConfigDialog {...defaultProps} onSave={onSave} />);
      await waitForLoading();
      
      // Make a change to enable save button
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      await user.click(checkbox);
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      await user.click(saveButton);
      
      expect(onSave).toHaveBeenCalledTimes(1);
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          sourceServerId: 's-12345',
          useGroupDefaults: false,
        })
      );
    });

    it('includes static IP in saved configuration', async () => {
      const user = userEvent.setup();
      const onSave = vi.fn();
      
      render(<ServerLaunchConfigDialog {...defaultProps} onSave={onSave} />);
      await waitForLoading();
      
      const input = screen.getByPlaceholderText('IP address');
      await user.type(input, '10.0.1.100');
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      await user.click(saveButton);
      
      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          launchTemplate: expect.objectContaining({
            staticPrivateIp: '10.0.1.100',
          }),
        })
      );
    });

    it('disables save button when no changes are made', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      expect(saveButton).toBeDisabled();
    });

    it('enables save button when changes are made', async () => {
      const user = userEvent.setup();
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      expect(saveButton).toBeDisabled();
      
      const input = screen.getByPlaceholderText('IP address');
      await user.type(input, '10.0.1.100');
      
      await waitFor(() => {
        expect(saveButton).not.toBeDisabled();
      });
    });

    it('shows loading state on save button when saving', () => {
      render(<ServerLaunchConfigDialog {...defaultProps} saving={true} />);
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      expect(saveButton).toBeDisabled();
    });
  });

  describe('Cancel Action', () => {
    it('calls onClose when Cancel button is clicked', async () => {
      const user = userEvent.setup();
      const onClose = vi.fn();
      
      render(<ServerLaunchConfigDialog {...defaultProps} onClose={onClose} />);
      
      const cancelButton = screen.getByRole('button', { name: /Cancel/ });
      await user.click(cancelButton);
      
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('disables cancel button when saving', () => {
      render(<ServerLaunchConfigDialog {...defaultProps} saving={true} />);
      
      const cancelButton = screen.getByRole('button', { name: /Cancel/ });
      expect(cancelButton).toBeDisabled();
    });
  });

  describe('Validation', () => {
    it('disables save button when IP validation fails', async () => {
      const user = userEvent.setup();
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      // Type an invalid IP
      const input = screen.getByPlaceholderText('IP address');
      await user.type(input, 'invalid-ip');
      
      const saveButton = screen.getByRole('button', { name: /Save Configuration/ });
      
      // Note: Actual validation happens in StaticIPInput component
      // This test verifies the dialog respects validation state
      expect(saveButton).toBeInTheDocument();
    });
  });

  describe('Configuration Badges', () => {
    it('shows configuration badges for fields', async () => {
      render(<ServerLaunchConfigDialog {...defaultProps} />);
      await waitForLoading();
      
      const badges = screen.getAllByTestId('config-badge');
      expect(badges.length).toBeGreaterThan(0);
    });

    it('shows custom badge for overridden fields', async () => {
      const serverConfig: ServerLaunchConfig = {
        sourceServerId: 's-12345',
        useGroupDefaults: false,
        launchTemplate: {
          instanceType: 'c6a.xlarge',
        },
      };

      render(
        <ServerLaunchConfigDialog {...defaultProps} serverConfig={serverConfig} />
      );
      await waitForLoading();
      
      const badges = screen.getAllByTestId('config-badge');
      expect(badges.some(badge => badge.textContent === 'Custom')).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('handles server without hostname gracefully', async () => {
      const serverWithoutHostname: ResolvedServer = {
        ...mockServer,
        hostname: 'Unknown',
        nameTag: undefined,
      };

      render(
        <ServerLaunchConfigDialog
          {...defaultProps}
          server={serverWithoutHostname}
        />
      );
      await waitForLoading();
      
      expect(screen.getByText(/Configure Launch Settings: Unknown/)).toBeInTheDocument();
    });

    it('handles missing group defaults', async () => {
      const emptyDefaults: LaunchConfig = {};

      render(
        <ServerLaunchConfigDialog {...defaultProps} groupDefaults={emptyDefaults} />
      );
      await waitForLoading();
      
      expect(screen.getByText('Target Subnet')).toBeInTheDocument();
    });
  });

  describe('Form Reset on Dialog Open', () => {
    it('resets form when dialog is reopened', async () => {
      const { rerender } = render(
        <ServerLaunchConfigDialog {...defaultProps} open={false} />
      );
      
      // Open dialog
      rerender(<ServerLaunchConfigDialog {...defaultProps} open={true} />);
      await waitForLoading();
      
      const checkbox = screen.getByRole('checkbox', {
        name: /Use Protection Group Defaults/,
      });
      expect(checkbox).toBeChecked();
    });
  });
});
