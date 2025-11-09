/**
 * Tag Filter Editor Component
 * 
 * Allows users to add, edit, and remove tag filters for protection groups.
 * Each filter consists of a key and multiple possible values.
 */

import React from 'react';
import {
  Box,
  Button,
  IconButton,
  TextField,
  Typography,
  Paper,
  Stack,
  Chip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import type { TagFilter } from '../types';

interface TagFilterEditorProps {
  filters: TagFilter[];
  onChange: (filters: TagFilter[]) => void;
  error?: string;
}

/**
 * Tag Filter Editor Component
 * 
 * Provides UI for managing tag filters with key-value pairs.
 * Supports adding/removing filters and multiple values per key.
 */
export const TagFilterEditor: React.FC<TagFilterEditorProps> = ({
  filters,
  onChange,
  error,
}) => {
  const handleAddFilter = () => {
    onChange([...filters, { key: '', values: [''] }]);
  };

  const handleRemoveFilter = (index: number) => {
    onChange(filters.filter((_, i) => i !== index));
  };

  const handleKeyChange = (index: number, key: string) => {
    const updated = [...filters];
    updated[index] = { ...updated[index], key };
    onChange(updated);
  };

  const handleAddValue = (filterIndex: number) => {
    const updated = [...filters];
    updated[filterIndex] = {
      ...updated[filterIndex],
      values: [...updated[filterIndex].values, ''],
    };
    onChange(updated);
  };

  const handleRemoveValue = (filterIndex: number, valueIndex: number) => {
    const updated = [...filters];
    updated[filterIndex] = {
      ...updated[filterIndex],
      values: updated[filterIndex].values.filter((_, i) => i !== valueIndex),
    };
    onChange(updated);
  };

  const handleValueChange = (filterIndex: number, valueIndex: number, value: string) => {
    const updated = [...filters];
    updated[filterIndex] = {
      ...updated[filterIndex],
      values: updated[filterIndex].values.map((v, i) => (i === valueIndex ? value : v)),
    };
    onChange(updated);
  };

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Tag Filters
        </Typography>
        <Button
          size="small"
          startIcon={<AddIcon />}
          onClick={handleAddFilter}
        >
          Add Filter
        </Button>
      </Stack>

      {error && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}

      {filters.length === 0 ? (
        <Paper variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            No tag filters defined
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Add tag filters to match servers based on their tags
          </Typography>
        </Paper>
      ) : (
        <Stack spacing={2}>
          {filters.map((filter, filterIndex) => (
            <Paper key={filterIndex} variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={2}>
                {/* Filter Key */}
                <Stack direction="row" spacing={1} alignItems="flex-start">
                  <TextField
                    fullWidth
                    size="small"
                    label="Tag Key"
                    placeholder="e.g., Environment"
                    value={filter.key}
                    onChange={(e) => handleKeyChange(filterIndex, e.target.value)}
                    error={filter.key === ''}
                    helperText={filter.key === '' ? 'Tag key is required' : ''}
                  />
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleRemoveFilter(filterIndex)}
                    title="Remove filter"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Stack>

                {/* Filter Values */}
                <Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    Tag Values (servers matching any of these values will be included)
                  </Typography>
                  <Stack spacing={1}>
                    {filter.values.map((value, valueIndex) => (
                      <Stack key={valueIndex} direction="row" spacing={1}>
                        <TextField
                          fullWidth
                          size="small"
                          placeholder="e.g., production"
                          value={value}
                          onChange={(e) => handleValueChange(filterIndex, valueIndex, e.target.value)}
                          error={value === ''}
                          helperText={value === '' ? 'Value is required' : ''}
                        />
                        <IconButton
                          size="small"
                          onClick={() => handleRemoveValue(filterIndex, valueIndex)}
                          title="Remove value"
                          disabled={filter.values.length === 1}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Stack>
                    ))}
                    <Button
                      size="small"
                      startIcon={<AddIcon />}
                      onClick={() => handleAddValue(filterIndex)}
                      sx={{ alignSelf: 'flex-start' }}
                    >
                      Add Value
                    </Button>
                  </Stack>
                </Box>

                {/* Preview */}
                {filter.key && filter.values.some(v => v) && (
                  <Box sx={{ pt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Preview:
                    </Typography>
                    <Box sx={{ mt: 0.5 }}>
                      <Chip
                        label={`${filter.key}: ${filter.values.filter(v => v).join(', ')}`}
                        size="small"
                      />
                    </Box>
                  </Box>
                )}
              </Stack>
            </Paper>
          ))}
        </Stack>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
        Servers must match at least one value from each tag filter to be included in this protection group.
      </Typography>
    </Box>
  );
};
