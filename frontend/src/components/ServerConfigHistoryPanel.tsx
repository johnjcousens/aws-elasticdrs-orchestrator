/**
 * ServerConfigHistoryPanel Component
 * 
 * Displays audit trail of per-server launch configuration changes.
 * Features:
 * - Chronological list of configuration changes
 * - Shows timestamp, user, changed fields
 * - Before/after value display for each change
 * - Date range filter
 * - Expandable detail view for each change
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  Table,
  Button,
  Alert,
  StatusIndicator,
  ExpandableSection,
  ColumnLayout,
  DateRangePicker,
  type DateRangePickerProps,
} from '@cloudscape-design/components';
import { DateTimeDisplay } from './DateTimeDisplay';
import apiClient from '../services/api';

/**
 * Configuration change audit log entry
 */
export interface ConfigChangeEntry {
  timestamp: string;
  user: string;
  action: string;
  protectionGroupId: string;
  serverId: string;
  changes: Array<{
    field: string;
    oldValue: string | null;
    newValue: string | null;
  }>;
}

export interface ServerConfigHistoryPanelProps {
  /** Server ID to fetch history for */
  serverId: string;
  /** Protection group ID */
  protectionGroupId: string;
  /** Optional callback when history is refreshed */
  onRefresh?: () => void;
}

/**
 * ServerConfigHistoryPanel Component
 * 
 * Displays chronological audit trail of server configuration changes.
 */
