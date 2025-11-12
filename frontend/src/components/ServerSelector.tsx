/**
 * Server Selector Component
 * 
 * Allows selection of source servers for wave configuration.
 * Fetches servers from protection group and displays with checkboxes.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  FormControl,
  FormGroup,
  FormControlLabel,
  Checkbox,
  TextField,
  Typography,
  Paper,
  Stack,
  Chip,
  Alert,
} from '@mui/material';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';
import apiClient from '../services/api';

interface ServerSelectorProps {
  protectionGroupId: string;
  selectedServerIds: string[];
  onChange: (serverIds: string[]) => void;
  readonly?: boolean;
}

interface Server {
  id: string;
  hostname?: string;
  tags?: Record<string, string>;
}

/**
 * Server Selector Component
 * 
 * Displays available servers from a protection group and allows selection.
 */
export const ServerSelector: React.FC<ServerSelectorProps> = ({
  protectionGroupId,
  selectedServerIds,
  onChange,
  readonly = false,
}) => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (protectionGroupId) {
      fetchServers();
    }
  }, [protectionGroupId]);

  const fetchServers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Call DRS API with filtering by Protection Group
      // This ensures we only get servers that belong to this PG
      const response = await apiClient.listDRSSourceServers(
        'us-east-1',
        undefined, // currentProtectionGroupId - not editing a PG
        protectionGroupId // filterByProtectionGroup - show only this PG's servers
      );
      
      if (!response.initialized) {
        setError('DRS is not initialized in us-east-1. Please initialize DRS first.');
        setServers([]);
        return;
      }
      
      // Transform DRS response to Server format
      // All servers returned are from this PG and selectable
      const drsServers: Server[] = response.servers.map((s: any) => ({
        id: s.sourceServerID,
        hostname: s.hostname,
        tags: {
          State: s.state,
          ReplicationState: s.replicationState
        }
      }));
      
      setServers(drsServers);
    } catch (err: any) {
      setError(err.message || 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (serverId: string) => {
    if (readonly) return;

    const newSelection = selectedServerIds.includes(serverId)
      ? selectedServerIds.filter(id => id !== serverId)
      : [...selectedServerIds, serverId];
    
    onChange(newSelection);
  };

  const handleSelectAll = () => {
    if (readonly) return;
    onChange(filteredServers.map(s => s.id));
  };

  const handleDeselectAll = () => {
    if (readonly) return;
    onChange([]);
  };

  // Filter servers based on search term
  const filteredServers = servers.filter(server => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      server.id.toLowerCase().includes(term) ||
      server.hostname?.toLowerCase().includes(term) ||
      Object.values(server.tags || {}).some(tag => tag.toLowerCase().includes(term))
    );
  });

  if (loading) {
    return <LoadingState message="Loading servers..." />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={fetchServers} />;
  }

  if (servers.length === 0) {
    return (
      <Alert severity="info">
        No servers found in this protection group. Servers will be automatically discovered when they match the group's tag filters.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header with selection info */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {selectedServerIds.length} of {servers.length} servers selected
        </Typography>
        {!readonly && (
          <Stack direction="row" spacing={1}>
            <Chip
              label="Select All"
              size="small"
              onClick={handleSelectAll}
              clickable
              disabled={selectedServerIds.length === filteredServers.length}
            />
            <Chip
              label="Deselect All"
              size="small"
              onClick={handleDeselectAll}
              clickable
              disabled={selectedServerIds.length === 0}
            />
          </Stack>
        )}
      </Stack>

      {/* Search field */}
      {!readonly && servers.length > 5 && (
        <TextField
          fullWidth
          size="small"
          placeholder="Search servers by hostname, ID, or tags..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ mb: 2 }}
        />
      )}

      {/* Server list */}
      <Paper variant="outlined" sx={{ maxHeight: 400, overflow: 'auto', p: 2 }}>
        {filteredServers.length === 0 ? (
          <Typography variant="body2" color="text.secondary" textAlign="center">
            No servers match your search
          </Typography>
        ) : (
          <FormControl component="fieldset" fullWidth>
            <FormGroup>
              {filteredServers.map((server) => (
                <FormControlLabel
                  key={server.id}
                  control={
                    <Checkbox
                      checked={selectedServerIds.includes(server.id)}
                      onChange={() => handleToggle(server.id)}
                      disabled={readonly}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2">
                        {server.hostname || server.id}
                      </Typography>
                      {server.tags && Object.keys(server.tags).length > 0 && (
                        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} flexWrap="wrap">
                          {Object.entries(server.tags).map(([key, value]) => (
                            <Chip
                              key={key}
                              label={`${key}: ${value}`}
                              size="small"
                              variant="outlined"
                              sx={{ mb: 0.5 }}
                            />
                          ))}
                        </Stack>
                      )}
                    </Box>
                  }
                  sx={{ mb: 1 }}
                />
              ))}
            </FormGroup>
          </FormControl>
        )}
      </Paper>
    </Box>
  );
};
