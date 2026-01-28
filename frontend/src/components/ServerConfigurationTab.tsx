/**
 * ServerConfigurationTab Component
 * 
 * Displays a table of servers in a protection group with their configuration status.
 * Allows users to configure per-server launch template settings.
 */

import React, { useState, useMemo } from 'react';
import {
  Table,
  Box,
  Button,
  Select,
  SpaceBetween,
  Header,
  SelectProps,
} from '@cloudscape-design/components';
import { ServerConfigBadge } from './ServerConfigBadge';
import { ServerLaunchConfigDialog } from './ServerLaunchConfigDialog';
import type {
  ResolvedServer,
  LaunchConfig,
  ServerLaunchConfig,
} from '../types';

export interface ServerConfigurationTabProps {
  /** Protection group ID */
  protectionGroupId: string;
  /** List of resolved servers in the protection group */
  servers: ResolvedServer[];
  /** Protection group default launch configuration */
  groupDefaults: LaunchConfig;
  /** Map of server-specific configurations (key: sourceServerId) */
  serverConfigs: Map<string, ServerLaunchConfig>;
  /** AWS region for the protection group */
  region: string;
  /** Callback when server configuration changes */
  onConfigChange: (serverId: string, config: ServerLaunchConfig | null) => void;
  /** Loading state */
  loading?: boolean;
}

type FilterOption = 'all' | 'custom' | 'default';

const FILTER_OPTIONS: SelectProps.Option[] = [
  { label: 'All Servers', value: 'all' },
  { label: 'Custom Only', value: 'custom' },
  { label: 'Default Only', value: 'default' },
];

/**
 * ServerConfigurationTab Component
 * 
 * Provides a table view of servers with configuration management capabilities.
 * 
 * Features:
 * - Table view of all servers in protection group
 * - Filter by configuration status (All, Custom, Default)
 * - Configure button for each server
 * - Bulk configure button (future enhancement)
 * - Visual badges indicating custom vs default configuration
 */
