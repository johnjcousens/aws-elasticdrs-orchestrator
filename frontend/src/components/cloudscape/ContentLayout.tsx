/**
 * CloudScape ContentLayout Wrapper
 * 
 * Provides consistent page content layout with standardized spacing,
 * headers, and description sections.
 */

import React, { type ReactNode } from 'react';
import {
  ContentLayout as CloudScapeContentLayout,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';

interface ContentLayoutProps {
  children: ReactNode;
  header?: string | ReactNode;
  description?: string;
  actions?: ReactNode;
  disableOverlap?: boolean;
}

/**
 * ContentLayout Component
 * 
 * Wraps page content with CloudScape ContentLayout providing:
 * - Consistent page headers
 * - Description sections
 * - Action buttons in header
 * - Standardized spacing
 */
export const ContentLayout: React.FC<ContentLayoutProps> = ({
  children,
  header,
  description,
  actions,
  disableOverlap = false,
}) => {
  return (
    <CloudScapeContentLayout
      header={
        header ? (
          typeof header === 'string' ? (
            <Header
              variant="h1"
              description={description}
              actions={actions}
            >
              {header}
            </Header>
          ) : (
            header
          )
        ) : undefined
      }
      disableOverlap={disableOverlap}
    >
      <SpaceBetween size="l">
        {children}
      </SpaceBetween>
    </CloudScapeContentLayout>
  );
};
