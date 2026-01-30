/**
 * Protection Group Dialog Component
 * 
 * Modal dialog for creating and editing protection groups.
 * Supports both:
 * - Tag-based server selection (new) - servers matching ALL specified tags
 * - Explicit server IDs (legacy) - for backward compatibility
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Textarea,
  Alert,
  Container,
  Header,
  ColumnLayout,
  Icon,
  Tabs,
} from '@cloudscape-design/components';
import { RegionSelector } from './RegionSelector';
import { ServerDiscoveryPanel } from './ServerDiscoveryPanel';
import { LaunchConfigSection } from './LaunchConfigSection';
import { ServerConfigurationTab } from './ServerConfigurationTab';
import { PermissionAwareButton } from './PermissionAware';
import { DRSPermission } from '../types/permissions';
import { ServerListItem } from './ServerListItem';
import { useAccount } from '../contexts/AccountContext';
import apiClient from '../services/api';
import type { ProtectionGroup, ResolvedServer, LaunchConfig, ServerLaunchConfig } from '../types';

interface TagEntry {
  key: string;
  value: string;
}

interface ProtectionGroupDialogProps {
  open: boolean;
  group?: ProtectionGroup | null;
  onClose: () => void;
  onSave: (group: ProtectionGroup) => void;
}

/**
 * Protection Group Dialog Component
 * 
 * Provides form for creating/editing protection groups.
 * Supports both tag-based and explicit server selection.
 */
