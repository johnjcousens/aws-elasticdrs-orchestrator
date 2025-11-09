/**
 * CardSkeleton - Skeleton loader for card layouts
 * 
 * Provides a skeleton placeholder for card-based content displays.
 * Used for execution cards and other card layouts during loading.
 */

import type { ReactElement } from 'react';
import { Card, CardContent, CardActions, Skeleton, Stack, Box } from '@mui/material';

interface CardSkeletonProps {
  /** Number of skeleton cards to display */
  count?: number;
  /** Whether to show action buttons skeleton */
  showActions?: boolean;
  /** Whether to show progress bar skeleton */
  showProgress?: boolean;
}

/**
 * CardSkeleton Component
 * 
 * Displays skeleton loaders that mimic the structure of Card components.
 * Used during initial data fetching for card-based layouts.
 * 
 * @param count - Number of skeleton cards to display (default: 3)
 * @param showActions - Show action buttons skeleton area (default: true)
 * @param showProgress - Show progress bar skeleton (default: false)
 * 
 * @example
 * ```tsx
 * {loading ? (
 *   <CardSkeleton count={5} showProgress={true} />
 * ) : (
 *   <Stack spacing={2}>
 *     {items.map(item => <Card>...</Card>)}
 *   </Stack>
 * )}
 * ```
 */
export const CardSkeleton = ({
  count = 3,
  showActions = true,
  showProgress = false,
}: CardSkeletonProps): ReactElement => {
  return (
    <Stack spacing={2}>
      {Array.from({ length: count }).map((_, index) => (
        <Card key={index}>
          <CardContent>
            {/* Title skeleton */}
            <Skeleton variant="text" width="60%" height={32} sx={{ mb: 2 }} />
            
            {/* Status badges and metadata row */}
            <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
              <Skeleton variant="rounded" width={80} height={24} />
              <Skeleton variant="text" width={120} height={24} />
              <Skeleton variant="text" width={100} height={24} />
            </Stack>

            {/* Progress bar (conditional) */}
            {showProgress && (
              <Box sx={{ mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
                  <Skeleton variant="text" width={60} height={20} />
                  <Skeleton variant="text" width={40} height={20} />
                </Stack>
                <Skeleton variant="rectangular" width="100%" height={8} sx={{ borderRadius: 1 }} />
              </Box>
            )}

            {/* Additional content lines */}
            <Skeleton variant="text" width="90%" height={20} />
            <Skeleton variant="text" width="75%" height={20} />
          </CardContent>

          {/* Action buttons skeleton (conditional) */}
          {showActions && (
            <CardActions>
              <Skeleton variant="rectangular" width={120} height={36} sx={{ borderRadius: 1 }} />
            </CardActions>
          )}
        </Card>
      ))}
    </Stack>
  );
};
