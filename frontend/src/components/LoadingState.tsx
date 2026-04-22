// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * Centered loading spinner used as a page-level placeholder while data
 * is being fetched. Displayed inside a minimum-height container so the
 * layout doesn't collapse before content arrives.
 */

import React from 'react';
import { Spinner } from '@cloudscape-design/components';

export interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
}) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '400px',
      gap: '16px',
    }}
  >
    <Spinner size="large" />
    <span style={{ fontSize: '14px', color: '#5f6b7a' }}>
      {message}
    </span>
  </div>
);
