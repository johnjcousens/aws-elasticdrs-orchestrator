/**
 * Protection Group Dialog Component
 * 
 * Modal dialog for creating and editing protection groups.
 * Supports both:
 * - Tag-based server selection (new) - servers matching ALL specified tags
 * - Explicit server IDs (legacy) - for backward compatibility
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Table,
  StatusIndicator,
  ColumnLayout,
  Icon,
  Tabs,
} from '@cloudscape-design/components';
import { RegionSelector } from './RegionSelector';
import { ServerDiscoveryPanel } from './ServerDiscoveryPanel';
import apiClient from '../services/api';
import type { ProtectionGroup, ResolvedServer } from '../types';

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
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [region, setRegion] = useState('');
  const [tags, setTags] = useState<TagEntry[]>([{ key: '', value: '' }]);
  const [selectedServerIds, setSelectedServerIds] = useState<string[]>([]);
  const [selectionMode, setSelectionMode] = useState<'tags' | 'servers'>('servers');
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
        setName(group.name);
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
      } else {
        // Create mode - reset form
        setName('');
        setDescription('');
        setRegion('us-east-1');
        setSelectionMode('servers');
        setSelectedServerIds([]);
        setTags([{ key: '', value: '' }]);
      }
      setError(null);
      setValidationErrors({});
      setPreviewServers([]);
      setPreviewError(null);
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
    } catch (err: any) {
      setPreviewError(err.message || 'Failed to preview servers');
      setPreviewServers([]);
    } finally {
      setPreviewLoading(false);
    }
  }, [region, tags]);

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

    try {
      setLoading(true);
      setError(null);

      let savedGroup: ProtectionGroup;

      if (selectionMode === 'tags') {
        // Tag-based selection
        const groupData: any = {
          GroupName: name.trim(),
          Description: description.trim() || undefined,
          Region: region,
          ServerSelectionTags: tagsArrayToObject(tags),
        };

        if (isEditMode && group) {
          // Include version for optimistic locking
          if (group.version !== undefined) {
            groupData.version = group.version;
          }
          savedGroup = await apiClient.updateProtectionGroup(group.protectionGroupId, groupData);
        } else {
          savedGroup = await apiClient.createProtectionGroup(groupData);
        }
      } else {
        // Explicit server selection (legacy)
        const groupData: any = {
          GroupName: name.trim(),
          Description: description.trim() || undefined,
          Region: region,
          SourceServerIds: selectedServerIds,
        };

        if (isEditMode && group) {
          // Include version for optimistic locking
          if (group.version !== undefined) {
            groupData.version = group.version;
          }
          savedGroup = await apiClient.updateProtectionGroup(group.protectionGroupId, groupData);
        } else {
          savedGroup = await apiClient.createProtectionGroup(groupData);
        }
      }

      onSave(savedGroup);
      onClose();
    } catch (err: any) {
      if (err.isVersionConflict) {
        // Optimistic locking conflict - another user modified the resource
        setError('This protection group was modified by another user. Please close and reopen to get the latest version.');
      } else if (err.response?.status === 409) {
        const conflictData = err.response?.data;
        if (conflictData?.conflictType === 'NAME_CONFLICT') {
          setError(`Protection Group name "${name}" is already in use.`);
        } else if (conflictData?.conflictType === 'SERVER_CONFLICT') {
          setError(conflictData?.message || 'One or more servers are already assigned to another Protection Group.');
        } else {
          setError(conflictData?.message || 'Conflict detected. Please check your inputs.');
        }
      } else {
        setError(err.message || 'Failed to save protection group');
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
            <Button
              onClick={handleSave}
              variant="primary"
              disabled={loading || !region || !hasValidSelection}
              loading={loading}
            >
              {isEditMode ? 'Save Changes' : 'Create Group'}
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
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
            onChange={({ detail }) => setName(detail.value)}
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
            onChange={({ detail }) => setDescription(detail.value)}
            placeholder="e.g., All database servers for HRP application"
            rows={2}
            disabled={loading}
          />
        </FormField>

        <RegionSelector
          value={region}
          onChange={setRegion}
          disabled={loading || isEditMode}
          error={Boolean(validationErrors.region)}
          helperText={
            isEditMode
              ? 'Region cannot be changed after creation'
              : validationErrors.region || 'Select the AWS region where DRS servers are located'
          }
        />

        {/* Server Selection - Tabs for different modes */}
        {region && (
          <Tabs
            activeTabId={selectionMode}
            onChange={({ detail }) => {
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
                      <ServerDiscoveryPanel
                        region={region}
                        selectedServerIds={selectedServerIds}
                        onSelectionChange={setSelectedServerIds}
                        currentProtectionGroupId={group?.protectionGroupId}
                      />
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
                            <Button iconName="add-plus" onClick={handleAddTag} disabled={loading}>
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
                                onChange={({ detail }) => handleTagChange(index, 'key', detail.value)}
                                placeholder="e.g., DR-Application"
                                disabled={loading}
                              />
                            </FormField>
                            <FormField label={index === 0 ? 'Tag Value' : undefined}>
                              <Input
                                value={tag.value}
                                onChange={({ detail }) => handleTagChange(index, 'value', detail.value)}
                                placeholder="e.g., HRP"
                                disabled={loading}
                              />
                            </FormField>
                            <Box padding={{ top: index === 0 ? 'l' : 'n' }}>
                              <Button
                                iconName="close"
                                variant="icon"
                                onClick={() => handleRemoveTag(index)}
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
                              onClick={handlePreview}
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
                        <Table
                          items={previewServers}
                          columnDefinitions={[
                            {
                              id: 'hostname',
                              header: 'Hostname',
                              cell: (item) => item.hostname || 'N/A',
                            },
                            {
                              id: 'serverId',
                              header: 'Server ID',
                              cell: (item) => (
                                <code style={{ fontSize: '12px' }}>
                                  {item.sourceServerId.substring(0, 16)}...
                                </code>
                              ),
                            },
                            {
                              id: 'status',
                              header: 'Replication',
                              cell: (item) => (
                                <StatusIndicator
                                  type={item.replicationState === 'CONTINUOUS' ? 'success' : 'warning'}
                                >
                                  {item.replicationState}
                                </StatusIndicator>
                              ),
                            },
                          ]}
                          variant="embedded"
                          empty={
                            <Box textAlign="center" color="inherit" padding="s">
                              Click "Preview Servers" to see matching servers
                            </Box>
                          }
                        />
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
        )}
      </SpaceBetween>
    </Modal>
  );
};
