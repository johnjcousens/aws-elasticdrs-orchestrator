/**
 * Server Selector Component
 * 
 * Allows selection of source servers for wave configuration.
 * Fetches servers from protection group and displays with checkboxes.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  SpaceBetween,
  Input,
  Checkbox,
  Button,
  Alert,
  Badge,
} from '@cloudscape-design/components';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';
import apiClient from '../services/api';

interface ServerSelectorProps {
  protectionGroupId: string;  // Backward compatibility - single PG
  protectionGroupIds?: string[];  // Multi-PG support
  selectedServerIds: string[];
  onChange: (serverIds: string[]) => void;
  readonly?: boolean;
}

interface Server {
  id: string;
  hostname?: string;
  tags?: Record<string, string>;
  protectionGroupId?: string;  // Track which PG this server belongs to
  protectionGroupName?: string;  // Display friendly PG name
}

/**
 * Server Selector Component
 * 
 * Displays available servers from a protection group and allows selection.
 */
export const ServerSelector: React.FC<ServerSelectorProps> = ({
  protectionGroupId,
  protectionGroupIds,
  selectedServerIds,
  onChange,
  readonly = false,
}) => {
  // Defensive: ensure selectedServerIds is always an array
  const safeSelectedServerIds = selectedServerIds || [];
  
  // Use protectionGroupIds if provided, otherwise fall back to single protectionGroupId
  const pgIds = protectionGroupIds && protectionGroupIds.length > 0 
    ? protectionGroupIds 
    : (protectionGroupId ? [protectionGroupId] : []);
  
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (pgIds.length > 0) {
      fetchServers();
    }
  }, [JSON.stringify(pgIds)]);  // Watch for changes in the PG IDs array

  const fetchServers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch servers from all selected Protection Groups
      const allServers: Server[] = [];
      
      for (const pgId of pgIds) {
        try {
          const response = await apiClient.listDRSSourceServers(
            'us-east-1',
            undefined, // currentProtectionGroupId - not editing a PG
            pgId // filterByProtectionGroup - show only this PG's servers
          );
          
          if (!response.initialized) {
            setError('DRS is not initialized in us-east-1. Please initialize DRS first.');
            setServers([]);
            return;
          }
          
          // Transform DRS response to Server format with PG tracking
          const drsServers: Server[] = response.servers.map((s: any) => ({
            id: s.sourceServerID,
            hostname: s.hostname,
            protectionGroupId: pgId,
            protectionGroupName: s.assignedToProtectionGroup?.protectionGroupName || 'Unknown PG',
            tags: {
              'Protection Group': s.assignedToProtectionGroup?.protectionGroupName || 'Unknown',
              State: s.state,
              ReplicationState: s.replicationState
            }
          }));
          
          allServers.push(...drsServers);
        } catch (pgError: any) {
          console.error(`Failed to fetch servers for PG ${pgId}:`, pgError);
          // Continue with other PGs even if one fails
        }
      }
      
      setServers(allServers);
    } catch (err: any) {
      setError(err.message || 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (serverId: string) => {
    if (readonly) return;

    const newSelection = safeSelectedServerIds.includes(serverId)
      ? safeSelectedServerIds.filter(id => id !== serverId)
      : [...safeSelectedServerIds, serverId];
    
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
      <Alert type="info">
        No servers found in this protection group. Servers will be automatically discovered when they match the group's tag filters.
      </Alert>
    );
  }

  return (
    <SpaceBetween size="m">
      {/* Header with selection info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
          {safeSelectedServerIds.length} of {servers.length} servers selected
        </span>
        {!readonly && (
          <SpaceBetween direction="horizontal" size="xs">
            <Button
              onClick={handleSelectAll}
              disabled={safeSelectedServerIds.length === filteredServers.length}
            >
              Select All
            </Button>
            <Button
              onClick={handleDeselectAll}
              disabled={safeSelectedServerIds.length === 0}
            >
              Deselect All
            </Button>
          </SpaceBetween>
        )}
      </div>

      {/* Search field */}
      {!readonly && servers.length > 5 && (
        <Input
          type="search"
          placeholder="Search servers by hostname, ID, or tags..."
          value={searchTerm}
          onChange={({ detail }) => setSearchTerm(detail.value)}
        />
      )}

      {/* Server list */}
      <Container>
        <div style={{ maxHeight: '400px', overflow: 'auto' }}>
          {filteredServers.length === 0 ? (
            <Box textAlign="center" padding="l">
              <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
                No servers match your search
              </span>
            </Box>
          ) : (
            <SpaceBetween size="s">
              {filteredServers.map((server) => (
                <div key={server.id} style={{ padding: '8px 0' }}>
                  <Checkbox
                    checked={safeSelectedServerIds.includes(server.id)}
                    onChange={() => handleToggle(server.id)}
                    disabled={readonly}
                  >
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                        {server.hostname || server.id}
                      </div>
                      {server.tags && Object.keys(server.tags).length > 0 && (
                        <SpaceBetween direction="horizontal" size="xs">
                          {Object.entries(server.tags).map(([key, value]) => (
                            <Badge key={key} color="blue">
                              {key}: {value}
                            </Badge>
                          ))}
                        </SpaceBetween>
                      )}
                    </div>
                  </Checkbox>
                </div>
              ))}
            </SpaceBetween>
          )}
        </div>
      </Container>
    </SpaceBetween>
  );
};
