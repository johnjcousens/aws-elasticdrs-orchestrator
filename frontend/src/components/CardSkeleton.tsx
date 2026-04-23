// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * Loading spinner used in place of card-based skeleton placeholders.
 * CloudScape does not provide a skeleton component, so a centered spinner
 * is shown while card layouts load.
 */

import type { ReactElement } from 'react';
import { Spinner } from '@cloudscape-design/components';

export const CardSkeleton = (): ReactElement => (
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
