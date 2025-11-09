/**
 * DataTableSkeleton - Skeleton loader for data tables
 * 
 * Provides a skeleton placeholder that matches the structure of Material-UI DataGrid.
 * Shows header row and configurable number of content rows.
 */

import type { ReactElement } from 'react';
import { Box, Paper, Skeleton, Stack } from '@mui/material';

interface DataTableSkeletonProps {
  rows?: number;
  height?: number;
}

/**
 * DataTableSkeleton Component
 * 
 * Displays a skeleton loader that mimics the structure of a data table.
 * Used during initial data fetching to improve perceived performance.
 * 
 * @param rows - Number of skeleton rows to display (default: 5)
 * @param height - Total height of the skeleton container (default: 600)
 * 
 * @example
 * ```tsx
 * {loading ? (
 *   <DataTableSkeleton rows={10} height={600} />
 * ) : (
 *   <DataGrid rows={data} columns={columns} />
 * )}
 * ```
 */
export const DataTableSkeleton = ({
  rows = 5,
  height = 600,
}: DataTableSkeletonProps): ReactElement => {
  return (
    <Paper
      sx={{
        height,
        width: '100%',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Table Header */}
      <Box
        sx={{
          backgroundColor: 'primary.main',
          p: 1.5,
          display: 'flex',
          gap: 2,
        }}
      >
        <Skeleton
          variant="rectangular"
          width="20%"
          height={24}
          sx={{ bgcolor: 'primary.light' }}
        />
        <Skeleton
          variant="rectangular"
          width="25%"
          height={24}
          sx={{ bgcolor: 'primary.light' }}
        />
        <Skeleton
          variant="rectangular"
          width="20%"
          height={24}
          sx={{ bgcolor: 'primary.light' }}
        />
        <Skeleton
          variant="rectangular"
          width="15%"
          height={24}
          sx={{ bgcolor: 'primary.light' }}
        />
        <Skeleton
          variant="rectangular"
          width="20%"
          height={24}
          sx={{ bgcolor: 'primary.light' }}
        />
      </Box>

      {/* Table Rows */}
      <Stack spacing={0} sx={{ flex: 1, p: 2 }}>
        {Array.from({ length: rows }).map((_, index) => (
          <Box
            key={index}
            sx={{
              display: 'flex',
              gap: 2,
              py: 1.5,
              borderBottom: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Skeleton variant="text" width="20%" height={32} />
            <Skeleton variant="text" width="25%" height={32} />
            <Skeleton variant="text" width="20%" height={32} />
            <Skeleton variant="text" width="15%" height={32} />
            <Skeleton variant="text" width="20%" height={32} />
          </Box>
        ))}
      </Stack>

      {/* Table Footer (Pagination area) */}
      <Box
        sx={{
          borderTop: '1px solid',
          borderColor: 'divider',
          p: 2,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Skeleton variant="text" width={120} height={24} />
        <Skeleton variant="text" width={200} height={24} />
      </Box>
    </Paper>
  );
};
