import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  List,
  Button
} from '@mui/material';
import { Search as SearchIcon } from '@mui/icons-material';
import { ServerListItem } from './ServerListItem';
import { apiClient } from '../services/api';

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
}

export const ServerDiscoveryPanel: React.FC<ServerDiscoveryPanelProps> = ({
  region,
  selectedServerIds,
  onSelectionChange
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
      const response = await apiClient.get(`/drs/source-servers?region=${region}`);
      
      if (response.data.initialized === false) {
        setDrsInitialized(false);
        setError(response.data.message);
        setServers([]);
      } else {
        setDrsInitialized(true);
        setServers(response.data.servers || []);
      }
    } catch (err: any) {
      console.error('Error fetching servers:', err);
      if (err.response?.data?.error === 'DRS_NOT_INITIALIZED') {
        setDrsInitialized(false);
        setError(err.response.data.message);
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
      <Box display="flex" justifyContent="center" alignItems="center" p={4}>
        <CircularProgress />
        <Typography ml={2}>Discovering servers in {region}...</Typography>
      </Box>
    );
  }

  if (!drsInitialized) {
    return (
      <Alert severity="warning">
        <Typography variant="subtitle1" gutterBottom>
          DRS Not Initialized
        </Typography>
        <Typography variant="body2">
          {error || `DRS is not initialized in ${region}. Please initialize DRS before creating Protection Groups.`}
        </Typography>
      </Alert>
    );
  }

  if (servers.length === 0) {
    return (
      <Alert severity="info">
        <Typography variant="subtitle1" gutterBottom>
          No Servers Found
        </Typography>
        <Typography variant="body2">
          No DRS source servers found in {region}. Add servers to DRS before creating Protection Groups.
        </Typography>
      </Alert>
    );
  }

  const availableCount = servers.filter(s => s.selectable).length;
  const assignedCount = servers.filter(s => !s.selectable).length;

  return (
    <Box>
      {/* Search and Filter */}
      <Box display="flex" gap={2} mb={2}>
        <TextField
          fullWidth
          placeholder="Search by hostname, server ID, or Protection Group..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
        />
        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Filter</InputLabel>
          <Select
            value={filter}
            label="Filter"
            onChange={(e) => setFilter(e.target.value as any)}
          >
            <MenuItem value="all">All Servers</MenuItem>
            <MenuItem value="available">Available</MenuItem>
            <MenuItem value="assigned">Assigned</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Server Count */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="body2" color="text.secondary">
          Total: {servers.length} | Available: {availableCount} | Assigned: {assignedCount}
        </Typography>
        <Box>
          <Button
            size="small"
            onClick={handleSelectAll}
            disabled={availableCount === 0}
          >
            Select All Available
          </Button>
          <Button
            size="small"
            onClick={handleDeselectAll}
            disabled={selectedServerIds.length === 0}
            sx={{ ml: 1 }}
          >
            Deselect All
          </Button>
        </Box>
      </Box>

      {/* Server List */}
      <Paper variant="outlined">
        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          {filteredServers.map((server) => (
            <ServerListItem
              key={server.sourceServerID}
              server={server}
              selected={selectedServerIds.includes(server.sourceServerID)}
              onToggle={() => handleToggle(server.sourceServerID)}
            />
          ))}
        </List>
      </Paper>

      {/* Selection Count */}
      <Typography variant="body2" color="text.secondary" mt={1}>
        {selectedServerIds.length} of {availableCount} available servers selected
      </Typography>
    </Box>
  );
};