export const ServerConfigHistoryPanel: React.FC<ServerConfigHistoryPanelProps> = ({
  serverId,
  protectionGroupId,
  onRefresh,
}) => {
  // State
  const [history, setHistory] = useState<ConfigChangeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<DateRangePickerProps.Value>({
    type: 'relative',
    amount: 30,
    unit: 'day',
  });

  /**
   * Load configuration history from API
   */
  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query parameters for date range
      const params: Record<string, string> = {};
      
      if (dateRange?.type === 'absolute' && dateRange.startDate && dateRange.endDate) {
        params.startDate = dateRange.startDate;
        params.endDate = dateRange.endDate;
      } else if (dateRange?.type === 'relative') {
        // Calculate relative date range
        const now = new Date();
        const startDate = new Date(now);
        
        if (dateRange.unit === 'day') {
          startDate.setDate(now.getDate() - (dateRange.amount || 30));
        } else if (dateRange.unit === 'week') {
          startDate.setDate(now.getDate() - (dateRange.amount || 4) * 7);
        } else if (dateRange.unit === 'month') {
          startDate.setMonth(now.getMonth() - (dateRange.amount || 1));
        }
        
        params.startDate = startDate.toISOString();
        params.endDate = now.toISOString();
      }

      // Fetch history from API
      const response = await apiClient.getServerConfigHistory(
        protectionGroupId,
        serverId,
        params
      );

      setHistory(response || []);
    } catch (err: unknown) {
      const error = err as Error & { message?: string };
      console.error('Failed to load configuration history:', error);
      setError(error.message || 'Failed to load configuration history');
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Load history on mount and when filters change
   */
  useEffect(() => {
    loadHistory();
  }, [serverId, protectionGroupId, dateRange]);

  /**
   * Handle refresh button click
   */
  const handleRefresh = () => {
    loadHistory();
    onRefresh?.();
  };

  /**
   * Format field name for display
   */
  const formatFieldName = (field: string): string => {
    const fieldNames: Record<string, string> = {
      staticPrivateIp: 'Static Private IP',
      subnetId: 'Subnet',
      securityGroupIds: 'Security Groups',
      instanceType: 'Instance Type',
      instanceProfileName: 'IAM Instance Profile',
      associatePublicIp: 'Associate Public IP',
      monitoring: 'Detailed Monitoring',
      ebsOptimized: 'EBS Optimized',
      disableApiTermination: 'Termination Protection',
      tags: 'Tags',
      useGroupDefaults: 'Use Group Defaults',
    };
    return fieldNames[field] || field;
  };

  /**
   * Format value for display
   */
  const formatValue = (value: string | null): string => {
    if (value === null || value === undefined) {
      return '(not set)';
    }
    if (value === '') {
      return '(empty)';
    }
    if (typeof value === 'boolean') {
      return value ? 'Yes' : 'No';
    }
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    return String(value);
  };

  /**
   * Get action display text
   */
  const getActionText = (action: string): string => {
    const actions: Record<string, string> = {
      UPDATE_SERVER_CONFIG: 'Updated Configuration',
      CREATE_SERVER_CONFIG: 'Created Configuration',
      DELETE_SERVER_CONFIG: 'Deleted Configuration',
      RESET_TO_DEFAULTS: 'Reset to Defaults',
    };
    return actions[action] || action;
  };

  /**
   * Get action status indicator type
   */
  const getActionStatus = (action: string): 'success' | 'info' | 'warning' => {
    if (action === 'DELETE_SERVER_CONFIG' || action === 'RESET_TO_DEFAULTS') {
      return 'warning';
    }
    if (action === 'CREATE_SERVER_CONFIG') {
      return 'success';
    }
    return 'info';
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="View chronological history of configuration changes for this server"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                iconName="refresh"
                onClick={handleRefresh}
                disabled={loading}
                loading={loading}
              >
                Refresh
              </Button>
            </SpaceBetween>
          }
        >
          Configuration History
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Date Range Filter */}
        <DateRangePicker
          value={dateRange}
          onChange={({ detail }) => {
            if (detail.value) {
              setDateRange(detail.value);
            }
          }}
          relativeOptions={[
            { key: 'previous-7-days', amount: 7, unit: 'day', type: 'relative' },
            { key: 'previous-30-days', amount: 30, unit: 'day', type: 'relative' },
            { key: 'previous-90-days', amount: 90, unit: 'day', type: 'relative' },
          ]}
          isValidRange={(range) => {
            if (!range || range.type !== 'absolute') {
              return { valid: true };
            }
            const start = new Date(range.startDate || '');
            const end = new Date(range.endDate || '');
            if (start > end) {
              return { valid: false, errorMessage: 'Start date must be before end date' };
            }
            return { valid: true };
          }}
          placeholder="Filter by date range"
          rangeSelectorMode="absolute-only"
        />

        {/* Error Alert */}
        {error && (
          <Alert type="error" header="Failed to load history">
            {error}
          </Alert>
        )}

        {/* History Table */}
        <Table
          columnDefinitions={[
            {
              id: 'timestamp',
              header: 'Timestamp',
              cell: (item: ConfigChangeEntry) => (
                <DateTimeDisplay value={item.timestamp} />
              ),
              sortingField: 'timestamp',
              width: 200,
            },
            {
              id: 'user',
              header: 'User',
              cell: (item: ConfigChangeEntry) => item.user || 'System',
              sortingField: 'user',
              width: 200,
            },
            {
              id: 'action',
              header: 'Action',
              cell: (item: ConfigChangeEntry) => (
                <StatusIndicator type={getActionStatus(item.action)}>
                  {getActionText(item.action)}
                </StatusIndicator>
              ),
              width: 180,
            },
            {
              id: 'changes',
              header: 'Changes',
              cell: (item: ConfigChangeEntry) => (
                <ExpandableSection
                  variant="footer"
                  headerText={`${item.changes.length} field${item.changes.length !== 1 ? 's' : ''} changed`}
                >
                  <SpaceBetween size="m">
                    {item.changes.map((change, index) => (
                      <Box key={index} padding="s">
                        <ColumnLayout columns={3} variant="text-grid">
                          <div>
                            <Box variant="awsui-key-label">Field</Box>
                            <div>{formatFieldName(change.field)}</div>
                          </div>
                          <div>
                            <Box variant="awsui-key-label">Previous Value</Box>
                            <div>
                              <Box color="text-status-inactive">
                                {formatValue(change.oldValue)}
                              </Box>
                            </div>
                          </div>
                          <div>
                            <Box variant="awsui-key-label">New Value</Box>
                            <div>
                              <Box color="text-status-success">
                                {formatValue(change.newValue)}
                              </Box>
                            </div>
                          </div>
                        </ColumnLayout>
                      </Box>
                    ))}
                  </SpaceBetween>
                </ExpandableSection>
              ),
            },
          ]}
          items={history}
          loading={loading}
          loadingText="Loading configuration history..."
          sortingDescending
          empty={
            <Box textAlign="center" color="inherit">
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                <b>No configuration history</b>
              </Box>
              <Box variant="p" color="inherit">
                Configuration changes will appear here once you modify server settings.
              </Box>
            </Box>
          }
          header={
            <Header
              counter={history.length > 0 ? `(${history.length})` : undefined}
            >
              Change History
            </Header>
          }
        />
      </SpaceBetween>
    </Container>
  );
};

export default ServerConfigHistoryPanel;
