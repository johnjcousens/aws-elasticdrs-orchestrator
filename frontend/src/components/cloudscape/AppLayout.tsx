/**
 * CloudScape AppLayout Wrapper
 * 
 * Provides consistent AWS console-style layout for all pages.
 * Includes navigation, breadcrumbs, notifications, and content area.
 */

import React, { useState, type ReactNode } from 'react';
import {
  AppLayout as CloudScapeAppLayout,
  SideNavigation,
  type SideNavigationProps,
  BreadcrumbGroup,
  Flashbar,
  TopNavigation,
} from '@cloudscape-design/components';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { useSettings } from '../../contexts/SettingsContext';
import { SettingsModal } from '../SettingsModal';
import { AccountSelector } from '../AccountSelector';

interface AppLayoutProps {
  children: ReactNode;
  breadcrumbs?: Array<{ text: string; href: string }>;
  navigationHide?: boolean;
  toolsHide?: boolean;
}

/**
 * AppLayout Component
 * 
 * Wraps page content with CloudScape AppLayout providing:
 * - Top navigation with user menu and logout
 * - Side navigation with React Router integration
 * - Breadcrumb navigation
 * - Notification flashbar
 * - Consistent spacing and layout
 */
export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  breadcrumbs = [],
  navigationHide = false,
  toolsHide = true,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, signOut } = useAuth();
  const { notifications } = useNotifications();
  const { settings, updateSettings, openSettingsModal, settingsModalVisible, settingsModalTab, closeSettingsModal } = useSettings();
  const [navigationOpen, setNavigationOpen] = useState(true);

  // Toggle theme between light and dark
  const toggleTheme = () => {
    const newTheme = settings.theme === 'dark' ? 'light' : 'dark';
    updateSettings({ theme: newTheme });
  };

  // Navigation items
  const navigationItems = [
    { type: 'link', text: 'Dashboard', href: '/' },
    { type: 'divider' },
    { type: 'link', text: 'Getting Started', href: '/getting-started' },
    { type: 'link', text: 'Protection Groups', href: '/protection-groups' },
    { type: 'link', text: 'Recovery Plans', href: '/recovery-plans' },
    { type: 'link', text: 'History', href: '/executions' },
  ];

  // Handle navigation
  const handleNavigationFollow = (event: { preventDefault: () => void; detail: { href: string } }) => {
    event.preventDefault();
    navigate(event.detail.href);
  };

  // Handle breadcrumb navigation
  const handleBreadcrumbFollow = (event: { preventDefault: () => void; detail: { href: string } }) => {
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
      {/* Top Navigation Bar - AWS Console Style */}
      <div id="top-nav" style={{ position: 'sticky', top: 0, zIndex: 1002 }}>
        <TopNavigation
          identity={{
            href: '/',
            title: 'Elastic Disaster Recovery Orchestrator',
            logo: {
              src: '/aws-logo.png',
              alt: 'AWS',
            },
            onFollow: (e) => {
              e.preventDefault();
              navigate('/');
            },
          }}
          utilities={[
            {
              type: 'button',
              iconName: settings.theme === 'dark' ? 'view-full' : 'view-vertical',
              text: settings.theme === 'dark' ? 'Light Mode' : 'Dark Mode',
              ariaLabel: settings.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode',
              disableUtilityCollapse: false,
              onClick: toggleTheme,
            },
            {
              type: 'button',
              iconName: 'notification',
              ariaLabel: 'Notifications',
              badge: false,
              disableUtilityCollapse: false,
            },
            {
              type: 'button',
              iconName: 'settings',
              ariaLabel: 'Settings',
              disableUtilityCollapse: false,
              onClick: () => openSettingsModal(),
            },
            {
              type: 'menu-dropdown',
              text: user?.email || user?.username || 'User',
              iconName: 'user-profile',
              items: [
                { id: 'profile', text: 'Profile', disabled: true },
                { id: 'preferences', text: 'Preferences', disabled: true },
                { id: 'signout', text: 'Sign out' },
              ],
              onItemClick: ({ detail }) => {
                if (detail.id === 'signout') {
                  handleSignOut();
                }
              },
            },
          ]}
          search={<AccountSelector />}
        />
      </div>

      {/* Main App Layout */}
      <CloudScapeAppLayout
        navigation={
          !navigationHide ? (
            <SideNavigation
              activeHref={location.pathname}
              items={navigationItems as SideNavigationProps.Item[]}
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
        notifications={<Flashbar items={notifications} />}
        content={children}
        toolsHide={toolsHide}
        navigationHide={navigationHide}
        navigationOpen={navigationOpen}
        onNavigationChange={({ detail }) => setNavigationOpen(detail.open)}
        navigationWidth={280}
        contentType="default"
        headerSelector="#top-nav"
      />

      {/* Settings Modal */}
      <SettingsModal
        visible={settingsModalVisible}
        onDismiss={closeSettingsModal}
        initialTab={settingsModalTab || undefined}
      />
    </>
  );
};