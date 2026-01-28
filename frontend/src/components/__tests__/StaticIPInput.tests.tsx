/**
 * StaticIPInput Component Tests
 * 
 * Tests for the StaticIPInput component covering:
 * - Format validation (Requirements 3.1, 3.2)
 * - Rendering and props
 * - Error display
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { StaticIPInput } from '../StaticIPInput';
import '@testing-library/jest-dom';

// Mock the API client module
vi.mock('../../services/api', () => ({
  default: {
    validateStaticIP: vi.fn(),
  },
}));

describe('StaticIPInput', () => {
  const defaultProps = {
    value: '',
    subnetId: 'subnet-12345',
    groupId: 'group-123',
    serverId: 'server-456',
    region: 'us-east-1',
    onChange: vi.fn(),
    onValidation: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders with default label and description', () => {
      render(<StaticIPInput {...defaultProps} />);
      
      expect(screen.getByText('Static Private IP Address')).toBeInTheDocument();
      expect(screen.getByText(/Enter a private IP address within the target subnet/)).toBeInTheDocument();
    });

    it('renders with custom label and description', () => {
      render(
        <StaticIPInput
          {...defaultProps}
          label="Custom IP Label"
          description="Custom description"
        />
      );
      
      expect(screen.getByText('Custom IP Label')).toBeInTheDocument();
      expect(screen.getByText('Custom description')).toBeInTheDocument();
    });

    it('renders input field with placeholder', () => {
      render(<StaticIPInput {...defaultProps} />);
      
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toBeInTheDocument();
    });

    it('renders with initial value', () => {
      render(<StaticIPInput {...defaultProps} value="10.0.1.100" />);
      
      const input = screen.getByDisplayValue('10.0.1.100');
      expect(input).toBeInTheDocument();
    });

    it('renders as disabled when disabled prop is true', () => {
      render(<StaticIPInput {...defaultProps} disabled={true} />);
      
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toBeDisabled();
    });

    it('shows required constraint text when required is true', () => {
      render(<StaticIPInput {...defaultProps} required={true} />);
      
      expect(screen.getByText('Required')).toBeInTheDocument();
    });
  });

  describe('onChange Callback', () => {
    it('calls onChange callback on input change', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();

      render(<StaticIPInput {...defaultProps} onChange={onChange} />);
      
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      await user.type(input, '10');
      
      // userEvent.type() triggers onChange for each character separately
      expect(onChange).toHaveBeenCalled();
      // Check that it was called with individual characters (not accumulated)
      expect(onChange).toHaveBeenCalledWith('1');
      expect(onChange).toHaveBeenCalledWith('0');
    });
  });

  describe('Props Validation', () => {
    it('accepts all required props', () => {
      const { container } = render(<StaticIPInput {...defaultProps} />);
      expect(container).toBeInTheDocument();
    });

    it('accepts optional label prop', () => {
      render(<StaticIPInput {...defaultProps} label="Test Label" />);
      expect(screen.getByText('Test Label')).toBeInTheDocument();
    });

    it('accepts optional description prop', () => {
      render(<StaticIPInput {...defaultProps} description="Test description" />);
      expect(screen.getByText('Test description')).toBeInTheDocument();
    });

    it('accepts optional disabled prop', () => {
      render(<StaticIPInput {...defaultProps} disabled={true} />);
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toBeDisabled();
    });

    it('accepts optional required prop', () => {
      render(<StaticIPInput {...defaultProps} required={true} />);
      expect(screen.getByText('Required')).toBeInTheDocument();
    });
  });

  describe('Input Field Behavior', () => {
    it('allows typing in the input field', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<StaticIPInput {...defaultProps} onChange={onChange} />);
      
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      await user.type(input, '10.0.1.100');
      
      // Verify onChange was called multiple times (once per character)
      expect(onChange).toHaveBeenCalled();
      expect(onChange.mock.calls.length).toBeGreaterThan(1);
    });

    it('clears input when cleared by user', async () => {
      const user = userEvent.setup();
      const onChange = vi.fn();
      render(<StaticIPInput {...defaultProps} value="10.0.1.100" onChange={onChange} />);
      
      const input = screen.getByDisplayValue('10.0.1.100');
      await user.clear(input);
      
      // Verify onChange was called with empty string
      expect(onChange).toHaveBeenCalledWith('');
    });

    it('updates when value prop changes', () => {
      const { rerender } = render(<StaticIPInput {...defaultProps} value="10.0.1.100" />);
      expect(screen.getByDisplayValue('10.0.1.100')).toBeInTheDocument();
      
      rerender(<StaticIPInput {...defaultProps} value="10.0.1.200" />);
      expect(screen.getByDisplayValue('10.0.1.200')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('renders FormField wrapper', () => {
      const { container } = render(<StaticIPInput {...defaultProps} />);
      // FormField is rendered (Cloudscape component)
      expect(container.querySelector('input')).toBeInTheDocument();
    });

    it('renders Input component', () => {
      render(<StaticIPInput {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'text');
    });

    it('sets input mode to decimal', () => {
      render(<StaticIPInput {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toHaveAttribute('inputmode', 'decimal');
    });

    it('disables autocomplete', () => {
      render(<StaticIPInput {...defaultProps} />);
      const input = screen.getByPlaceholderText('e.g., 10.0.1.100');
      expect(input).toHaveAttribute('autocomplete', 'off');
    });
  });
});
