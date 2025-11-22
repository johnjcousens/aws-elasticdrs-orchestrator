import type { ReactElement } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { Box, Paper, Fade, useMediaQuery, useTheme } from '@mui/material';
import { DataTableSkeleton } from './DataTableSkeleton';
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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));

  // Filter columns for mobile - hide columns marked with hide property
  const responsiveColumns = isMobile
    ? columns.filter((col) => !(col as any).hideOnMobile)
    : columns;

  // Show loading state with skeleton
  if (loading) {
    return <DataTableSkeleton rows={10} height={height} />;
  }

  // Show error state with retry option
  if (error) {
    return <ErrorState error={error} onRetry={onRetry} />;
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
    <Fade in={true} timeout={300}>
      <Paper 
        sx={{ 
          height: isMobile ? 'auto' : height, 
          width: '100%', 
          overflow: 'hidden' 
        }}
      >
        <DataGrid
          rows={rows}
          columns={responsiveColumns}
          initialState={{
            pagination: {
              paginationModel: { pageSize, page: 0 },
            },
          }}
          pageSizeOptions={isMobile ? [10, 25] : [10, 25, 50, 100]}
          checkboxSelection={false}
          disableRowSelectionOnClick
          density={isMobile ? 'compact' : 'standard'}
          sx={{
            // AWS theme styling for headers
            '& .MuiDataGrid-columnHeaders': {
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              fontWeight: 600,
              fontSize: isMobile ? '0.75rem' : '0.875rem',
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
              minHeight: isMobile ? '48px !important' : 'auto',
              maxHeight: isMobile ? '48px !important' : 'auto',
            },
            // Cell styling
            '& .MuiDataGrid-cell': {
              '&:focus': {
                outline: 'none',
              },
              '&:focus-within': {
                outline: 'none',
              },
              fontSize: isMobile ? '0.75rem' : '0.875rem',
              padding: isMobile ? '4px 8px' : '8px 16px',
            },
            // Footer styling
            '& .MuiDataGrid-footerContainer': {
              backgroundColor: 'background.paper',
              borderTop: '1px solid',
              borderTopColor: 'divider',
              minHeight: isMobile ? '48px' : 'auto',
            },
            // Pagination styling
            '& .MuiTablePagination-root': {
              color: 'text.primary',
              fontSize: isMobile ? '0.75rem' : '0.875rem',
            },
            // Pagination toolbar mobile optimization
            '& .MuiTablePagination-toolbar': {
              minHeight: isMobile ? '48px' : '52px',
              paddingLeft: isMobile ? '8px' : '16px',
              paddingRight: isMobile ? '4px' : '8px',
            },
            // Pagination select mobile optimization
            '& .MuiTablePagination-select': {
              fontSize: isMobile ? '0.75rem' : '0.875rem',
            },
            // Pagination display text mobile optimization
            '& .MuiTablePagination-displayedRows': {
              fontSize: isMobile ? '0.75rem' : '0.875rem',
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
    </Fade>
  );
};
