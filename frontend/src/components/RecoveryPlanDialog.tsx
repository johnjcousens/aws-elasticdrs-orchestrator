/**
 * Recovery Plan Dialog Component
 * 
 * Dialog for creating and editing recovery plans with protection group
 * selection and wave configuration.
 */

import React, { useState, useEffect } from 'react';
import type { RecoveryPlan, ProtectionGroup, Wave, CreateRecoveryPlanRequest, UpdateRecoveryPlanRequest } from '../types';
import {
  Modal,
  Box,
  SpaceBetween,
  Button,
  FormField,
  Input,
  Textarea,
  Alert,
  Header,
  Container,
} from '@cloudscape-design/components';
import { LoadingState } from './LoadingState';
import { WaveConfigEditor } from './WaveConfigEditor';
import apiClient from '../services/api';
import { DRS_LIMITS } from '../services/drsQuotaService';
import { PermissionAwareButton } from './PermissionAware';
import { DRSPermission } from '../contexts/PermissionsContext';

interface RecoveryPlanDialogProps {
  open: boolean;
  plan: RecoveryPlan | null;
  onClose: () => void;
  onSave: (plan: RecoveryPlan) => void;
}

/**
 * Recovery Plan Dialog Component
 * 
 * Form dialog for creating or editing a recovery plan.
 */
