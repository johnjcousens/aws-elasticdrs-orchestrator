import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  FormField,
  Input,
  Select,
  Spinner,
  Alert,
  Container,
} from '@cloudscape-design/components';
import { ServerListItem } from './ServerListItem';
import apiClient from '../services/api';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  };
  selectable: boolean;
}

interface ServerDiscoveryPanelProps {
  region: string;
  selectedServerIds: string[];
  onSelectionChange: (serverIds: string[]) => void;
  currentProtectionGroupId?: string;
}

export const ServerDiscoveryPanel: React.FC<ServerDiscoveryPanelProps> = ({
  region,
  selectedServerIds,
  onSelectionChange,
  currentProtectionGroupId
}) => {
  const [servers, setServers] = useState<DRSServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'available' | 'assigned'>('all');
  const [drsInitialized, setDrsInitialized] = useState(true);

  // Fetch servers
  const fetchServers = useCallback(async (silent = false) => {
    if (!region) return;
    
    if (!silent) setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.listDRSSourceServers(region, currentProtectionGroupId);
      
      if (response.initialized === false) {
        setDrsInitialized(false);
        setError(response.message);
        setServers([]);
      } else {
        setDrsInitialized(true);
        setServers(response.servers || []);
      }
    } catch (err: any) {
      console.error('Error fetching servers:', err);
      if (err.message?.includes('DRS_NOT_INITIALIZED') || err.message?.includes('not initialized')) {
        setDrsInitialized(false);
        setError(err.message);
        setServers([]);
      } else {
        setError('Failed to fetch DRS source servers. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [region]);

  // Initial fetch
  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!region || !drsInitialized) return;
    
    const interval = setInterval(() => {
      fetchServers(true); // Silent refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, [region, drsInitialized, fetchServers]);

  // Filter and search
  const filteredServers = servers.filter(server => {
    // Apply filter
    if (filter === 'available' && !server.selectable) return false;
    if (filter === 'assigned' && server.selectable) return false;
    
    // Apply search
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        server.hostname.toLowerCase().includes(searchLower) ||
        server.sourceServerID.toLowerCase().includes(searchLower) ||
        server.assignedToProtectionGroup?.protectionGroupName.toLowerCase().includes(searchLower)
      );
    }
    
    return true;
  });

  // Handle selection
  const handleToggle = (serverId: string) => {
    const currentIndex = selectedServerIds.indexOf(serverId);
    const newSelected = [...selectedServerIds];
    
    if (currentIndex === -1) {
      newSelected.push(serverId);
    } else {
      newSelected.splice(currentIndex, 1);
    }
    
    onSelectionChange(newSelected);
  };

  const handleSelectAll = () => {
    const selectableServers = filteredServers.filter(s => s.selectable);
    onSelectionChange(selectableServers.map(s => s.sourceServerID));
  };

  const handleDeselectAll = () => {
    onSelectionChange([]);
  };

  if (loading && servers.length === 0) {
    return (
      <Box textAlign="center" padding={{ vertical: 'xxl' }}>
        <Spinner size="large" />
        <div style={{ marginTop: '16px' }}>Discovering servers in {region}...</div>
      </Box>
    );
  }

  if (!drsInitialized) {
    return (
      <Alert type="warning" header="DRS Not Initialized">
        {error || `DRS is not initialized in ${region}. Please initialize DRS before creating Protection Groups.`}
      </Alert>
    );
  }

  if (servers.length === 0) {
    return (
      <Alert type="info" header="No Servers Found">
        No DRS source servers found in {region}. Add servers to DRS before creating Protection Groups.
      </Alert>
    );
  }

  const availableCount = servers.filter(s => s.selectable).length;
  const assignedCount = servers.filter(s => !s.selectable).length;

  return (
    <div>
      {/* Search and Filter */}
      <div style={{ display: 'flex', marginBottom: '16px' }}>
        <div style={{ flex: 1, marginRight: '16px' }}>
          <FormField>
            <Input
              type="search"
              placeholder="Search by hostname, server ID, or Protection Group..."
              value={searchTerm}
              onChange={({ detail }) => setSearchTerm(detail.value)}
            />
          </FormField>
        </div>
        <div style={{ minWidth: '150px' }}>
          <FormField label="Filter">
            <Select
              selectedOption={{ label: filter === 'all' ? 'All Servers' : filter === 'available' ? 'Available' : 'Assigned', value: filter }}
              onChange={({ detail }) => setFilter(detail.selectedOption.value as any)}
              options={[
                { label: 'All Servers', value: 'all' },
                { label: 'Available', value: 'available' },
                { label: 'Assigned', value: 'assigned' }
              ]}
            />
          </FormField>
        </div>
      </div>

      {/* Server Count */}
      <div style={{ display: 'flex', marginBottom: '16px' }}>
        <div style={{ flex: 1, fontSize: '14px', color: '#5f6b7a' }}>
          Total: {servers.length} | Available: {availableCount} | Assigned: {assignedCount}
        </div>
        <div>
          <Button
            variant="inline-link"
            onClick={handleSelectAll}
            disabled={availableCount === 0}
          >
            Select All Available
          </Button>
          <Button
            variant="inline-link"
            onClick={handleDeselectAll}
            disabled={selectedServerIds.length === 0}
          >
            Deselect All
          </Button>
        </div>
      </div>

      {/* Server List */}
      <Container>
        <div style={{ maxHeight: '400px', overflow: 'auto', border: '1px solid #e9ebed', borderRadius: '8px' }}>
          {filteredServers.map((server) => (
            <ServerListItem
              key={server.sourceServerID}
              server={server}
              selected={selectedServerIds.includes(server.sourceServerID)}
              onToggle={() => handleToggle(server.sourceServerID)}
            />
          ))}
        </div>
      </Container>

      {/* Selection Count */}
      <div style={{ fontSize: '14px', color: '#5f6b7a', marginTop: '8px' }}>
        {selectedServerIds.length} of {availableCount} available servers selected
      </div>
    </div>
  );
};
