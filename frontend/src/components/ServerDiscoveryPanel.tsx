import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Checkbox,
  FormField,
  Input,
  Select,
  Spinner,
  Alert,
  Container,
} from '@cloudscape-design/components';
import { ServerListItem } from './ServerListItem';
import apiClient from '../services/api';
import type { DRSServer } from '../types';


interface ServerDiscoveryPanelProps {
  region: string;
  selectedServerIds: string[];
  onSelectionChange: (serverIds: string[]) => void;
  currentProtectionGroupId?: string;
  pauseRefresh?: boolean;  // Pause auto-refresh when user is configuring other settings
}

export const ServerDiscoveryPanel: React.FC<ServerDiscoveryPanelProps> = ({
  region,
  selectedServerIds,
  onSelectionChange,
  currentProtectionGroupId,
  pauseRefresh = false,
}) => {
  const [servers, setServers] = useState<DRSServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'available' | 'assigned'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'hostname' | 'ip'>('name');
  const [drsInitialized, setDrsInitialized] = useState(true);

  // Fetch servers
  const fetchServers = useCallback(async (silent = false) => {
    if (!region) return;
    
    if (!silent) setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.listDRSSourceServers(region, currentProtectionGroupId);
      
      // Check if DRS is initialized - response may have 'initialized' field or just servers
      const responseAny = response as { initialized?: boolean; message?: string; servers: typeof response.servers };
      if (responseAny.initialized === false) {
        setDrsInitialized(false);
        setError(responseAny.message || 'DRS not initialized');
        setServers([]);
      } else {
        setDrsInitialized(true);
        // Map servers to ensure required fields have defaults
        const mappedServers: DRSServer[] = (response.servers || []).map(s => ({
          ...s,
          state: s.state || 'UNKNOWN',
          replicationState: s.replicationState || 'UNKNOWN',
          lagDuration: s.lagDuration || '',
          lastSeen: s.lastSeen || '',
          assignedToProtectionGroup: s.assignedToProtectionGroup || null,
          selectable: s.selectable ?? true,
        }));
        setServers(mappedServers);
      }
    } catch (err: unknown) {
      console.error('Error fetching servers:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      if (errorMessage.includes('DRS_NOT_INITIALIZED') || errorMessage.includes('not initialized')) {
        setDrsInitialized(false);
        setError(errorMessage);
        setServers([]);
      } else {
        setError('Failed to fetch DRS source servers. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }, [region, currentProtectionGroupId]);

  // Initial fetch
  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  // Auto-refresh every 30 seconds (paused when user is configuring launch settings)
  useEffect(() => {
    if (!region || !drsInitialized || pauseRefresh) return;
    
    const interval = setInterval(() => {
      fetchServers(true); // Silent refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, [region, drsInitialized, fetchServers, pauseRefresh]);

  // Filter, search, and sort
  const filteredServers = servers
    .filter(server => {
      // Apply filter
      if (filter === 'available' && !server.selectable) return false;
      if (filter === 'assigned' && server.selectable) return false;
      
      // Apply search - include all new fields
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        return (
          server.hostname.toLowerCase().includes(searchLower) ||
          server.sourceServerID.toLowerCase().includes(searchLower) ||
          server.nameTag?.toLowerCase().includes(searchLower) ||
          server.sourceInstanceId?.toLowerCase().includes(searchLower) ||
          server.sourceIp?.toLowerCase().includes(searchLower) ||
          server.sourceRegion?.toLowerCase().includes(searchLower) ||
          server.sourceAccount?.toLowerCase().includes(searchLower) ||
          server.assignedToProtectionGroup?.protectionGroupName.toLowerCase().includes(searchLower)
        );
      }
      
      return true;
    })
    .sort((a, b) => {
      // Sort by selected field
      let aVal = '';
      let bVal = '';
      
      switch (sortBy) {
        case 'name':
          aVal = (a.nameTag || a.hostname || '').toLowerCase();
          bVal = (b.nameTag || b.hostname || '').toLowerCase();
          break;
        case 'hostname':
          aVal = (a.hostname || '').toLowerCase();
          bVal = (b.hostname || '').toLowerCase();
          break;
        case 'ip':
          aVal = (a.sourceIp || '').toLowerCase();
          bVal = (b.sourceIp || '').toLowerCase();
          break;
      }
      
      return aVal.localeCompare(bVal);
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
        {error || `AWS Elastic Disaster Recovery (DRS) is not initialized in ${region}. Go to the DRS Console and complete the initialization wizard before creating Protection Groups.`}
      </Alert>
    );
  }

  if (servers.length === 0) {
    return (
      <Alert type="info" header="No Replicating Servers">
        DRS is initialized in {region}, but no source servers are replicating yet. Install the AWS Replication Agent on your source servers to begin replication before creating Protection Groups.
      </Alert>
    );
  }

  const availableCount = servers.filter(s => s.selectable).length;
  const assignedCount = servers.filter(s => !s.selectable).length;

  return (
    <div>
      {/* Search, Filter, and Sort */}
      <div style={{ display: 'flex', marginBottom: '16px', gap: '16px' }}>
        <div style={{ flex: 1 }}>
          <FormField>
            <Input
              type="search"
              placeholder="Search by name, hostname, instance ID, IP..."
              value={searchTerm}
              onChange={({ detail }) => setSearchTerm(detail.value)}
            />
          </FormField>
        </div>
        <div style={{ minWidth: '140px' }}>
          <FormField label="Filter">
            <Select
              selectedOption={{ label: filter === 'all' ? 'All Servers' : filter === 'available' ? 'Available' : 'Assigned', value: filter }}
              onChange={({ detail }) => setFilter(detail.selectedOption?.value as 'all' | 'available' | 'assigned' || 'all')}
              options={[
                { label: 'All Servers', value: 'all' },
                { label: 'Available', value: 'available' },
                { label: 'Assigned', value: 'assigned' }
              ]}
            />
          </FormField>
        </div>
        <div style={{ minWidth: '140px' }}>
          <FormField label="Sort by">
            <Select
              selectedOption={{ 
                label: sortBy === 'name' ? 'Name Tag' : sortBy === 'hostname' ? 'Hostname' : 'IP Address', 
                value: sortBy 
              }}
              onChange={({ detail }) => setSortBy(detail.selectedOption?.value as 'name' | 'hostname' | 'ip' || 'name')}
              options={[
                { label: 'Name Tag', value: 'name' },
                { label: 'Hostname', value: 'hostname' },
                { label: 'IP Address', value: 'ip' }
              ]}
            />
          </FormField>
        </div>
      </div>

      {/* Server Count */}
      <div style={{ fontSize: '14px', color: '#5f6b7a', marginBottom: '8px' }}>
        Total: {servers.length} | Available: {availableCount} | Assigned: {assignedCount}
      </div>

      {/* Server List */}
      <Container>
        <div style={{ border: '1px solid #e9ebed', borderRadius: '8px' }}>
          {/* Select All Header */}
          <div style={{ 
            padding: '12px 16px', 
            borderBottom: '1px solid #e9ebed',
            backgroundColor: '#fafafa'
          }}>
            <Checkbox
              checked={selectedServerIds.length > 0 && selectedServerIds.length === filteredServers.filter(s => s.selectable).length}
              indeterminate={selectedServerIds.length > 0 && selectedServerIds.length < filteredServers.filter(s => s.selectable).length}
              onChange={({ detail }) => {
                // Prevent any form submission behavior
                if (detail.checked) {
                  handleSelectAll();
                } else {
                  handleDeselectAll();
                }
              }}
              disabled={availableCount === 0}
            >
              <span style={{ fontWeight: 600 }}>
                Select All ({selectedServerIds.length} of {availableCount} selected)
              </span>
            </Checkbox>
          </div>
          
          {/* Server Items */}
          <div style={{ maxHeight: '400px', overflow: 'auto' }}>
            {filteredServers.map((server) => (
              <ServerListItem
                key={server.sourceServerID}
                server={server}
                selected={selectedServerIds.includes(server.sourceServerID)}
                onToggle={() => handleToggle(server.sourceServerID)}
              />
            ))}
          </div>
        </div>
      </Container>
    </div>
  );
};
