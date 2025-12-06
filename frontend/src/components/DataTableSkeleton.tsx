/**
 * DataTableSkeleton - Loading placeholder for data tables
 * 
 * Provides a loading placeholder for data tables.
 * CloudScape doesn't have skeleton components, so this uses Spinner.
 */

import type { ReactElement } from 'react';
import { Spinner } from '@cloudscape-design/components';

interface DataTableSkeletonProps {
  rows?: number;
  height?: number;
}

/**
 * DataTableSkeleton Component
 * 
 * Displays a loading spinner for data tables.
 * CloudScape doesn't have skeleton components, so this uses a centered spinner.
 * 
 * @param rows - Number of skeleton rows to display (default: 5) - Not used in CloudScape version
 * @param height - Total height of the skeleton container (default: 600)
 * 
 * @example
 * ```tsx
 * {loading ? (
 *   <DataTableSkeleton rows={10} height={600} />
 * ) : (
 *   <Table items={data} columnDefinitions={columns} />
 * )}
 * ```
 */
export const DataTableSkeleton = ({
  rows = 5,
  height = 600,
}: DataTableSkeletonProps): ReactElement => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: `${height}px`,
        width: '100%',
      }}
    >
      <Spinner size="large" />
      <span style={{ fontSize: '14px', color: '#5f6b7a', marginTop: '16px' }}>
        Loading table data...
      </span>
    </div>
  );
};
