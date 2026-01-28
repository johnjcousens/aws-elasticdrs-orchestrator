/**
 * Server Selector Component
 * 
 * Allows selection of source servers for wave configuration.
 * Fetches servers from protection group and displays with checkboxes.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
  protectionGroups?: Array<{
    protectionGroupId: string;
    groupName?: string;
    sourceServerIds?: string[];
    serverSelectionTags?: Record<string, string>;
    region?: string;
  }>;  // Full PG objects to access sourceServerIds and region
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
  protectionGroups = [],
}) => {
  // Defensive: ensure selectedServerIds is always an array
  const safeSelectedServerIds = selectedServerIds || [];
  
  // Use protectionGroupIds if provided, otherwise fall back to single protectionGroupId
  // Wrapped in useMemo to prevent dependency changes on every render
  const pgIds = useMemo(() => {
    return protectionGroupIds && protectionGroupIds.length > 0 
      ? protectionGroupIds 
      : (protectionGroupId ? [protectionGroupId] : []);
  }, [protectionGroupIds, protectionGroupId]);
  
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchServers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Fetch servers from all selected Protection Groups
      const allServers: Server[] = [];
      
      for (const pgId of pgIds) {
        try {
          // Find the Protection Group object to check if it's server-based or tag-based
          const pg = protectionGroups.find(p => p.protectionGroupId === pgId);
          
          // If PG has sourceServerIds, it's server-based - fetch those specific servers
          if (pg && pg.sourceServerIds && pg.sourceServerIds.length > 0) {
            // Server-based Protection Group - fetch specific servers by ID
            const region = pg.region || 'us-east-1'; // Use PG's region
            const response = await apiClient.listDRSSourceServers(
              region,
              undefined, // currentProtectionGroupId
              undefined  // Don't filter by PG - we want all servers to find our specific IDs
            );
            
            // Check if DRS is initialized
            const responseAny = response as { initialized?: boolean };
            if (responseAny.initialized === false) {
              setError(`DRS is not initialized in ${region}. Please initialize DRS first.`);
              setServers([]);
              return;
            }
            
            // Filter to only the servers in this PG's sourceServerIds
            const serversList = Array.isArray(response.servers) ? response.servers : [];
            const pgServers = serversList.filter(s => 
              pg.sourceServerIds?.includes(s.sourceServerID)
            );
            
            const drsServers: Server[] = pgServers.map((s) => ({
              id: s.sourceServerID,
              hostname: s.hostname,
              protectionGroupId: pgId,
              protectionGroupName: pg.groupName || 'Unknown PG',
              tags: {
                'Protection Group': pg.groupName || 'Unknown',
                State: s.state || 'UNKNOWN',
                ReplicationState: s.replicationState || 'UNKNOWN'
              }
            }));
            
            allServers.push(...drsServers);
          } else {
            // Tag-based Protection Group - fetch servers filtered by PG
            const response = await apiClient.listDRSSourceServers(
              'us-east-1',
              undefined, // currentProtectionGroupId - not editing a PG
              pgId // filterByProtectionGroup - show only this PG's servers
            );
            
            // Check if DRS is initialized
            const responseAny = response as { initialized?: boolean };
            if (responseAny.initialized === false) {
              setError('DRS is not initialized in us-east-1. Please initialize DRS first.');
              setServers([]);
              return;
            }
            
            // Transform DRS response to Server format with PG tracking
            const serversList = Array.isArray(response.servers) ? response.servers : [];
            const drsServers: Server[] = serversList.map((s) => ({
              id: s.sourceServerID,
              hostname: s.hostname,
              protectionGroupId: pgId,
              protectionGroupName: s.assignedToProtectionGroup?.protectionGroupName || 'Unknown PG',
              tags: {
                'Protection Group': s.assignedToProtectionGroup?.protectionGroupName || 'Unknown',
                State: s.state || 'UNKNOWN',
                ReplicationState: s.replicationState || 'UNKNOWN'
              }
            }));
            
            allServers.push(...drsServers);
          }
        } catch (pgError) {
          console.error('Failed to fetch servers for PG:', pgId, pgError);
          // Continue with other PGs even if one fails
        }
      }
      
      setServers(allServers);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  }, [pgIds, protectionGroups]);

  useEffect(() => {
    if (pgIds.length > 0) {
      fetchServers();
    }
  }, [pgIds, fetchServers]);

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
    // Check if any selected PGs are server-based
    const selectedPGs = protectionGroups.filter(pg => pgIds.includes(pg.protectionGroupId));
    const hasServerBasedPGs = selectedPGs.some(pg => pg.sourceServerIds && pg.sourceServerIds.length > 0);
    
    if (hasServerBasedPGs) {
      return (
        <Alert type="warning">
          No servers found. The selected Protection Group has specific servers configured, but they could not be retrieved. 
          This may indicate the servers no longer exist in DRS or there's a connectivity issue.
        </Alert>
      );
    }
    
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
              onClick={(e) => { e.preventDefault(); handleSelectAll(); }}
              disabled={safeSelectedServerIds.length === filteredServers.length}
            >
              Select All
            </Button>
            <Button
              onClick={(e) => { e.preventDefault(); handleDeselectAll(); }}
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
          onChange={({ detail }: { detail: { value: string } }) => setSearchTerm(detail.value)}
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
                    onChange={() => {
                      // Prevent any form submission behavior
                      handleToggle(server.id);
                    }}
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