export const ServerConfigurationTab: React.FC<ServerConfigurationTabProps> = ({
  protectionGroupId,
  servers,
  groupDefaults,
  serverConfigs,
  region,
  onConfigChange,
  loading = false,
}) => {
  // State for filter selection
  const [filterOption, setFilterOption] = useState<SelectProps.Option>(
    FILTER_OPTIONS[0]
  );

  // State for configuration dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedServer, setSelectedServer] = useState<ResolvedServer | null>(
    null
  );

  /**
   * Check if a server has custom configuration
   */
  const hasCustomConfig = (serverId: string): boolean => {
    const config = serverConfigs.get(serverId);
    if (!config) return false;
    
    // If useGroupDefaults is false, it's custom
    if (config.useGroupDefaults === false) return true;
    
    // If useGroupDefaults is true but has launchTemplate fields, it's partial custom
    if (config.launchTemplate && Object.keys(config.launchTemplate).length > 0) {
      return true;
    }
    
    return false;
  };

  /**
   * Get list of customized fields for a server
   */
  const getCustomFields = (serverId: string): string[] => {
    const config = serverConfigs.get(serverId);
    if (!config || !config.launchTemplate) return [];
    
    return Object.keys(config.launchTemplate).filter(
      (key) => config.launchTemplate![key as keyof typeof config.launchTemplate] !== undefined
    );
  };

  /**
   * Get static IP for display
   */
  const getStaticIp = (serverId: string): string => {
    const config = serverConfigs.get(serverId);
    const staticIp = config?.launchTemplate?.staticPrivateIp;
    return staticIp || 'DHCP';
  };

  /**
   * Filter servers based on selected filter option
   */
  const filteredServers = useMemo(() => {
    const filterValue = filterOption.value as FilterOption;
    
    if (filterValue === 'all') {
      return servers;
    }
    
    if (filterValue === 'custom') {
      return servers.filter((server) => hasCustomConfig(server.sourceServerID));
    }
    
    if (filterValue === 'default') {
      return servers.filter((server) => !hasCustomConfig(server.sourceServerID));
    }
    
    return servers;
  }, [servers, filterOption, serverConfigs]);

  /**
   * Handle configure button click
   */
  const handleConfigure = (server: ResolvedServer) => {
    setSelectedServer(server);
    setDialogOpen(true);
  };

  /**
   * Handle dialog close
   */
  const handleDialogClose = () => {
    setDialogOpen(false);
    setSelectedServer(null);
  };

  /**
   * Handle configuration save
   */
  const handleConfigSave = (config: ServerLaunchConfig) => {
    if (selectedServer) {
      onConfigChange(selectedServer.sourceServerID, config);
      handleDialogClose();
    }
  };

  /**
   * Handle reset to defaults
   */
  const handleResetToDefaults = (serverId: string) => {
    onConfigChange(serverId, null);
  };

  /**
   * Table column definitions
   */
  const columnDefinitions = [
    {
      id: 'serverName',
      header: 'Server Name',
      cell: (item: ResolvedServer) => (
        <Box>
          <Box variant="strong">{item.hostname || item.nameTag || 'Unknown'}</Box>
          <Box variant="small" color="text-body-secondary">
            {item.sourceServerID}
          </Box>
        </Box>
      ),
      sortingField: 'hostname',
      width: 250,
    },
    {
      id: 'staticIp',
      header: 'Static IP',
      cell: (item: ResolvedServer) => {
        const ip = getStaticIp(item.sourceServerID);
        return (
          <Box color={ip === 'DHCP' ? 'text-body-secondary' : 'text-body-primary'}>
            {ip}
          </Box>
        );
      },
      width: 150,
    },
    {
      id: 'configStatus',
      header: 'Config Status',
      cell: (item: ResolvedServer) => (
        <ServerConfigBadge
          hasCustomConfig={hasCustomConfig(item.sourceServerID)}
          customFields={getCustomFields(item.sourceServerID)}
        />
      ),
      width: 120,
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: (item: ResolvedServer) => (
        <SpaceBetween direction="horizontal" size="xs">
          <Button
            variant="normal"
            onClick={() => handleConfigure(item)}
            iconName="settings"
          >
            Configure
          </Button>
          {hasCustomConfig(item.sourceServerID) && (
            <Button
              variant="normal"
              onClick={() => handleResetToDefaults(item.sourceServerID)}
              iconName="undo"
            >
              Reset
            </Button>
          )}
        </SpaceBetween>
      ),
      width: 200,
    },
  ];

  /**
   * Count servers with custom configs
   */
  const customConfigCount = servers.filter((server) =>
    hasCustomConfig(server.sourceServerID)
  ).length;

  return (
    <>
      <Table
        columnDefinitions={columnDefinitions}
        items={filteredServers}
        loading={loading}
        loadingText="Loading servers..."
        empty={
          <Box textAlign="center" color="inherit">
            <Box variant="strong" textAlign="center" color="inherit">
              No servers
            </Box>
            <Box variant="p" padding={{ bottom: 's' }} color="inherit">
              {filterOption.value === 'all'
                ? 'No servers found in this protection group.'
                : `No servers with ${filterOption.value} configuration.`}
            </Box>
          </Box>
        }
        header={
          <Header
            variant="h2"
            counter={`(${filteredServers.length}/${servers.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Select
                  selectedOption={filterOption}
                  onChange={({ detail }) =>
                    setFilterOption(detail.selectedOption)
                  }
                  options={FILTER_OPTIONS}
                  selectedAriaLabel="Selected"
                />
                <Button
                  variant="primary"
                  iconName="add-plus"
                  disabled={servers.length === 0}
                >
                  Bulk Configure
                </Button>
              </SpaceBetween>
            }
            description={
              customConfigCount > 0
                ? `${customConfigCount} server${customConfigCount === 1 ? '' : 's'} with custom configuration`
                : 'All servers using protection group defaults'
            }
          >
            Server Configurations
          </Header>
        }
        variant="container"
        stickyHeader
      />

      {/* Configuration Dialog */}
      {selectedServer && (
        <ServerLaunchConfigDialog
          open={dialogOpen}
          server={selectedServer}
          groupDefaults={groupDefaults}
          serverConfig={serverConfigs.get(selectedServer.sourceServerID)}
          region={region}
          groupId={protectionGroupId}
          onClose={handleDialogClose}
          onSave={handleConfigSave}
        />
      )}
    </>
  );
};

export default ServerConfigurationTab;
