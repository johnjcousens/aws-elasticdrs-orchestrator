/**
 * Wave Configuration Editor Component
 * 
 * Allows creation and editing of recovery waves with server selection,
 * execution type, dependencies, and configuration options.
 */

import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  IconButton,
  Chip,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import { ServerSelector } from './ServerSelector';
import type { Wave } from '../types';

interface WaveConfigEditorProps {
  waves: Wave[];
  protectionGroupId: string;
  onChange: (waves: Wave[]) => void;
  readonly?: boolean;
}

/**
 * Wave Configuration Editor Component
 * 
 * Provides UI for configuring multiple recovery waves with dependencies.
 */
export const WaveConfigEditor: React.FC<WaveConfigEditorProps> = ({
  waves,
  protectionGroupId,
  onChange,
  readonly = false,
}) => {
  const [expandedWave, setExpandedWave] = useState<number | null>(waves.length > 0 ? 0 : null);

  const handleAddWave = () => {
    const newWave: Wave = {
      waveNumber: waves.length,
      name: `Wave ${waves.length + 1}`,
      description: '',
      serverIds: [],
      executionType: 'sequential',
      dependsOnWaves: [],
    };
    onChange([...waves, newWave]);
    setExpandedWave(waves.length);
  };

  const handleRemoveWave = (waveNumber: number) => {
    const updatedWaves = waves
      .filter(w => w.waveNumber !== waveNumber)
      .map((w, index) => ({
        ...w,
        waveNumber: index,
        // Update dependencies to reflect removed wave
        dependsOnWaves: (w.dependsOnWaves || [])
          .filter(dep => dep !== waveNumber)
          .map(dep => dep > waveNumber ? dep - 1 : dep),
      }));
    onChange(updatedWaves);
    setExpandedWave(null);
  };

  const handleMoveWave = (waveNumber: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && waveNumber === 0) ||
      (direction === 'down' && waveNumber === waves.length - 1)
    ) {
      return;
    }

    const newIndex = direction === 'up' ? waveNumber - 1 : waveNumber + 1;
    const updatedWaves = [...waves];
    [updatedWaves[waveNumber], updatedWaves[newIndex]] = [updatedWaves[newIndex], updatedWaves[waveNumber]];
    
    // Renumber waves and update dependencies
    const renumberedWaves = updatedWaves.map((w, index) => ({
      ...w,
      waveNumber: index,
      dependsOnWaves: (w.dependsOnWaves || []).map(dep => {
        if (dep === waveNumber) return newIndex;
        if (dep === newIndex) return waveNumber;
        return dep;
      }),
    }));

    onChange(renumberedWaves);
    setExpandedWave(newIndex);
  };

  const handleUpdateWave = (waveNumber: number, field: keyof Wave, value: any) => {
    const updatedWaves = waves.map(w =>
      w.waveNumber === waveNumber ? { ...w, [field]: value } : w
    );
    onChange(updatedWaves);
  };

  const getAvailableDependencies = (currentWaveNumber: number): number[] => {
    // Waves can only depend on previous waves to prevent circular dependencies
    return Array.from({ length: currentWaveNumber }, (_, i) => i);
  };

  if (!protectionGroupId) {
    return (
      <Alert severity="warning">
        Please select a protection group before configuring waves.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h6">Wave Configuration</Typography>
        {!readonly && (
          <Button
            variant="outlined"
            size="small"
            startIcon={<AddIcon />}
            onClick={handleAddWave}
          >
            Add Wave
          </Button>
        )}
      </Stack>

      {/* Waves list */}
      {waves.length === 0 ? (
        <Alert severity="info">
          No waves configured. Add at least one wave to define the recovery sequence.
        </Alert>
      ) : (
        <Stack spacing={2}>
          {waves.map((wave) => (
            <Accordion
              key={wave.waveNumber}
              expanded={expandedWave === wave.waveNumber}
              onChange={() => setExpandedWave(expandedWave === wave.waveNumber ? null : wave.waveNumber)}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ width: '100%', pr: 2 }}>
                  <Typography variant="body1" sx={{ fontWeight: 500, minWidth: 100 }}>
                    {wave.name}
                  </Typography>
                  <Chip
                    label={`${wave.serverIds.length} server${wave.serverIds.length !== 1 ? 's' : ''}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  <Chip
                    label={wave.executionType}
                    size="small"
                    color="secondary"
                    variant="outlined"
                  />
                  {!readonly && (
                    <Box sx={{ ml: 'auto', display: 'flex', gap: 0.5 }}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMoveWave(wave.waveNumber, 'up');
                        }}
                        disabled={wave.waveNumber === 0}
                      >
                        <ArrowUpwardIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleMoveWave(wave.waveNumber, 'down');
                        }}
                        disabled={wave.waveNumber === waves.length - 1}
                      >
                        <ArrowDownwardIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveWave(wave.waveNumber);
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  )}
                </Stack>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={3}>
                  {/* Basic Information */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Basic Information
                    </Typography>
                    <Stack spacing={2}>
                      <TextField
                        fullWidth
                        label="Wave Name"
                        value={wave.name}
                        onChange={(e) => handleUpdateWave(wave.waveNumber, 'name', e.target.value)}
                        disabled={readonly}
                        required
                      />
                      <TextField
                        fullWidth
                        label="Description"
                        value={wave.description || ''}
                        onChange={(e) => handleUpdateWave(wave.waveNumber, 'description', e.target.value)}
                        disabled={readonly}
                        multiline
                        rows={2}
                      />
                    </Stack>
                  </Box>

                  <Divider />

                  {/* Execution Configuration */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Execution Configuration
                    </Typography>
                    <Stack spacing={2}>
                      <FormControl fullWidth disabled={readonly}>
                        <InputLabel>Execution Type</InputLabel>
                        <Select
                          value={wave.executionType}
                          label="Execution Type"
                          onChange={(e) => handleUpdateWave(wave.waveNumber, 'executionType', e.target.value)}
                        >
                          <MenuItem value="sequential">Sequential (one server at a time)</MenuItem>
                          <MenuItem value="parallel">Parallel (all servers simultaneously)</MenuItem>
                        </Select>
                      </FormControl>

                      {getAvailableDependencies(wave.waveNumber).length > 0 && (
                        <FormControl fullWidth disabled={readonly}>
                          <InputLabel>Depends On Waves</InputLabel>
                          <Select
                            multiple
                            value={wave.dependsOnWaves || []}
                            label="Depends On Waves"
                            onChange={(e) => handleUpdateWave(wave.waveNumber, 'dependsOnWaves', e.target.value)}
                            renderValue={(selected) => (
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {(selected as number[]).map((value) => (
                                  <Chip key={value} label={`Wave ${value + 1}`} size="small" />
                                ))}
                              </Box>
                            )}
                          >
                            {getAvailableDependencies(wave.waveNumber).map((waveNum) => (
                              <MenuItem key={waveNum} value={waveNum}>
                                Wave {waveNum + 1} - {waves[waveNum].name}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      )}
                    </Stack>
                  </Box>

                  <Divider />

                  {/* Server Selection */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom sx={{ mb: 2 }}>
                      Server Selection
                    </Typography>
                    <ServerSelector
                      protectionGroupId={protectionGroupId}
                      selectedServerIds={wave.serverIds}
                      onChange={(serverIds) => handleUpdateWave(wave.waveNumber, 'serverIds', serverIds)}
                      readonly={readonly}
                    />
                  </Box>
                </Stack>
              </AccordionDetails>
            </Accordion>
          ))}
        </Stack>
      )}

      {/* Validation Messages */}
      {waves.length > 0 && waves.some(w => w.serverIds.length === 0) && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Some waves have no servers selected. Each wave must include at least one server.
        </Alert>
      )}
    </Box>
  );
};
