/**
 * Protection Group Dialog Component
 * 
 * Modal dialog for creating and editing protection groups.
 * Includes form fields for name, description, and tag filters.
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Alert,
} from '@mui/material';
import { TagFilterEditor } from './TagFilterEditor';
import apiClient from '../services/api';
import type { ProtectionGroup, TagFilter } from '../types';

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
 * Validates inputs and handles API calls.
 */
export const ProtectionGroupDialog: React.FC<ProtectionGroupDialogProps> = ({
  open,
  group,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tagFilters, setTagFilters] = useState<TagFilter[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    name?: string;
    tagFilters?: string;
  }>({});

  const isEditMode = Boolean(group);

  // Initialize form when dialog opens or group changes
  useEffect(() => {
    if (open) {
      if (group) {
        // Edit mode - populate form with existing data
        setName(group.name);
        setDescription(group.description || '');
        setTagFilters(group.tagFilters.length > 0 ? group.tagFilters : []);
      } else {
        // Create mode - reset form
        setName('');
        setDescription('');
        setTagFilters([]);
      }
      setError(null);
      setValidationErrors({});
    }
  }, [open, group]);

  const validateForm = (): boolean => {
    const errors: { name?: string; tagFilters?: string } = {};

    // Validate name
    if (!name.trim()) {
      errors.name = 'Name is required';
    }

    // Validate tag filters
    if (tagFilters.length === 0) {
      errors.tagFilters = 'At least one tag filter is required';
    } else {
      // Check each filter has a key and at least one value
      const invalidFilters = tagFilters.some(
        filter => !filter.key.trim() || filter.values.length === 0 || filter.values.every(v => !v.trim())
      );
      if (invalidFilters) {
        errors.tagFilters = 'All tag filters must have a key and at least one value';
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

      // Clean up tag filters - remove empty values
      const cleanedFilters = tagFilters.map(filter => ({
        key: filter.key.trim(),
        values: filter.values.filter(v => v.trim()).map(v => v.trim()),
      }));

      const groupData = {
        name: name.trim(),
        description: description.trim() || undefined,
        tagFilters: cleanedFilters,
      };

      let savedGroup: ProtectionGroup;

      if (isEditMode && group) {
        // Update existing group
        savedGroup = await apiClient.updateProtectionGroup(group.id, groupData);
      } else {
        // Create new group
        savedGroup = await apiClient.createProtectionGroup(groupData);
      }

      onSave(savedGroup);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save protection group');
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
    <Dialog 
      open={open} 
      onClose={handleCancel}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        {isEditMode ? 'Edit Protection Group' : 'Create Protection Group'}
      </DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {/* Name Field */}
          <TextField
            fullWidth
            label="Name"
            placeholder="e.g., Production Servers"
            value={name}
            onChange={(e) => setName(e.target.value)}
            error={Boolean(validationErrors.name)}
            helperText={validationErrors.name || 'A unique name for this protection group'}
            disabled={loading}
            sx={{ mb: 2 }}
          />

          {/* Description Field */}
          <TextField
            fullWidth
            label="Description"
            placeholder="e.g., All production servers in us-west-2"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            multiline
            rows={2}
            disabled={loading}
            helperText="Optional description of this protection group"
            sx={{ mb: 3 }}
          />

          {/* Tag Filters Editor */}
          <TagFilterEditor
            filters={tagFilters}
            onChange={setTagFilters}
            error={validationErrors.tagFilters}
          />
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button 
          onClick={handleCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading}
        >
          {loading ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create Group'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
