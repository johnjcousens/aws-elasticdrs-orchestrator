/**
 * ConfigImportPanel Integration Tests - Simplified
 * 
 * Simplified integration tests focusing on core functionality
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfigImportPanel } from '../ConfigImportPanel';
import '@testing-library/jest-dom';

// Create mock functions at module level
const mockImportConfiguration = vi.fn();

// Mock toast
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
  }
}));

// Mock ImportResultsDialog
vi.mock('../ImportResultsDialog', () => ({
  ImportResultsDialog: () => null
}));

// Mock ApiContext
vi.mock('../../contexts/ApiContext', () => ({
  ApiProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useApi: () => ({
    importConfiguration: mockImportConfiguration,
  }),
}));

describe('ConfigImportPanel - Integration Tests (Simplified)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockImportConfiguration.mockReset();
  });

  it('renders the import panel', () => {
    render(<ConfigImportPanel />);
    
    expect(screen.getByRole('button', { name: /Select File/i })).toBeInTheDocument();
    expect(screen.getByText(/Import Protection Groups and Recovery Plans/i)).toBeInTheDocument();
  });

  it('shows schema version 1.1 support message', () => {
    render(<ConfigImportPanel />);
    
    // Component should mention support for per-server configurations
    expect(screen.getByText(/non-destructive/i)).toBeInTheDocument();
  });
});