export const ProtectionGroupDialog: React.FC<ProtectionGroupDialogProps> = ({
  open,
  group,
  onClose,
  onSave,
}) => {
  const { getCurrentAccountId } = useAccount();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [region, setRegion] = useState('');
  const [tags, setTags] = useState<TagEntry[]>([{ key: '', value: '' }]);
  const [selectedServerIds, setSelectedServerIds] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState<'tags' | 'servers'>('servers');
  const [launchConfig, setLaunchConfig] = useState<LaunchConfig>({});
  const [serverConfigs, setServerConfigs] = useState<Map<string, ServerLaunchConfig>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    name?: string;
    region?: string;
    tags?: string;
    servers?: string;
  }>({});
  
  // Preview state for tag-based selection
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewServers, setPreviewServers] = useState<ResolvedServer[]>([]);
  const [previewError, setPreviewError] = useState<string | null>(null);
  
  // State for active tab
  const [activeTabId, setActiveTabId] = useState<string>('servers');

  const isEditMode = Boolean(group);

  // Convert tags object to array format for editing
  const tagsObjectToArray = (tagsObj: Record<string, string>): TagEntry[] => {
    const entries = Object.entries(tagsObj).map(([key, value]) => ({ key, value }));
    return entries.length > 0 ? entries : [{ key: '', value: '' }];
  };

  // Convert tags array to object format for API
  const tagsArrayToObject = (tagsArr: TagEntry[]): Record<string, string> => {
    const obj: Record<string, string> = {};
    tagsArr.forEach(({ key, value }) => {
      if (key.trim() && value.trim()) {
        obj[key.trim()] = value.trim();
      }
    });
    return obj;
  };

  // Initialize form when dialog opens or group changes
  useEffect(() => {
    if (open) {
      if (group) {
        // Edit mode - populate form with existing data
        setName(group.groupName || '');
        setDescription(group.description || '');
        setRegion(group.region || '');
        
        // Determine selection mode based on existing data
        if (group.serverSelectionTags && Object.keys(group.serverSelectionTags).length > 0) {
          setSelectionMode('tags');
          setTags(tagsObjectToArray(group.serverSelectionTags));
          setSelectedServerIds([]);
        } else if (group.sourceServerIds && group.sourceServerIds.length > 0) {
          setSelectionMode('servers');
          setSelectedServerIds(group.sourceServerIds);
          setTags([{ key: '', value: '' }]);
        } else {
          // Default to server selection for existing groups without either
          setSelectionMode('servers');
          setSelectedServerIds([]);
          setTags([{ key: '', value: '' }]);
        }
        // Load existing launch config
        setLaunchConfig(group.launchConfig || {});
        
        // Load existing per-server configs
        if (group.servers && group.servers.length > 0) {
          const configMap = new Map<string, ServerLaunchConfig>();
          group.servers.forEach(serverConfig => {
            configMap.set(serverConfig.sourceServerId, serverConfig);
          });
          setServerConfigs(configMap);
        } else {
          setServerConfigs(new Map());
        }
      } else {
        // Create mode - reset form
        setName('');
        setDescription('');
        setRegion('us-east-1');
        setSelectionMode('servers');
        setSelectedServerIds([]);
        setTags([{ key: '', value: '' }]);
        setLaunchConfig({
          copyTags: true,
          launchDisposition: 'STARTED',
          licensing: { osByol: false }
        });
        setServerConfigs(new Map());
      }
      setError(null);
      setValidationErrors({});
      setPreviewServers([]);
      setPreviewError(null);
      setActiveTabId('servers'); // Reset to first tab
    }
  }, [open, group]);

  // Add a new tag row
  const handleAddTag = () => {
    setTags([...tags, { key: '', value: '' }]);
  };

  // Remove a tag row
  const handleRemoveTag = (index: number) => {
    if (tags.length > 1) {
      setTags(tags.filter((_, i) => i !== index));
    }
  };

  // Update a tag entry
  const handleTagChange = (index: number, field: 'key' | 'value', newValue: string) => {
    const newTags = [...tags];
    newTags[index] = { ...newTags[index], [field]: newValue };
    setTags(newTags);
  };

  // Preview resolved servers for tag-based selection
  const handlePreview = useCallback(async () => {
    const tagsObj = tagsArrayToObject(tags);
    if (Object.keys(tagsObj).length === 0) {
      setPreviewError('Add at least one tag to preview servers');
      return;
    }

    if (!region) {
      setPreviewError('Select a region first');
      return;
    }

    try {
      setPreviewLoading(true);
      setPreviewError(null);
      
      const response = await apiClient.resolveProtectionGroupTags(region, tagsObj);
      setPreviewServers(response.resolvedServers || []);
      
      if (response.resolvedServers?.length === 0) {
        setPreviewError('No servers found matching these tags');
      }
    } catch (err: unknown) {
      const error = err as Error & { message?: string };
      setPreviewError(error.message || 'Failed to preview servers');
      setPreviewServers([]);
    } finally {
      setPreviewLoading(false);
    }
  }, [region, tags]);

  // Handle per-server configuration changes
  const handleServerConfigChange = (serverId: string, config: ServerLaunchConfig | null) => {
    const newConfigs = new Map(serverConfigs);
    if (config === null) {
      // Remove server config (reset to defaults)
      newConfigs.delete(serverId);
    } else {
      // Update server config
      newConfigs.set(serverId, config);
    }
    setServerConfigs(newConfigs);
  };

  // State for fetching server details in explicit selection mode
  const [fetchingServerDetails, setFetchingServerDetails] = useState(false);
  const [explicitModeServers, setExplicitModeServers] = useState<ResolvedServer[]>([]);

  // Fetch server details when in explicit selection mode and servers are selected
  useEffect(() => {
    if (selectionMode === 'servers' && selectedServerIds.length > 0 && region) {
      const fetchServerDetails = async () => {
        try {
          setFetchingServerDetails(true);
          const accountId = getCurrentAccountId();
          if (!accountId) return;
          
          const response = await apiClient.listDRSSourceServers(region, accountId);
          
          // Filter to only selected servers and convert to ResolvedServer format
          const selectedServers = response.servers
            .filter(server => selectedServerIds.includes(server.sourceServerID))
            .map(server => ({
              sourceServerID: server.sourceServerID,
              hostname: server.hostname,
              fqdn: server.fqdn,
              nameTag: server.nameTag,
              sourceInstanceId: server.sourceInstanceId,
              sourceIp: server.sourceIp,
              sourceMac: server.sourceMac,
              sourceRegion: server.sourceRegion,
              sourceAccount: server.sourceAccount,
              os: server.os,
              state: server.state,
              replicationState: server.replicationState,
              lagDuration: server.lagDuration,
              lastSeen: server.lastSeen,
              hardware: server.hardware,
              networkInterfaces: server.networkInterfaces,
              drsTags: server.drsTags,
              tags: server.drsTags || {},
              assignedToProtectionGroup: server.assignedToProtectionGroup,
              selectable: server.selectable,
            }));
          
          setExplicitModeServers(selectedServers);
        } catch (err) {
          console.error('Failed to fetch server details:', err);
          setExplicitModeServers([]);
        } finally {
          setFetchingServerDetails(false);
        }
      };
      
      fetchServerDetails();
    } else if (selectionMode === 'servers' && selectedServerIds.length === 0) {
      // Clear servers when selection is empty
      setExplicitModeServers([]);
    }
  }, [selectionMode, selectedServerIds, region]);

  // Get list of resolved servers for Server Configuration tab
  const resolvedServers = useMemo(() => {
    if (selectionMode === 'tags') {
      return previewServers;
    } else {
      // For explicit server selection, use fetched server details
      return explicitModeServers;
    }
  }, [selectionMode, previewServers, explicitModeServers]);

  // Count servers with custom configs
  const customConfigCount = useMemo(() => {
    let count = 0;
    serverConfigs.forEach((config) => {
      if (!config.useGroupDefaults || (config.launchTemplate && Object.keys(config.launchTemplate).length > 0)) {
        count++;
      }
    });
    return count;
  }, [serverConfigs]);

  const validateForm = (): boolean => {
    const errors: { name?: string; region?: string; tags?: string; servers?: string } = {};

    if (!name.trim()) {
      errors.name = 'Name is required';
    }

    if (!region) {
      errors.region = 'Region is required';
    }

    if (selectionMode === 'tags') {
      const tagsObj = tagsArrayToObject(tags);
      if (Object.keys(tagsObj).length === 0) {
        errors.tags = 'At least one tag is required';
      }
    } else {
      if (selectedServerIds.length === 0) {
        errors.servers = 'At least one server must be selected';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    // Validate for duplicate static IPs
    const staticIPs = new Map<string, string[]>(); // IP -> [serverIds]
    serverConfigs.forEach((config, serverId) => {
      const staticIp = config.launchTemplate?.staticPrivateIp;
      if (staticIp && staticIp.trim() !== '') {
        if (!staticIPs.has(staticIp)) {
          staticIPs.set(staticIp, []);
        }
        staticIPs.get(staticIp)!.push(serverId);
      }
    });

    // Check for duplicates
    const duplicates = Array.from(staticIPs.entries()).filter(([_, serverIds]) => serverIds.length > 1);
    if (duplicates.length > 0) {
      const duplicateMessages = duplicates.map(([ip, serverIds]) => 
        `IP ${ip} is assigned to ${serverIds.length} servers`
      ).join(', ');
      setError(`Duplicate static IP addresses detected: ${duplicateMessages}. Each server must have a unique static IP.`);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let savedGroup: ProtectionGroup;

      // Build base group data
      const groupData: {
        groupName: string;
        description: string;
        region: string;
        serverSelectionTags?: Record<string, string>;
        sourceServerIds?: string[];
        launchConfig?: LaunchConfig;
        servers?: ServerLaunchConfig[];
        version?: number;
      } = {
        groupName: name.trim(),
        description: description.trim(),  // Always send, even if empty, to allow clearing
        region: region,
      };

      // Add server selection based on mode
      if (selectionMode === 'tags') {
        groupData.serverSelectionTags = tagsArrayToObject(tags);
      } else {
        groupData.sourceServerIds = selectedServerIds;
      }

      // Add launch config if any settings are configured
      const hasLaunchConfig = launchConfig.subnetId ||
        (launchConfig.securityGroupIds && launchConfig.securityGroupIds.length > 0) ||
        launchConfig.instanceType ||
        launchConfig.instanceProfileName ||
        launchConfig.copyPrivateIp ||
        launchConfig.copyTags ||
        launchConfig.licensing?.osByol;

      if (hasLaunchConfig) {
        groupData.launchConfig = launchConfig;
      }

      // Add per-server configs if any exist
      if (serverConfigs.size > 0) {
        groupData.servers = Array.from(serverConfigs.values());
      }

      if (isEditMode && group) {
        // Include version for optimistic locking
        if (group.version !== undefined) {
          groupData.version = group.version;
        }
        savedGroup = await apiClient.updateProtectionGroup(group.protectionGroupId, groupData);
      } else {
        savedGroup = await apiClient.createProtectionGroup(groupData);
      }

      onSave(savedGroup);
      onClose();
    } catch (err: unknown) {
      const error = err as Error & { 
        message?: string; 
        isVersionConflict?: boolean;
        response?: {
          status?: number;
          data?: {
            conflictType?: string;
            message?: string;
          };
        };
      };
      
      if (error.isVersionConflict) {
        // Optimistic locking conflict - another user modified the resource
        setError('This protection group was modified by another user. Please close and reopen to get the latest version.');
      } else if (error.response?.status === 409) {
        const conflictData = error.response?.data;
        if (conflictData?.conflictType === 'NAME_CONFLICT') {
          setError(`Protection Group name "${name}" is already in use.`);
        } else if (conflictData?.conflictType === 'SERVER_CONFLICT') {
          setError(conflictData?.message || 'One or more servers are already assigned to another Protection Group.');
        } else {
          setError(conflictData?.message || 'Conflict detected. Please check your inputs.');
        }
      } else {
        setError(error.message || 'Failed to save protection group');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (!loading) {
      onClose();
    }
  };

  // Check if we have valid selection
  const hasValidSelection = selectionMode === 'tags' 
    ? tags.some(t => t.key.trim() && t.value.trim())
    : selectedServerIds.length > 0;

  return (
    <Modal
      visible={open}
      onDismiss={handleCancel}
      header={isEditMode ? 'Edit Protection Group' : 'Create Protection Group'}
      size="large"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleCancel} disabled={loading}>
              Cancel
            </Button>
            <PermissionAwareButton
              onClick={handleSave}
              variant="primary"
              disabled={loading || !region || !hasValidSelection}
              loading={loading}
              requiredPermission={isEditMode ? DRSPermission.MODIFY_PROTECTION_GROUPS : DRSPermission.CREATE_PROTECTION_GROUPS}
              fallbackTooltip={isEditMode ? "Requires protection group modification permission" : "Requires protection group creation permission"}
            >
              {isEditMode ? 'Update Group' : 'Create Group'}
            </PermissionAwareButton>
          </SpaceBetween>
        </Box>
      }
    >
      <form onSubmit={(e) => e.preventDefault()}>
        <SpaceBetween size="l">
          {error && (
            <Alert type="error" dismissible onDismiss={() => setError(null)}>
              {error}
            </Alert>
          )}

          <FormField
            label="Name"
            description="A unique name for this protection group"
            errorText={validationErrors.name}
          >
          <Input
            value={name}
            onChange={({ detail }: { detail: { value: string } }) => setName(detail.value)}
            placeholder="e.g., HRP Database Tier"
            disabled={loading}
          />
        </FormField>

        <FormField
          label="Description"
          description="Optional description"
        >
          <Textarea
            value={description}
            onChange={({ detail }: { detail: { value: string } }) => setDescription(detail.value)}
            placeholder="e.g., All database servers for HRP application"
            rows={2}
            disabled={loading}
          />
        </FormField>

        <FormField
          label="Region"
          description={
            isEditMode
              ? 'Region cannot be changed after creation'
              : 'Select the AWS region where DRS servers are located'
          }
          errorText={validationErrors.region}
        >
          <RegionSelector
            value={region}
            onChange={setRegion}
            disabled={loading || isEditMode}
            error={Boolean(validationErrors.region)}
          />
        </FormField>

        {/* Main Tabs - Configuration, Server Selection, Server Configurations */}
        {region && (
          <Tabs
            activeTabId={activeTabId}
            onChange={({ detail }: { detail: { activeTabId: string } }) => {
              setActiveTabId(detail.activeTabId);
            }}
            tabs={[
              {
                id: 'servers',
                label: 'Server Selection',
                content: (
                  <SpaceBetween size="m">
                    {/* Server Selection - Tabs for different modes */}
                    <Tabs
                      activeTabId={selectionMode}
                      onChange={({ detail }: { detail: { activeTabId: string } }) => {
                        const newMode = detail.activeTabId as 'tags' | 'servers';
                        setSelectionMode(newMode);
                        // Clear the other mode's data when switching
                        if (newMode === 'tags') {
                          setSelectedServerIds([]);
                        } else {
                          setTags([{ key: '', value: '' }]);
                          setPreviewServers([]);
                          setPreviewError(null);
                        }
                      }}
                      tabs={[
                        {
                          id: 'servers',
                          label: 'Select Servers',
                          content: (
                            <Container
                              header={
                                <Header variant="h3" description="Select specific DRS source servers">
                                  Server Selection
                                </Header>
                              }
                            >
                              <SpaceBetween size="s">
                                {validationErrors.servers && (
                                  <Alert type="error">{validationErrors.servers}</Alert>
                                )}
                                {/* Only render ServerDiscoveryPanel when this tab is active to prevent background API calls */}
                                {selectionMode === 'servers' && activeTabId === 'servers' && (
                                  <ServerDiscoveryPanel
                                    region={region}
                                    selectedServerIds={selectedServerIds}
                                    onSelectionChange={setSelectedServerIds}
                                    currentProtectionGroupId={group?.protectionGroupId}
                                    pauseRefresh={true}
                                  />
                                )}
                              </SpaceBetween>
                            </Container>
                          ),
                        },
                        {
                          id: 'tags',
                          label: 'Select by Tags',
                          content: (
                            <SpaceBetween size="m">
                              {/* Tag Editor */}
                              <Container
                                header={
                                  <Header
                                    variant="h3"
                                    description="Servers with ALL these tags will be included at execution time"
                                    actions={
                                      <Button iconName="add-plus" onClick={(e) => { e.preventDefault(); handleAddTag(); }} disabled={loading}>
                                        Add Tag
                                      </Button>
                                    }
                                  >
                                    Server Selection Tags
                                  </Header>
                                }
                              >
                                <SpaceBetween size="s">
                                  {validationErrors.tags && (
                                    <Alert type="error">{validationErrors.tags}</Alert>
                                  )}
                                  
                                  {tags.map((tag, index) => (
                                    <ColumnLayout key={index} columns={3}>
                                      <FormField label={index === 0 ? 'Tag Key' : undefined}>
                                        <Input
                                          value={tag.key}
                                          onChange={({ detail }: { detail: { value: string } }) => handleTagChange(index, 'key', detail.value)}
                                          placeholder="e.g., DR-Application"
                                          disabled={loading}
                                        />
                                      </FormField>
                                      <FormField label={index === 0 ? 'Tag Value' : undefined}>
                                        <Input
                                          value={tag.value}
                                          onChange={({ detail }: { detail: { value: string } }) => handleTagChange(index, 'value', detail.value)}
                                          placeholder="e.g., HRP"
                                          disabled={loading}
                                        />
                                      </FormField>
                                      <Box padding={{ top: index === 0 ? 'l' : 'n' }}>
                                        <Button
                                          iconName="close"
                                          variant="icon"
                                          onClick={(e) => { e.preventDefault(); handleRemoveTag(index); }}
                                          disabled={loading || tags.length === 1}
                                          ariaLabel="Remove tag"
                                        />
                                      </Box>
                                    </ColumnLayout>
                                  ))}
                                </SpaceBetween>
                              </Container>

                              {/* Server Preview for tag-based selection */}
                              <Container
                                header={
                                  <Header
                                    variant="h3"
                                    counter={previewServers.length > 0 ? `(${previewServers.length})` : undefined}
                                    actions={
                                      <Button
                                        onClick={(e) => { e.preventDefault(); handlePreview(); }}
                                        loading={previewLoading}
                                        disabled={!tags.some(t => t.key.trim() && t.value.trim()) || loading}
                                        iconName="refresh"
                                      >
                                        Preview Servers
                                      </Button>
                                    }
                                  >
                                    Matching Servers
                                  </Header>
                                }
                              >
                                {previewError && (
                                  <Alert type="warning">{previewError}</Alert>
                                )}
                                
                                {previewServers.length > 0 ? (
                                  <div style={{ maxHeight: '400px', overflow: 'auto', border: '1px solid #e9ebed', borderRadius: '8px' }}>
                                    {previewServers.map((server) => (
                                      <ServerListItem
                                        key={server.sourceServerID}
                                        server={{
                                          ...server,
                                          state: server.state || 'UNKNOWN',
                                          replicationState: server.replicationState || 'UNKNOWN',
                                          lagDuration: server.lagDuration || 'UNKNOWN',
                                          lastSeen: server.lastSeen || '',
                                          assignedToProtectionGroup: server.assignedToProtectionGroup || null,
                                          selectable: true // Keep servers looking normal
                                        }}
                                        selected={false} // Preview mode - no selection
                                        onToggle={() => {}} // No-op for preview
                                        showCheckbox={false} // Hide checkbox for tag preview
                                      />
                                    ))}
                                  </div>
                                ) : !previewError && (
                                  <Box textAlign="center" color="text-body-secondary" padding="s">
                                    <Icon name="search" /> Click "Preview Servers" to see which servers match your tags
                                  </Box>
                                )}
                              </Container>
                            </SpaceBetween>
                          ),
                        },
                      ]}
                    />
                  </SpaceBetween>
                ),
              },
              {
                id: 'launch-config',
                label: 'Launch Settings',
                content: (
                  <LaunchConfigSection
                    region={region}
                    launchConfig={launchConfig}
                    onChange={setLaunchConfig}
                    disabled={loading}
                    customConfigCount={customConfigCount}
                  />
                ),
              },
              {
                id: 'server-configs',
                label: `Server Configurations${customConfigCount > 0 ? ` (${customConfigCount} custom)` : ''}`,
                content: (
                  <Container>
                    {fetchingServerDetails ? (
                      <Box textAlign="center" color="text-body-secondary" padding="xxl">
                        <SpaceBetween size="s">
                          <Icon name="status-in-progress" size="large" />
                          <Box variant="p">Loading server details...</Box>
                        </SpaceBetween>
                      </Box>
                    ) : resolvedServers.length > 0 ? (
                      <ServerConfigurationTab
                        protectionGroupId={group?.protectionGroupId || ''}
                        servers={resolvedServers}
                        groupDefaults={launchConfig}
                        serverConfigs={serverConfigs}
                        region={region}
                        onConfigChange={handleServerConfigChange}
                        loading={loading}
                      />
                    ) : (
                      <Box textAlign="center" color="text-body-secondary" padding="xxl">
                        <SpaceBetween size="s">
                          <Icon name="status-info" size="large" />
                          <Box variant="p">
                            {selectionMode === 'tags' 
                              ? 'Preview servers in the Server Selection tab to configure per-server settings'
                              : 'Select servers in the Server Selection tab to configure per-server settings'}
                          </Box>
                        </SpaceBetween>
                      </Box>
                    )}
                  </Container>
                ),
              },
            ]}
          />
        )}

        {!region && (
          <Alert type="info">
            Select a region to configure server selection and launch settings
          </Alert>
        )}
        </SpaceBetween>
      </form>
    </Modal>
  );
};
