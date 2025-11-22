/**
 * Recovery Plan Dialog Component
 * 
 * Dialog for creating and editing recovery plans with protection group
 * selection and wave configuration.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Alert,
  Box,
  Typography,
  Divider,
  Autocomplete,
  Chip,
} from '@mui/material';
import { LoadingState } from './LoadingState';
import { WaveConfigEditor } from './WaveConfigEditor';
import { ConfirmDialog } from './ConfirmDialog';
import apiClient from '../services/api';
import type { RecoveryPlan, ProtectionGroup, Wave } from '../types';

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
            ExecutionType: wave.executionType,
            Dependencies: (wave.dependsOnWaves || []).map(depNum => ({
              DependsOnWaveId: `wave-${depNum}`
            }))
          }))
        };
        const updatedPlan = await apiClient.updateRecoveryPlan(plan.id, updateData as any);
        onSave(updatedPlan);
      } else {
        // Create new plan - VMware SRM model (waves specify their own Protection Groups)
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
            ExecutionType: wave.executionType,
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
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        {plan ? 'Edit Recovery Plan' : 'Create Recovery Plan'}
      </DialogTitle>

      <DialogContent dividers>
        {loadingGroups ? (
          <LoadingState message="Loading protection groups..." />
        ) : (
          <Stack spacing={3}>
            {/* Error Alert */}
            {error && (
              <Alert severity="error" onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {/* Basic Information Section */}
            <Box>
              <Typography variant="h6" gutterBottom>
                Basic Information
              </Typography>
              <Stack spacing={2}>
                <TextField
                  fullWidth
                  label="Plan Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  error={!!errors.name}
                  helperText={errors.name}
                  required
                  autoFocus
                />
                <TextField
                  fullWidth
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  multiline
                  rows={2}
                />
              </Stack>
            </Box>

            <Divider />

            {/* Wave Configuration */}
            <Box>
              <WaveConfigEditor
                waves={waves}
                protectionGroupId=""
                protectionGroups={protectionGroups}
                onChange={setWaves}
              />
              {errors.waves && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {errors.waves}
                </Alert>
              )}
            </Box>
          </Stack>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || loadingGroups}
        >
          {loading ? 'Saving...' : plan ? 'Update Plan' : 'Create Plan'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
