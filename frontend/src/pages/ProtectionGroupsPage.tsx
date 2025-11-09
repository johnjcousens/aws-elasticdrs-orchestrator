/**
 * Protection Groups Page
 * 
 * Main page for managing DRS protection groups.
 * Displays list of groups with CRUD operations.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  IconButton,
  Chip,
  Stack,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { DateTimeDisplay } from '../components/DateTimeDisplay';
import apiClient from '../services/api';
import type { ProtectionGroup } from '../types';

/**
 * Protection Groups Page Component
 * 
 * Manages the display and CRUD operations for protection groups.
 */
export const ProtectionGroupsPage: React.FC = () => {
  const [groups, setGroups] = useState<ProtectionGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [groupToDelete, setGroupToDelete] = useState<ProtectionGroup | null>(null);

  // Fetch protection groups on mount
  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.listProtectionGroups();
      setGroups(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load protection groups');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (group: ProtectionGroup) => {
    setGroupToDelete(group);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!groupToDelete) return;

    try {
      await apiClient.deleteProtectionGroup(groupToDelete.id);
      setGroups(groups.filter(g => g.id !== groupToDelete.id));
      setDeleteDialogOpen(false);
      setGroupToDelete(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete protection group');
      setDeleteDialogOpen(false);
    }
  };

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setGroupToDelete(null);
  };

  if (loading) {
    return <LoadingState message="Loading protection groups..." />;
  }

  if (error) {
    return <ErrorState error={error} onRetry={fetchGroups} />;
  }

  return (
    <Box>
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Protection Groups
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Define groups of servers to protect together based on tags
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: Open create dialog */}}
        >
          Create Group
        </Button>
      </Stack>

      {/* Protection Groups Table */}
      {groups.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Protection Groups
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Create your first protection group to start organizing servers
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {/* TODO: Open create dialog */}}
          >
            Create Protection Group
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Tag Filters</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {groups.map((group) => (
                <TableRow key={group.id} hover>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {group.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {group.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1} flexWrap="wrap">
                      {group.tagFilters.map((filter, index) => (
                        <Chip
                          key={index}
                          label={`${filter.key}: ${filter.values.join(', ')}`}
                          size="small"
                          sx={{ mb: 0.5 }}
                        />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <DateTimeDisplay value={group.createdAt} format="relative" />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => {/* TODO: Open edit dialog */}}
                      title="Edit"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(group)}
                      title="Delete"
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Protection Group"
        message={
          groupToDelete
            ? `Are you sure you want to delete "${groupToDelete.name}"? This action cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        confirmColor="error"
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
      />
    </Box>
  );
};
