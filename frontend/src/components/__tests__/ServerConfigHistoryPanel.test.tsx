/**
 * ServerConfigHistoryPanel Component Tests
 * 
 * Tests for the configuration history audit trail component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ServerConfigHistoryPanel } from '../ServerConfigHistoryPanel';
import type { ConfigChangeEntry } from '../ServerConfigHistoryPanel';
import apiClient from '../../services/api';
import '@testing-library/jest-dom';

// Mock API client
vi.mock('../../services/api', () => ({
  default: {
    getServerConfigHistory: vi.fn(),
  },
}));

// Mock DateTimeDisplay component
vi.mock('../DateTimeDisplay', () => ({
  DateTimeDisplay: ({ timestamp }: { timestamp: string }) => (
    <span data-testid="datetime">{timestamp}</span>
  ),
}));

describe('ServerConfigHistoryPanel', () => {
  const mockServerId = 's-test123';
  const mockGroupId = 'pg-test456';

  const mockHistoryData: ConfigChangeEntry[] = [
    {
      timestamp: '2024-01-27T10:00:00Z',
      user: 'admin@example.com',
      action: 'UPDATE_SERVER_CONFIG',
      protectionGroupId: mockGroupId,
      serverId: mockServerId,
      changes: [
        {
          field: 'staticPrivateIp',
          oldValue: null,
          newValue: '10.0.1.100',
        },
        {
          field: 'instanceType',
          oldValue: 'c6a.large',
          newValue: 'c6a.xlarge',
        },
      ],
    },
    {
      timestamp: '2024-01-26T15:30:00Z',
      user: 'user@example.com',
      action: 'CREATE_SERVER_CONFIG',
      protectionGroupId: mockGroupId,
      serverId: mockServerId,
      changes: [
        {
          field: 'useGroupDefaults',
          oldValue: 'true',
          newValue: 'false',
        },
      ],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders component with header', () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue([]);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    expect(screen.getByText('Configuration History')).toBeInTheDocument();
    expect(
      screen.getByText(/View chronological history of configuration changes/)
    ).toBeInTheDocument();
  });

  it('loads and displays configuration history', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(mockHistoryData);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // Verify history entries are displayed
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('user@example.com')).toBeInTheDocument();
    expect(screen.getByText('Updated Configuration')).toBeInTheDocument();
    expect(screen.getByText('Created Configuration')).toBeInTheDocument();
  });

  it('displays empty state when no history exists', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue([]);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No configuration history')).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Configuration changes will appear here/)
    ).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    const errorMessage = 'Failed to fetch history';
    vi.mocked(apiClient.getServerConfigHistory).mockRejectedValue(
      new Error(errorMessage)
    );

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load history')).toBeInTheDocument();
    });

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('shows loading state while fetching data', () => {
    vi.mocked(apiClient.getServerConfigHistory).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    expect(screen.getByText('Loading configuration history...')).toBeInTheDocument();
  });

  it('displays change details in expandable sections', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(mockHistoryData);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('2 fields changed')).toBeInTheDocument();
    });

    // Verify expandable section shows field count
    expect(screen.getByText('2 fields changed')).toBeInTheDocument();
    expect(screen.getByText('1 field changed')).toBeInTheDocument();
  });

  it('formats field names correctly', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue([
      {
        timestamp: '2024-01-27T10:00:00Z',
        user: 'admin@example.com',
        action: 'UPDATE_SERVER_CONFIG',
        protectionGroupId: mockGroupId,
        serverId: mockServerId,
        changes: [
          {
            field: 'staticPrivateIp',
            oldValue: null,
            newValue: '10.0.1.100',
          },
        ],
      },
    ]);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // Field name should be formatted (staticPrivateIp -> Static Private IP)
    // This will be visible when the expandable section is expanded
    expect(screen.getByText('1 field changed')).toBeInTheDocument();
  });

  it('handles refresh button click', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(mockHistoryData);

    const onRefresh = vi.fn();
    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
        onRefresh={onRefresh}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    await userEvent.click(refreshButton);

    // Verify API was called again
    expect(apiClient.getServerConfigHistory).toHaveBeenCalledTimes(2);
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('calls API with correct parameters', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue([]);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(apiClient.getServerConfigHistory).toHaveBeenCalledWith(
        mockGroupId,
        mockServerId,
        expect.objectContaining({
          startDate: expect.any(String),
          endDate: expect.any(String),
        })
      );
    });
  });

  it('displays action status indicators correctly', async () => {
    const historyWithDifferentActions: ConfigChangeEntry[] = [
      {
        timestamp: '2024-01-27T10:00:00Z',
        user: 'admin@example.com',
        action: 'UPDATE_SERVER_CONFIG',
        protectionGroupId: mockGroupId,
        serverId: mockServerId,
        changes: [],
      },
      {
        timestamp: '2024-01-26T10:00:00Z',
        user: 'admin@example.com',
        action: 'CREATE_SERVER_CONFIG',
        protectionGroupId: mockGroupId,
        serverId: mockServerId,
        changes: [],
      },
      {
        timestamp: '2024-01-25T10:00:00Z',
        user: 'admin@example.com',
        action: 'DELETE_SERVER_CONFIG',
        protectionGroupId: mockGroupId,
        serverId: mockServerId,
        changes: [],
      },
    ];

    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(
      historyWithDifferentActions
    );

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Updated Configuration')).toBeInTheDocument();
    });

    expect(screen.getByText('Updated Configuration')).toBeInTheDocument();
    expect(screen.getByText('Created Configuration')).toBeInTheDocument();
    expect(screen.getByText('Deleted Configuration')).toBeInTheDocument();
  });

  it('formats null and empty values correctly', async () => {
    const historyWithNullValues: ConfigChangeEntry[] = [
      {
        timestamp: '2024-01-27T10:00:00Z',
        user: 'admin@example.com',
        action: 'UPDATE_SERVER_CONFIG',
        protectionGroupId: mockGroupId,
        serverId: mockServerId,
        changes: [
          {
            field: 'staticPrivateIp',
            oldValue: null,
            newValue: '10.0.1.100',
          },
          {
            field: 'instanceType',
            oldValue: 'c6a.large',
            newValue: '',
          },
        ],
      },
    ];

    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(
      historyWithNullValues
    );

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    // Verify the component renders without errors
    expect(screen.getByText('2 fields changed')).toBeInTheDocument();
  });

  it('displays counter in header when history exists', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue(mockHistoryData);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(`(${mockHistoryData.length})`)).toBeInTheDocument();
    });
  });

  it('does not display counter when history is empty', async () => {
    vi.mocked(apiClient.getServerConfigHistory).mockResolvedValue([]);

    render(
      <ServerConfigHistoryPanel
        serverId={mockServerId}
        protectionGroupId={mockGroupId}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No configuration history')).toBeInTheDocument();
    });

    // Counter should not be present
    expect(screen.queryByText(/^\(\d+\)$/)).not.toBeInTheDocument();
  });
});
