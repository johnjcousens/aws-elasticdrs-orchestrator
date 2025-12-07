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
  TopNavigation,
  type FlashbarProps,
} from '@cloudscape-design/components';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

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
 * - Top navigation with user menu and logout
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
  const { user, signOut } = useAuth();

  // Navigation items
  const navigationItems = [
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
    { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
    { type: 'link', text: 'History', href: '/executions' },
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

  // Handle logout
  const handleSignOut = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <>
      {/* Top Navigation Bar - AWS Orange Branding */}
      <div id="top-nav" style={{ position: 'sticky', top: 0, zIndex: 1002 }}>
        <style>
          {`
            #top-nav [class*="awsui_identity"] {
              font-family: "Amazon Ember", "Helvetica Neue", Roboto, Arial, sans-serif !important;
            }
            #top-nav header[class*="awsui_header"] {
              background: linear-gradient(90deg, #232F3E 0%, #FF9900 100%) !important;
            }
          `}
        </style>
        <TopNavigation
          identity={{
            href: '/',
            title: 'Amazon Web Services Elastic Disaster Recovery Orchestrator',
            logo: {
              src: 'https://d0.awsstatic.com/logos/powered-by-aws-white.png',
              alt: 'Powered by AWS',
            },
            onFollow: (e) => {
              e.preventDefault();
              navigate('/');
            },
          }}
          utilities={[
            {
              type: 'menu-dropdown',
              text: user?.email || user?.username || 'User',
              iconName: 'user-profile',
              items: [
                { id: 'profile', text: 'Profile', disabled: true },
                { id: 'signout', text: 'Sign out' },
              ],
              onItemClick: ({ detail }) => {
                if (detail.id === 'signout') {
                  handleSignOut();
                }
              },
            },
          ]}
        />
      </div>

      {/* Main App Layout */}
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
        headerSelector="#top-nav"
      />
    </>
  );
};
