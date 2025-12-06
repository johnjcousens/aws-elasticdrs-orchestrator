/**
 * CloudScape AppLayout Wrapper
 * 
 * Provides consistent AWS console-style layout for all pages.
 * Includes navigation, breadcrumbs, notifications, and content area.
 */

import React, { type ReactNode } from 'react';
import {
  AppLayout as CloudScapeAppLayout,
  SideNavigation,
  BreadcrumbGroup,
  Flashbar,
  type FlashbarProps,
} from '@cloudscape-design/components';
import { useNavigate, useLocation } from 'react-router-dom';

interface AppLayoutProps {
  children: ReactNode;
  breadcrumbs?: Array<{ text: string; href: string }>;
  notifications?: FlashbarProps.MessageDefinition[];
  navigationHide?: boolean;
  toolsHide?: boolean;
}

/**
 * AppLayout Component
 * 
 * Wraps page content with CloudScape AppLayout providing:
 * - Side navigation
 * - Breadcrumb navigation
 * - Notification flashbar
 * - Consistent spacing and layout
 */
export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  breadcrumbs = [],
  notifications = [],
  navigationHide = false,
  toolsHide = true,
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Navigation items
  const navigationItems = [
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
    { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
    { type: 'link', text: 'Executions', href: '/executions' },
    { type: 'divider' },
    { type: 'link', text: 'Settings', href: '/settings' },
  ];

  // Handle navigation
  const handleNavigationFollow = (event: any) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  // Handle breadcrumb navigation
  const handleBreadcrumbFollow = (event: any) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  return (
    <CloudScapeAppLayout
      navigation={
        !navigationHide ? (
          <SideNavigation
            activeHref={location.pathname}
            items={navigationItems as any}
            onFollow={handleNavigationFollow}
          />
        ) : undefined
      }
      breadcrumbs={
        breadcrumbs.length > 0 ? (
          <BreadcrumbGroup
            items={breadcrumbs}
            onFollow={handleBreadcrumbFollow}
          />
        ) : undefined
      }
      notifications={
        notifications.length > 0 ? (
          <Flashbar items={notifications} />
        ) : undefined
      }
      content={children}
      toolsHide={toolsHide}
      navigationHide={navigationHide}
      navigationWidth={280}
      contentType="default"
    />
  );
};
