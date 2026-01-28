/**
 * CardSkeleton - Loading placeholder for card layouts
 * 
 * Provides a loading placeholder for card-based content displays.
 * Used for execution cards and other card layouts during loading.
 * 
 * Note: CloudScape doesn't have skeleton components, so this uses Spinner instead.
 */

import type { ReactElement } from 'react';
import { Spinner } from '@cloudscape-design/components';

interface CardSkeletonProps {
  /** Number of skeleton cards to display (default: 3) - Not used in CloudScape version */
  count?: number;
  /** Show action buttons skeleton area (default: true) - Not used in CloudScape version */
  showActions?: boolean;
  /** Show progress bar skeleton (default: false) - Not used in CloudScape version */
  showProgress?: boolean;
}

/**
 * CardSkeleton Component
 * 
 * Displays loading spinner for card-based layouts.
 * CloudScape doesn't have skeleton components, so this uses a centered spinner.
 * 
 * @param count - Number of skeleton cards to display (default: 3) - Not used in CloudScape version
 * @param showActions - Show action buttons skeleton area (default: true) - Not used in CloudScape version
 * @param showProgress - Show progress bar skeleton (default: false) - Not used in CloudScape version
 * 
 * @example
 * ```tsx
 * {loading ? (
 *   <CardSkeleton count={5} showProgress={true} />
 * ) : (
 *   <SpaceBetween size="m">
 *     {items.map(item => <Container>...</Container>)}
 *   </SpaceBetween>
 * )}
 * ```
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const CardSkeleton = (props: CardSkeletonProps = {}): ReactElement => {
  // CloudScape doesn't have skeleton components, use spinner instead
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '200px',
        gap: '16px',
      }}
    >
      <Spinner size="large" />
      <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
        Loading...
      </span>
    </div>
  );
};
