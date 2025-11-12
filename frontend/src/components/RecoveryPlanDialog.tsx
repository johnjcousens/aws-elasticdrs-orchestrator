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
  const [protectionGroupId, setProtectionGroupId] = useState('');
  const [waves, setWaves] = useState<Wave[]>([]);
  const [protectionGroups, setProtectionGroups] = useState<ProtectionGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPgChangeConfirm, setShowPgChangeConfirm] = useState(false);
  const [pendingPgId, setPendingPgId] = useState<string>('');
  const [originalPgId, setOriginalPgId] = useState<string>('');

  // Load protection groups on mount
  useEffect(() => {
    if (open) {
      fetchProtectionGroups();
    }
  }, [open]);

  // Populate form when editing
  useEffect(() => {
    if (plan) {
      setName(plan.name);
      setDescription(plan.description || '');
      // Extract Protection Group ID from first wave (PG IDs are stored in waves, not at root)
      const firstWave = plan.waves?.[0];
      const pgId = firstWave?.ProtectionGroupId || '';
      setProtectionGroupId(pgId);
      setOriginalPgId(pgId); // Store original for comparison
      setWaves(plan.waves || []); // Default to empty array if undefined
    } else {
      // Reset form for create mode
      setName('');
      setDescription('');
      setProtectionGroupId('');
      setOriginalPgId('');
      setWaves([]);
    }
    setErrors({});
    setError(null);
  }, [plan, open]);

  const handleProtectionGroupChange = (newPgId: string) => {
    // If editing and PG is different from original, show confirmation
    if (plan && originalPgId && newPgId !== originalPgId) {
      setPendingPgId(newPgId);
      setShowPgChangeConfirm(true);
    } else {
      // New plan or same PG - just update
      setProtectionGroupId(newPgId);
    }
  };

  const handleConfirmPgChange = () => {
    // Apply the Protection Group change and reset all server selections in waves
    setProtectionGroupId(pendingPgId);
    
    // Clear serverIds from all waves (keeps wave structure)
    const clearedWaves = waves.map(wave => ({
      ...wave,
      serverIds: []
    }));
    setWaves(clearedWaves);
    
    setShowPgChangeConfirm(false);
    setPendingPgId('');
  };

  const handleCancelPgChange = () => {
    setShowPgChangeConfirm(false);
    setPendingPgId('');
  };

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

    if (!protectionGroupId) {
      newErrors.protectionGroupId = 'Protection group is required';
    }

    if (waves.length === 0) {
      newErrors.waves = 'At least one wave is required';
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
        // Update existing plan - transform waves to backend format
        const updateData = {
          PlanName: name,
          Description: description,
          Waves: waves.map((wave, index) => ({
            WaveId: `wave-${index}`,
            WaveName: wave.name,
            WaveDescription: wave.description || '',
            ExecutionOrder: index,
            ProtectionGroupId: protectionGroupId,
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
        // Create new plan - transform to backend format
        const createData = {
          PlanName: name,
          Description: description,
          AccountId: '777788889999', // TODO: Get from AWS config or user context
          Region: 'us-east-1', // TODO: Get from selected protection group
          Owner: 'demo-user', // TODO: Get from auth context
          RPO: '1h',  // Recovery Point Objective - 1 hour default
          RTO: '30m', // Recovery Time Objective - 30 minutes default
          Waves: waves.map((wave, index) => ({
            WaveId: `wave-${index}`,
            WaveName: wave.name,
            WaveDescription: wave.description || '',
            ExecutionOrder: index,
            ProtectionGroupId: protectionGroupId,
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
    setProtectionGroupId('');
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

            {/* Protection Group Selection */}
            <Box>
              <Typography variant="h6" gutterBottom>
                Protection Group
              </Typography>
              <FormControl
                fullWidth
                error={!!errors.protectionGroupId}
                required
              >
                <InputLabel>Protection Group</InputLabel>
                <Select
                  value={protectionGroupId}
                  label="Protection Group"
                  onChange={(e) => handleProtectionGroupChange(e.target.value)}
                >
                  {protectionGroups.map((group) => (
                    <MenuItem key={group.protectionGroupId} value={group.protectionGroupId}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
                {errors.protectionGroupId && (
                  <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                    {errors.protectionGroupId}
                  </Typography>
                )}
              </FormControl>
              {plan && (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Changing the Protection Group will clear all server selections from waves
                </Alert>
              )}
            </Box>

            <Divider />

            {/* Wave Configuration */}
            <Box>
              {protectionGroupId ? (
                <WaveConfigEditor
                  waves={waves}
                  protectionGroupId={protectionGroupId}
                  onChange={setWaves}
                />
              ) : (
                <Alert severity="info">
                  Select a protection group to configure waves
                </Alert>
              )}
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

      {/* Protection Group Change Confirmation Dialog */}
      <ConfirmDialog
        open={showPgChangeConfirm}
        title="Change Protection Group?"
        message="Changing the Protection Group will clear all server selections from waves. You will need to re-select servers for each wave. Do you want to continue?"
        onConfirm={handleConfirmPgChange}
        onCancel={handleCancelPgChange}
        confirmLabel="Change Protection Group"
        confirmColor="warning"
      />
    </Dialog>
  );
};
