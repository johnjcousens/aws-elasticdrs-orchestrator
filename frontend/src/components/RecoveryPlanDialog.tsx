/**
 * Recovery Plan Dialog Component
 * 
 * Dialog for creating and editing recovery plans with protection group
 * selection and wave configuration.
 */

import React, { useState, useEffect } from 'react';
import type { RecoveryPlan, ProtectionGroup, Wave } from '../types';
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
import { DRS_LIMITS, validateWaveSize } from '../services/drsQuotaService';

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

  // Populate form when editing
  useEffect(() => {
    if (plan && protectionGroups.length > 0 && waves.length === 0) {
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
    } else if (!plan) {
      // Reset form for create mode
      setName('');
      setDescription('');
      setWaves([]);
    }
    setErrors({});
    setError(null);
  }, [plan, open, protectionGroups]);

  const fetchProtectionGroups = async () => {
    try {
      setLoadingGroups(true);
      const data = await apiClient.listProtectionGroups();
      setProtectionGroups(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load protection groups');
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

    if (waves.some(w => !w.protectionGroupId)) {
      newErrors.waves = 'All waves must have a Protection Group selected';
    }

    if (waves.some(w => w.serverIds.length === 0)) {
      newErrors.waves = 'All waves must have at least one server';
    }

    // DRS Service Limits: Validate wave sizes (max 100 servers per wave)
    const oversizedWaves = waves
      .map((w, idx) => ({ name: w.name || `Wave ${idx + 1}`, count: w.serverIds.length }))
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
        const updateData = {
          PlanName: name,
          Description: description,
          Waves: waves.map((wave, index) => ({
            WaveId: `wave-${index}`,
            WaveName: wave.name,
            WaveDescription: wave.description || '',
            ExecutionOrder: index,
            ProtectionGroupId: wave.protectionGroupId,  // Use wave's PG
            ServerIds: wave.serverIds,
            PauseBeforeWave: wave.pauseBeforeWave || false,  // Pause before starting this wave
            Dependencies: (wave.dependsOnWaves || []).map(depNum => ({
              DependsOnWaveId: `wave-${depNum}`
            }))
          }))
        };
        const updatedPlan = await apiClient.updateRecoveryPlan(plan.id, updateData as any);
        onSave(updatedPlan);
      } else {
        // Create new plan - waves specify their own Protection Groups
        const createData = {
          PlanName: name,
          Description: description,
          Waves: waves.map((wave, index) => ({
            WaveId: `wave-${index}`,
            WaveName: wave.name,
            WaveDescription: wave.description || '',
            ExecutionOrder: index,
            ProtectionGroupId: wave.protectionGroupId,  // Use wave's PG
            ServerIds: wave.serverIds,
            PauseBeforeWave: wave.pauseBeforeWave || false,  // Pause before starting this wave
            Dependencies: (wave.dependsOnWaves || []).map(depNum => ({
              DependsOnWaveId: `wave-${depNum}`
            }))
          }))
        };
        const newPlan = await apiClient.createRecoveryPlan(createData as any);
        onSave(newPlan);
      }

      handleClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save recovery plan');
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
            <Button
              onClick={handleSubmit}
              variant="primary"
              disabled={loading || loadingGroups}
              loading={loading}
            >
              {plan ? 'Update Plan' : 'Create Plan'}
            </Button>
          </SpaceBetween>
        </Box>
      }
    >
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
                onChange={setWaves}
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
    </Modal>
  );
};
