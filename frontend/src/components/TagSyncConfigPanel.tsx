/**
 * Tag Sync Configuration Panel Component
 * 
 * Provides configuration interface for scheduled DRS tag synchronization.
 * Allows users to enable/disable scheduled sync and configure the interval.
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  FormField,
  Toggle,
  Select,
  Button,
  Alert,
  StatusIndicator,
  Box,
  ColumnLayout,
} from '@cloudscape-design/components';
import apiClient from '../services/api';
import toast from 'react-hot-toast';

interface TagSyncSettings {
  enabled: boolean;
  intervalHours: number;
  scheduleExpression: string;
  ruleName: string;
  lastModified: string | null;
}

interface TagSyncConfigPanelProps {
  onConfigurationChange?: () => void;
}

export const TagSyncConfigPanel: React.FC<TagSyncConfigPanelProps> = ({
  onConfigurationChange,
}) => {
  const [settings, setSettings] = useState<TagSyncSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [enabled, setEnabled] = useState(false);
  const [intervalHours, setIntervalHours] = useState(4);

  // Interval options (1-24 hours)
  const intervalOptions = [
    { value: '1', label: '1 hour' },
    { value: '2', label: '2 hours' },
    { value: '4', label: '4 hours' },
    { value: '6', label: '6 hours' },
    { value: '8', label: '8 hours' },
    { value: '12', label: '12 hours' },
    { value: '24', label: '24 hours (daily)' },
  ];

  /**
   * Load current tag sync settings
   */
  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.getTagSyncSettings();
      setSettings(response);
      setEnabled(response.enabled);
      setIntervalHours(response.intervalHours);
      
    } catch (err: unknown) {
      const error = err as Error & { message?: string };
      console.error('Failed to load tag sync settings:', error);
      setError(error.message || 'Failed to load tag sync settings');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Save tag sync settings and trigger immediate sync
   */
  const saveSettings = async () => {
    try {
      setSaving(true);
      setError(null);

      const updateRequest = {
        enabled,
        intervalHours,
      };

      const response = await apiClient.updateTagSyncSettings(updateRequest);
      
      setSettings(response);
      toast.success('Tag sync settings updated successfully');
      
      // Trigger immediate manual tag sync so user doesn't have to wait for schedule
      if (enabled) {
        try {
          toast.loading('Starting initial tag sync...', { id: 'tag-sync' });
          await apiClient.triggerTagSync();
          toast.success('Tag sync completed successfully', { id: 'tag-sync' });
        } catch (syncErr: unknown) {
          const syncError = syncErr as Error & { message?: string };
          console.error('Failed to trigger immediate tag sync:', syncError);
          // Don't fail the save operation, just warn the user
          toast.error('Settings saved, but initial sync failed. It will run on schedule.', { id: 'tag-sync' });
        }
      }
      
      if (onConfigurationChange) {
        onConfigurationChange();
      }
      
    } catch (err: unknown) {
      const error = err as Error & { message?: string };
      console.error('Failed to update tag sync settings:', error);
      const errorMessage = error.message || 'Failed to update tag sync settings';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Reset form to current settings
   */
  const resetForm = () => {
    if (settings) {
      setEnabled(settings.enabled);
      setIntervalHours(settings.intervalHours);
    }
    setError(null);
  };

  /**
   * Check if form has changes
   */
  const hasChanges = () => {
    if (!settings) return false;
    return enabled !== settings.enabled || intervalHours !== settings.intervalHours;
  };

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  if (loading) {
    return (
      <Container>
        <Box textAlign="center" padding="xxl">
          <StatusIndicator type="loading">Loading tag sync settings...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Configure automatic synchronization of EC2 instance tags to DRS source servers"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <Button
                onClick={resetForm}
                disabled={!hasChanges() || saving}
              >
                Reset
              </Button>
              <Button
                variant="primary"
                onClick={saveSettings}
                loading={saving}
                disabled={!hasChanges()}
              >
                Save Changes
              </Button>
            </SpaceBetween>
          }
        >
          Tag Synchronization
        </Header>
      }
    >
      <SpaceBetween size="l">
        {error && (
          <Alert
            type="error"
            dismissible
            onDismiss={() => setError(null)}
            header="Configuration Error"
          >
            {error}
          </Alert>
        )}

        {settings && !settings.enabled && enabled && (
          <Alert
            type="info"
            header="EventBridge Rule Required"
          >
            To enable scheduled tag sync, ensure your CloudFormation stack was deployed with 
            <code>EnableTagSync=true</code>. If the EventBridge rule doesn't exist, 
            redeploy your stack with tag sync enabled.
          </Alert>
        )}

        <ColumnLayout columns={2} variant="text-grid">
          <SpaceBetween size="m">
            <FormField
              label="Scheduled Sync"
              description="Enable automatic tag synchronization on a schedule"
            >
              <Toggle
                checked={enabled}
                onChange={({ detail }) => setEnabled(detail.checked)}
                disabled={saving}
              >
                {enabled ? 'Enabled' : 'Disabled'}
              </Toggle>
            </FormField>

            <FormField
              label="Sync Interval"
              description="How often to synchronize tags automatically"
            >
              <Select
                selectedOption={intervalOptions.find(opt => parseInt(opt.value) === intervalHours) || intervalOptions[2]}
                onChange={({ detail }) => setIntervalHours(parseInt(detail.selectedOption?.value || '4'))}
                options={intervalOptions}
                disabled={!enabled || saving}
              />
            </FormField>
          </SpaceBetween>

          <SpaceBetween size="m">
            {settings && (
              <>
                <Box>
                  <Box variant="awsui-key-label">Current Status</Box>
                  <StatusIndicator type={settings.enabled ? 'success' : 'stopped'}>
                    {settings.enabled ? 'Active' : 'Inactive'}
                  </StatusIndicator>
                </Box>

                <Box>
                  <Box variant="awsui-key-label">Schedule Expression</Box>
                  <Box variant="code">{settings.scheduleExpression}</Box>
                </Box>

                <Box>
                  <Box variant="awsui-key-label">EventBridge Rule</Box>
                  <Box variant="code">{settings.ruleName}</Box>
                </Box>

                {settings.lastModified && (
                  <Box>
                    <Box variant="awsui-key-label">Last Modified</Box>
                    <Box>{new Date(settings.lastModified).toLocaleString()}</Box>
                  </Box>
                )}
              </>
            )}
          </SpaceBetween>
        </ColumnLayout>

        <Alert
          type="info"
          header="About Tag Synchronization"
        >
          <SpaceBetween size="s">
            <Box>
              Scheduled tag sync automatically copies tags from EC2 instances to their corresponding 
              DRS source servers. This ensures that DRS servers maintain up-to-date tags for 
              protection group filtering and recovery planning.
            </Box>
            <Box>
              <strong>Note:</strong> Manual tag sync via the "Sync Tags" button will continue to work 
              regardless of the scheduled sync settings.
            </Box>
          </SpaceBetween>
        </Alert>
      </SpaceBetween>
    </Container>
  );
};