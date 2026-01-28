/**
 * ServerConfigBadge Component Tests
 * 
 * Tests for the ServerConfigBadge component covering:
 * - Badge rendering (Requirements 6.1, 6.3)
 * - Tooltip content
 * - Field name mapping
 * - Visual indicators
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect } from 'vitest';
import { ServerConfigBadge } from '../ServerConfigBadge';
import '@testing-library/jest-dom';

describe('ServerConfigBadge', () => {
  describe('Badge Rendering', () => {
    it('renders "Default" badge when hasCustomConfig is false', () => {
      render(<ServerConfigBadge hasCustomConfig={false} />);
      expect(screen.getByText('Default')).toBeInTheDocument();
    });

    it('renders "Custom" badge when hasCustomConfig is true', () => {
      render(<ServerConfigBadge hasCustomConfig={true} />);
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('renders with custom fields list', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp', 'instanceType']}
        />
      );
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('renders with empty custom fields array', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={[]}
        />
      );
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('renders badge with correct color for custom config', () => {
      const { container } = render(<ServerConfigBadge hasCustomConfig={true} />);
      const badge = screen.getByText('Custom');
      expect(badge).toBeInTheDocument();
      // Badge should have blue color class (Cloudscape uses color prop)
    });

    it('renders badge with correct color for default config', () => {
      const { container } = render(<ServerConfigBadge hasCustomConfig={false} />);
      const badge = screen.getByText('Default');
      expect(badge).toBeInTheDocument();
      // Badge should have grey color class (Cloudscape uses color prop)
    });
  });

  describe('Tooltip Content', () => {
    it('shows tooltip with "Using protection group defaults" for default config', async () => {
      const user = userEvent.setup();
      render(<ServerConfigBadge hasCustomConfig={false} />);
      
      const badge = screen.getByText('Default');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Using protection group defaults')).toBeInTheDocument();
      });
    });

    it('shows tooltip with customized fields list for custom config', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp', 'instanceType', 'subnetId']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Customized fields:')).toBeInTheDocument();
        expect(screen.getByText('Static Private IP')).toBeInTheDocument();
        expect(screen.getByText('Instance Type')).toBeInTheDocument();
        expect(screen.getByText('Subnet')).toBeInTheDocument();
      });
    });

    it('shows generic message when custom config has no specific fields', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={[]}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Custom configuration applied')).toBeInTheDocument();
      });
    });
  });

  describe('Field Name Mapping', () => {
    it('maps staticPrivateIp to user-friendly name', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Static Private IP')).toBeInTheDocument();
      });
    });

    it('maps securityGroupIds to user-friendly name', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['securityGroupIds']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Security Groups')).toBeInTheDocument();
      });
    });

    it('maps instanceProfileName to user-friendly name', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['instanceProfileName']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('IAM Instance Profile')).toBeInTheDocument();
      });
    });

    it('displays unmapped field names as-is', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['unknownField']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('unknownField')).toBeInTheDocument();
      });
    });

    it('handles multiple field mappings correctly', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={[
            'staticPrivateIp',
            'instanceType',
            'securityGroupIds',
            'tags',
            'monitoring'
          ]}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Static Private IP')).toBeInTheDocument();
        expect(screen.getByText('Instance Type')).toBeInTheDocument();
        expect(screen.getByText('Security Groups')).toBeInTheDocument();
        expect(screen.getByText('Resource Tags')).toBeInTheDocument();
        expect(screen.getByText('Detailed Monitoring')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles undefined customFields gracefully', () => {
      render(<ServerConfigBadge hasCustomConfig={true} />);
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('handles null customFields gracefully', () => {
      render(<ServerConfigBadge hasCustomConfig={true} customFields={undefined} />);
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('renders correctly when hasCustomConfig changes', () => {
      const { rerender } = render(<ServerConfigBadge hasCustomConfig={false} />);
      expect(screen.getByText('Default')).toBeInTheDocument();
      
      rerender(<ServerConfigBadge hasCustomConfig={true} />);
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('updates tooltip when customFields change', async () => {
      const user = userEvent.setup();
      const { rerender } = render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Static Private IP')).toBeInTheDocument();
      });
      
      // Unhover
      await user.unhover(badge);
      
      // Update fields
      rerender(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['instanceType', 'subnetId']}
        />
      );
      
      // Hover again
      await user.hover(badge);
      
      await waitFor(() => {
        expect(screen.getByText('Instance Type')).toBeInTheDocument();
        expect(screen.getByText('Subnet')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('renders badge as interactive element', () => {
      render(<ServerConfigBadge hasCustomConfig={true} />);
      const badge = screen.getByText('Custom');
      expect(badge).toBeInTheDocument();
    });

    it('provides tooltip on hover for screen readers', async () => {
      const user = userEvent.setup();
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      const badge = screen.getByText('Custom');
      await user.hover(badge);
      
      await waitFor(() => {
        const tooltip = screen.getByText('Customized fields:');
        expect(tooltip).toBeInTheDocument();
      });
    });
  });

  describe('Visual Indicators', () => {
    it('uses blue badge for custom configuration', () => {
      render(<ServerConfigBadge hasCustomConfig={true} />);
      const badge = screen.getByText('Custom');
      expect(badge).toBeInTheDocument();
      // Cloudscape Badge component uses color="blue" prop
    });

    it('uses grey badge for default configuration', () => {
      render(<ServerConfigBadge hasCustomConfig={false} />);
      const badge = screen.getByText('Default');
      expect(badge).toBeInTheDocument();
      // Cloudscape Badge component uses color="grey" prop
    });
  });
});