export const RecoveryPlanDialog: React.FC<RecoveryPlanDialogProps> = ({
  open,
  plan,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [waves, setWaves] = useState<Wave[]>([]);
  const [protectionGroups, setProtectionGroups] = useState<ProtectionGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load protection groups on mount
  useEffect(() => {
    if (open) {
      fetchProtectionGroups();
    }
  }, [open]);

  // Populate form when editing - only runs when dialog opens or plan changes
  useEffect(() => {
    if (!open) return;
    
    if (plan && protectionGroups.length > 0) {
      // Edit mode - populate from existing plan (only on initial load)
      setName(plan.name);
      setDescription(plan.description || '');
      
      // Populate waves with BOTH protectionGroupId and protectionGroupIds array
      // Use first PG as default if wave doesn't have one
      const firstPgId = protectionGroups[0]?.protectionGroupId || '';
      const wavesWithPgId = (plan.waves || []).map(w => {
        // Extract PG ID from various possible fields (backend sends both now)
        const pgId = w.protectionGroupId || w.ProtectionGroupId || firstPgId;
        const pgIds = w.protectionGroupIds || (pgId ? [pgId] : []);
        
        return {
          ...w,
          protectionGroupId: pgId,  // Single field for backward compatibility
          protectionGroupIds: pgIds  // Array field for Autocomplete
        };
      });
      setWaves(wavesWithPgId);
    }
    setErrors({});
    setError(null);
  // Only re-run when dialog opens, plan changes, or protection groups load
  // Do NOT include waves.length - that causes reset when adding waves
  }, [plan, open, protectionGroups]);

  // Reset form when dialog closes or switches to create mode
  useEffect(() => {
    if (open && !plan) {
      // Create mode - reset form once when dialog opens
      setName('');
      setDescription('');
      setWaves([]);
      setErrors({});
      setError(null);
    }
  }, [open, plan]);

  const fetchProtectionGroups = async () => {
    try {
      setLoadingGroups(true);
      const data = await apiClient.listProtectionGroups();
      // Defensive check: ensure data is an array
      setProtectionGroups(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load protection groups';
      setError(errorMessage);
    } finally {
      setLoadingGroups(false);
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = 'Plan name is required';
    }

    if (waves.length === 0) {
      newErrors.waves = 'At least one wave is required';
    }

    if (waves.some(w => !w.protectionGroupId && (!w.protectionGroupIds || w.protectionGroupIds.length === 0))) {
      newErrors.waves = 'All waves must have a Protection Group selected';
    }

    // Check serverIds only for non-tag-based Protection Groups
    const wavesNeedingServers = waves.filter(w => {
      // Get the PGs for this wave
      const wavePgIds = w.protectionGroupIds && w.protectionGroupIds.length > 0 
        ? w.protectionGroupIds 
        : (w.protectionGroupId ? [w.protectionGroupId] : []);
      
      // Check if ALL selected PGs are tag-based
      const selectedPGs = protectionGroups.filter(pg => wavePgIds.includes(pg.protectionGroupId));
      const allTagBased = selectedPGs.length > 0 && selectedPGs.every(pg => 
        pg.serverSelectionTags && Object.keys(pg.serverSelectionTags).length > 0
      );
      
      // Only require serverIds if NOT tag-based
      return !allTagBased;
    });

    if (wavesNeedingServers.some(w => (w.serverIds || []).length === 0)) {
      newErrors.waves = 'All waves with non-tag-based Protection Groups must have at least one server';
    }

    // DRS Service Limits: Validate wave sizes (max 100 servers per wave) - only for non-tag-based
    const oversizedWaves = wavesNeedingServers
      .map((w, idx) => ({ name: w.name || `Wave ${idx + 1}`, count: (w.serverIds || []).length }))
      .filter(w => w.count > DRS_LIMITS.MAX_SERVERS_PER_JOB);
    
    if (oversizedWaves.length > 0) {
      const waveNames = oversizedWaves.map(w => `${w.name} (${w.count} servers)`).join(', ');
      newErrors.waves = `DRS limit: Max ${DRS_LIMITS.MAX_SERVERS_PER_JOB} servers per wave. Oversized: ${waveNames}`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      if (plan) {
        // Update existing plan - each wave uses its own Protection Group
        const updateData: UpdateRecoveryPlanRequest = {
          name: name,
          description: description,
          waves: waves.map((wave, index) => ({
            waveNumber: index,
            name: wave.name,
            description: wave.description || '',
            protectionGroupId: wave.protectionGroupId,  // Use wave's PG
            protectionGroupIds: wave.protectionGroupIds || (wave.protectionGroupId ? [wave.protectionGroupId] : []),
            serverIds: wave.serverIds || [],
            pauseBeforeWave: wave.pauseBeforeWave || false,  // Pause before starting this wave
            dependsOnWaves: wave.dependsOnWaves || []
          }))
        };
        // Include version for optimistic locking
        if (plan.version !== undefined) {
          updateData.version = plan.version;
        }
        const updatedPlan = await apiClient.updateRecoveryPlan(plan.id, updateData);
        onSave(updatedPlan);
      } else {
        // Create new plan - waves specify their own Protection Groups
        const createData: CreateRecoveryPlanRequest = {
          name: name,
          description: description,
          protectionGroupId: waves[0]?.protectionGroupId || '',  // Use first wave's PG as default
          waves: waves.map((wave, index) => ({
            waveNumber: index,
            name: wave.name,
            description: wave.description || '',
            protectionGroupId: wave.protectionGroupId,  // Use wave's PG
            protectionGroupIds: wave.protectionGroupIds || (wave.protectionGroupId ? [wave.protectionGroupId] : []),
            serverIds: wave.serverIds || [],
            pauseBeforeWave: wave.pauseBeforeWave || false,  // Pause before starting this wave
            dependsOnWaves: wave.dependsOnWaves || []
          }))
        };
        const newPlan = await apiClient.createRecoveryPlan(createData);
        onSave(newPlan);
      }

      handleClose();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'isVersionConflict' in err && err.isVersionConflict) {
        // Optimistic locking conflict - another user modified the resource
        setError('This recovery plan was modified by another user. Please close and reopen to get the latest version.');
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Failed to save recovery plan';
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setWaves([]);
    setErrors({});
    setError(null);
    onClose();
  };

  return (
    <Modal
      visible={open}
      onDismiss={handleClose}
      header={plan ? 'Edit Recovery Plan' : 'Create Recovery Plan'}
      size="large"
      footer={
        <Box float="right">
          <SpaceBetween direction="horizontal" size="xs">
            <Button onClick={handleClose} disabled={loading}>
              Cancel
            </Button>
            <PermissionAwareButton
              onClick={handleSubmit}
              variant="primary"
              disabled={loading || loadingGroups}
              loading={loading}
              requiredPermission={plan ? DRSPermission.MODIFY_RECOVERY_PLANS : DRSPermission.CREATE_RECOVERY_PLANS}
              fallbackTooltip={plan ? "Requires recovery plan modification permission" : "Requires recovery plan creation permission"}
            >
              {plan ? 'Update Plan' : 'Create Plan'}
            </PermissionAwareButton>
          </SpaceBetween>
        </Box>
      }
    >
      <form onSubmit={(e) => { 
        console.log('[RecoveryPlanDialog] Form submit prevented');
        e.preventDefault(); 
      }}>
        {loadingGroups ? (
          <LoadingState message="Loading protection groups..." />
        ) : (
          <SpaceBetween size="l">
            {/* Error Alert */}
            {error && (
              <Alert
                type="error"
                dismissible
                onDismiss={() => setError(null)}
              >
                {error}
              </Alert>
            )}

            {/* Basic Information Section */}
            <Container header={<Header variant="h2">Basic Information</Header>}>
              <SpaceBetween size="l">
                <FormField
                  label="Plan Name"
                  errorText={errors.name}
                >
                  <Input
                    value={name}
                    onChange={({ detail }) => setName(detail.value)}
                    placeholder="e.g., Production Recovery Plan"
                    disabled={loading}
                    autoFocus
                  />
                </FormField>

                <FormField
                  label="Description"
                  description="Optional description of this recovery plan"
                >
                  <Textarea
                    value={description}
                    onChange={({ detail }) => setDescription(detail.value)}
                    placeholder="e.g., Recovery plan for all production servers"
                    rows={2}
                    disabled={loading}
                  />
                </FormField>
              </SpaceBetween>
            </Container>

            {/* Wave Configuration */}
            <Container header={<Header variant="h2">Wave Configuration</Header>}>
              <SpaceBetween size="l">
                <WaveConfigEditor
                  waves={waves}
                  protectionGroupId=""
                  protectionGroups={protectionGroups}
                  onChange={(newWaves) => {
                    console.log('[RecoveryPlanDialog] WaveConfigEditor onChange called with', newWaves.length, 'waves');
                    setWaves(newWaves);
                  }}
                />
                {errors.waves && (
                  <Alert type="error">
                    {errors.waves}
                  </Alert>
                )}
              </SpaceBetween>
            </Container>
          </SpaceBetween>
        )}
      </form>
    </Modal>
  );
};
