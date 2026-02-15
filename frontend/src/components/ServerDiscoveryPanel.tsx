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
  SpaceBetween,
} from '@cloudscape-design/components';
import { ServerListItem } from './ServerListItem';
import { useAccount } from '../contexts/AccountContext';
import apiClient from '../services/api';
import type { DRSServer, RegionStatus } from '../types';
import { getRegionStatusGuidance, isDrsUnavailable } from '../types/region-status';


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
  const { getCurrentAccountId } = useAccount();
  const [servers, setServers] = useState<DRSServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<'all' | 'available' | 'assigned'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'hostname' | 'ip'>('name');
  const [regionStatus, setRegionStatus] = useState<RegionStatus>('ACTIVE');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch servers
  const fetchServers = useCallback(async (silent = false) => {
    if (!region) return;
    
    const accountId = getCurrentAccountId();
    if (!accountId) return;
    
    if (!silent) setLoading(true);
    setError(null);
    setErrorMessage(null);
    
    try {
      const response = await apiClient.listDRSSourceServers(region, accountId, currentProtectionGroupId);
      
      // Check response structure for status information
      const responseAny = response as { 
        initialized?: boolean; 
        message?: string; 
        status?: RegionStatus;
        errorMessage?: string;
        servers: typeof response.servers;
      };
      
      // Handle new status-based response
      if (responseAny.status && responseAny.status !== 'ACTIVE') {
        setRegionStatus(responseAny.status);
        setErrorMessage(responseAny.errorMessage || responseAny.message || null);
        setServers([]);
      } 
      // Handle legacy initialized field for backward compatibility
      else if (responseAny.initialized === false) {
        setRegionStatus('NOT_INITIALIZED');
        setErrorMessage(responseAny.message || null);
        setServers([]);
      } 
      // Success case
      else {
        setRegionStatus('ACTIVE');
        setErrorMessage(null);
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
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      
      // Try to extract status from error message
      let detectedStatus: RegionStatus = 'ERROR';
      
      if (errorMsg.includes('NOT_INITIALIZED') || errorMsg.includes('not initialized')) {
        detectedStatus = 'NOT_INITIALIZED';
      } else if (errorMsg.includes('IAM_PERMISSION_DENIED') || errorMsg.includes('not authorized')) {
        detectedStatus = 'IAM_PERMISSION_DENIED';
      } else if (errorMsg.includes('SCP_DENIED') || errorMsg.includes('service control policy')) {
        detectedStatus = 'SCP_DENIED';
      } else if (errorMsg.includes('REGION_NOT_ENABLED') || errorMsg.includes('not enabled')) {
        detectedStatus = 'REGION_NOT_ENABLED';
      } else if (errorMsg.includes('REGION_NOT_OPTED_IN') || errorMsg.includes('not opted')) {
        detectedStatus = 'REGION_NOT_OPTED_IN';
      } else if (errorMsg.includes('THROTTLED') || errorMsg.includes('rate limit')) {
        detectedStatus = 'THROTTLED';
      } else if (errorMsg.includes('ENDPOINT_UNREACHABLE') || errorMsg.includes('unreachable')) {
        detectedStatus = 'ENDPOINT_UNREACHABLE';
      }
      
      setRegionStatus(detectedStatus);
      setErrorMessage(errorMsg);
      setServers([]);
      setError('Failed to fetch DRS source servers. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [region, currentProtectionGroupId, getCurrentAccountId]);

  // Initial fetch
  useEffect(() => {
    fetchServers();
  }, [fetchServers]);

  // Auto-refresh every 30 seconds (paused when user is configuring launch settings or DRS unavailable)
  useEffect(() => {
    if (!region || isDrsUnavailable(regionStatus) || pauseRefresh) return;
    
    const interval = setInterval(() => {
      fetchServers(true); // Silent refresh
    }, 30000);
    
    return () => clearInterval(interval);
  }, [region, regionStatus, fetchServers, pauseRefresh]);

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

  // Display region status error with specific guidance
  if (isDrsUnavailable(regionStatus)) {
    const guidance = getRegionStatusGuidance(regionStatus, region, errorMessage || undefined);
    
    return (
      <Alert 
        type={guidance.severity} 
        header={guidance.title}
      >
        <SpaceBetween size="m">
          <div>{guidance.message}</div>
          
          {errorMessage && errorMessage !== guidance.message && (
            <Box variant="code">
              <strong>Error Details:</strong> {errorMessage}
            </Box>
          )}
          
          {guidance.actionable && guidance.actions && guidance.actions.length > 0 && (
            <div>
              <strong>Next Steps:</strong>
              <ul style={{ marginTop: '8px', marginBottom: '0' }}>
                {guidance.actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>
          )}
        </SpaceBetween>
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
              onChange={({ detail }: { detail: { value: string } }) => setSearchTerm(detail.value)}
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
