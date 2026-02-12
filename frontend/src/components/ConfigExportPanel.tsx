/**
 * Configuration Export Panel
 * 
 * Handles exporting Protection Groups and Recovery Plans to JSON file.
 */

import React, { useState } from 'react';
import {
  SpaceBetween,
  Button,
  Alert,
  Box,
  TextContent,
} from '@cloudscape-design/components';
import { useApi } from '../contexts/ApiContext';
import toast from 'react-hot-toast';

interface ConfigExportPanelProps {
  onExportComplete?: () => void;
}

export const ConfigExportPanel: React.FC<ConfigExportPanelProps> = ({
  onExportComplete,
}) => {
  const { exportConfiguration } = useApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);

    try {
      const config = await exportConfiguration();
      
      // Count servers with custom configs
      let serversWithCustomConfig = 0;
      if (config.protectionGroups) {
        config.protectionGroups.forEach((group: any) => {
          if (group.servers && Array.isArray(group.servers)) {
            serversWithCustomConfig += group.servers.length;
          }
        });
      }
      
      // Generate filename with timestamp
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
      const sanitizedTimestamp = String(timestamp).replace(/[^a-zA-Z0-9-]/g, '');
      const filename = `drs-orchestration-config-${sanitizedTimestamp}.json`;
      
      // Create blob and trigger download
      const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.setAttribute('rel', 'noopener noreferrer');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      const message = serversWithCustomConfig > 0 
        ? `Configuration exported successfully (includes ${serversWithCustomConfig} server${serversWithCustomConfig === 1 ? '' : 's'} with custom configs)`
        : 'Configuration exported successfully';
      toast.success(message);
      onExportComplete?.();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to export configuration';
      setError(message);
      toast.error('Failed to export configuration');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SpaceBetween size="l">
      <TextContent>
        <p>
          Export all Protection Groups and Recovery Plans to a JSON file. 
          This file can be used to backup your configuration or migrate to another environment.
        </p>
        <p>
          The export includes:
        </p>
        <ul>
          <li>All Protection Groups with server selection settings</li>
          <li>All Recovery Plans with wave configurations</li>
          <li>Account context (account ID, assume role name)</li>
          <li>Launch configuration settings (group defaults)</li>
          <li>Per-server launch configurations (custom overrides)</li>
          <li>Static private IP assignments</li>
        </ul>
      </TextContent>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box>
        <Button
          variant="primary"
          loading={loading}
          onClick={handleExport}
          iconName="download"
        >
          Export Configuration
        </Button>
      </Box>
    </SpaceBetween>
  );
};
