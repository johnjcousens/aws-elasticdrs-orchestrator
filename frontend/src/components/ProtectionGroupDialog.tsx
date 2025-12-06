/**
 * Protection Group Dialog Component
 * 
 * Modal dialog for creating and editing protection groups.
 * Includes form fields for name, description, and automatic server discovery.
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Textarea,
  Alert,
} from '@cloudscape-design/components';
import { RegionSelector } from './RegionSelector';
import { ServerDiscoveryPanel } from './ServerDiscoveryPanel';
import apiClient from '../services/api';
import type { ProtectionGroup } from '../types';

interface ProtectionGroupDialogProps {
  open: boolean;
  group?: ProtectionGroup | null;
  onClose: () => void;
  onSave: (group: ProtectionGroup) => void;
}

/**
 * Protection Group Dialog Component
 * 
 * Provides form for creating/editing protection groups with automatic server discovery.
 * Validates inputs and handles API calls with conflict detection.
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
  const [selectedServerIds, setSelectedServerIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    name?: string;
    region?: string;
    servers?: string;
  }>({});

  const isEditMode = Boolean(group);

  // Initialize form when dialog opens or group changes
  useEffect(() => {
    if (open) {
      if (group) {
        // Edit mode - populate form with existing data
        setName(group.name);
        setDescription(group.description || '');
        setRegion(group.region || '');
        setSelectedServerIds(group.sourceServerIds || []);
      } else {
        // Create mode - reset form
        setName('');
        setDescription('');
        setRegion('us-east-1'); // Default region
        setSelectedServerIds([]);
      }
      setError(null);
      setValidationErrors({});
    }
  }, [open, group]);

  const validateForm = (): boolean => {
    const errors: { name?: string; region?: string; servers?: string } = {};

    // Validate name
    if (!name.trim()) {
      errors.name = 'Name is required';
    }

    // Validate region
    if (!region) {
      errors.region = 'Region is required';
    }

    // Validate server selection
    if (selectedServerIds.length === 0) {
      errors.servers = 'At least one server must be selected';
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

      const groupData = {
        GroupName: name.trim(),
        Description: description.trim() || undefined,
        Region: region,
        sourceServerIds: selectedServerIds,
      };

      let savedGroup: ProtectionGroup;

      if (isEditMode && group) {
        // Update existing group
        savedGroup = await apiClient.updateProtectionGroup(group.protectionGroupId, groupData);
      } else {
        // Create new group
        savedGroup = await apiClient.createProtectionGroup(groupData);
      }

      onSave(savedGroup);
      onClose();
    } catch (err: any) {
      // Handle conflict errors with detailed messages
      if (err.response?.status === 409) {
        const conflictData = err.response?.data;
        if (conflictData?.conflictType === 'NAME_CONFLICT') {
          setError(`Protection Group name "${name}" is already in use. Please choose a different name.`);
        } else if (conflictData?.conflictType === 'SERVER_CONFLICT') {
          const conflicts = conflictData.conflicts || [];
          const conflictMessages = conflicts.map((c: any) => 
            `${c.serverId} is assigned to "${c.protectionGroupName}"`
          ).join(', ');
          setError(`Server conflict: ${conflictMessages}. Please deselect these servers or remove them from their current Protection Group.`);
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
              disabled={loading || !region}
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
          <Alert type="error">
            {error}
          </Alert>
        )}

        {/* Name Field */}
        <FormField
          label="Name"
          description="A globally unique name for this protection group"
          errorText={validationErrors.name}
        >
          <Input
            value={name}
            onChange={({ detail }) => setName(detail.value)}
            placeholder="e.g., Production Servers"
            disabled={loading}
          />
        </FormField>

        {/* Description Field */}
        <FormField
          label="Description"
          description="Optional description of this protection group"
        >
          <Textarea
            value={description}
            onChange={({ detail }) => setDescription(detail.value)}
            placeholder="e.g., All production servers in us-east-1"
            rows={2}
            disabled={loading}
          />
        </FormField>

        {/* Region Selector */}
        <RegionSelector
          value={region}
          onChange={setRegion}
          disabled={loading || isEditMode}
          error={Boolean(validationErrors.region)}
          helperText={
            isEditMode
              ? 'Region cannot be changed after creation'
              : validationErrors.region || 'Select the AWS region where servers are located'
          }
        />

        {/* Server Discovery Panel */}
        {region && (
          <>
            {validationErrors.servers && (
              <Alert type="error">
                {validationErrors.servers}
              </Alert>
            )}
            <ServerDiscoveryPanel
              region={region}
              selectedServerIds={selectedServerIds}
              onSelectionChange={setSelectedServerIds}
              currentProtectionGroupId={group?.protectionGroupId}
            />
          </>
        )}
      </SpaceBetween>
    </Modal>
  );
};
