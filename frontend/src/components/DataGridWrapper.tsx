import type { ReactElement } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { Box, Paper } from '@mui/material';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';

interface DataGridWrapperProps {
  rows: GridRowsProp;
  columns: GridColDef[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  pageSize?: number;
  emptyMessage?: string;
  height?: number;
}

/**
 * DataGridWrapper - Reusable Material-UI DataGrid with AWS theme integration
 * 
 * Features:
 * - AWS-branded styling matching theme
 * - Built-in loading, error, and empty states
 * - Configurable pagination (default 10 rows per page)
 * - Column sorting and filtering
 * - Responsive design
 * 
 * @example
 * ```tsx
 * <DataGridWrapper
 *   rows={data}
 *   columns={columnDefs}
 *   loading={loading}
 *   error={error}
 *   onRetry={fetchData}
 *   emptyMessage="No items found"
 * />
 * ```
 */
export const DataGridWrapper = ({
  rows,
  columns,
  loading = false,
  error = null,
  onRetry,
  pageSize = 10,
  emptyMessage = 'No data available',
  height = 600,
}: DataGridWrapperProps): ReactElement => {
  // Show loading state
  if (loading) {
    return <LoadingState />;
  }

  // Show error state with retry option
  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  // Show empty state when no rows
  if (rows.length === 0) {
    return (
      <Paper
        sx={{
          p: 4,
          textAlign: 'center',
          backgroundColor: 'background.paper',
        }}
      >
        <Box sx={{ color: 'text.secondary' }}>
          {emptyMessage}
        </Box>
      </Paper>
    );
  }

  return (
    <Paper sx={{ height, width: '100%', overflow: 'hidden' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: { pageSize, page: 0 },
          },
        }}
        pageSizeOptions={[10, 25, 50, 100]}
        checkboxSelection={false}
        disableRowSelectionOnClick
        sx={{
          // AWS theme styling for headers
          '& .MuiDataGrid-columnHeaders': {
            backgroundColor: 'primary.main',
            color: 'primary.contrastText',
            fontWeight: 600,
            fontSize: '0.875rem',
          },
          // Header cell styling
          '& .MuiDataGrid-columnHeader': {
            '&:focus': {
              outline: 'none',
            },
            '&:focus-within': {
              outline: 'none',
            },
          },
          // Column separator styling
          '& .MuiDataGrid-columnSeparator': {
            color: 'primary.contrastText',
            opacity: 0.5,
          },
          // Row hover effect
          '& .MuiDataGrid-row': {
            '&:hover': {
              backgroundColor: 'action.hover',
            },
          },
          // Cell styling
          '& .MuiDataGrid-cell': {
            '&:focus': {
              outline: 'none',
            },
            '&:focus-within': {
              outline: 'none',
            },
          },
          // Footer styling
          '& .MuiDataGrid-footerContainer': {
            backgroundColor: 'background.paper',
            borderTop: '1px solid',
            borderTopColor: 'divider',
          },
          // Pagination styling
          '& .MuiTablePagination-root': {
            color: 'text.primary',
          },
          // Sort icon styling
          '& .MuiDataGrid-sortIcon': {
            color: 'primary.contrastText',
            opacity: 0.7,
          },
          // Menu icon styling
          '& .MuiDataGrid-menuIcon': {
            color: 'primary.contrastText',
            opacity: 0.7,
          },
          // No rows overlay
          '& .MuiDataGrid-overlay': {
            backgroundColor: 'background.paper',
          },
        }}
      />
    </Paper>
  );
};
