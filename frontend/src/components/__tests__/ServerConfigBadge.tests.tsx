/**
 * ServerConfigBadge Component Tests - Simplified
 * 
 * Tests for the ServerConfigBadge component without tooltip interactions
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ServerConfigBadge } from '../ServerConfigBadge';
import '@testing-library/jest-dom';

describe('ServerConfigBadge', () => {
  describe('Badge Rendering', () => {
    it('renders "Default" badge for default config', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={false}
          customFields={[]}
        />
      );
      
      expect(screen.getByText('Default')).toBeInTheDocument();
    });

    it('renders "Custom" badge for custom config', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('renders "Custom" badge when custom config has no specific fields', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={[]}
        />
      );
      
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });
  });

  describe('Props Handling', () => {
    it('handles staticPrivateIp field', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('handles multiple fields', () => {
      render(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp', 'instanceType', 'subnetId']}
        />
      );
      
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });

    it('updates when props change', () => {
      const { rerender } = render(
        <ServerConfigBadge
          hasCustomConfig={false}
          customFields={[]}
        />
      );
      
      expect(screen.getByText('Default')).toBeInTheDocument();
      
      rerender(
        <ServerConfigBadge
          hasCustomConfig={true}
          customFields={['staticPrivateIp']}
        />
      );
      
      expect(screen.getByText('Custom')).toBeInTheDocument();
    });
  });
});
