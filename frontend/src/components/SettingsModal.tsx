/**
 * Settings Modal Component
 * 
 * Provides configuration export/import functionality accessed via the Settings gear icon.
 * Contains tabs for Account Management, Export, and Import.
 * Import/Export tabs are only visible to users with appropriate permissions.
 */

import React, { useState, useMemo } from 'react';
import {
  Modal,
  Tabs,
  SpaceBetween,
  Box,
} from '@cloudscape-design/components';
import { ConfigExportPanel } from './ConfigExportPanel';
import { ConfigImportPanel } from './ConfigImportPanel';
import { TagSyncConfigPanel } from './TagSyncConfigPanel';
import AccountManagementPanel from './AccountManagementPanel';
import { usePermissions } from '../contexts/PermissionsContext';
import { DRSPermission } from '../types/permissions';

interface SettingsModalProps {
  visible: boolean;
  onDismiss: () => void;
  initialTab?: string;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  visible,
  onDismiss,
  initialTab,
}) => {
  const [activeTab, setActiveTab] = useState(initialTab || 'accounts');
  const { hasPermission } = usePermissions();

  // Update active tab when initialTab prop changes
  React.useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab);
    }
  }, [initialTab]);

  // Check permissions for import/export functionality
  const canExport = hasPermission(DRSPermission.EXPORT_CONFIGURATION);
  const canImport = hasPermission(DRSPermission.IMPORT_CONFIGURATION);

  // Build tabs array based on permissions - memoized to prevent useEffect dependency changes
  const tabs = useMemo(() => {
    const baseTabs = [
      {
        id: 'accounts',
        label: 'Account Management',
        content: (
          <Box padding={{ top: 'm' }}>
            <AccountManagementPanel />
          </Box>
        ),
      },
      {
        id: 'tag-sync',
        label: 'Tag Sync',
        content: (
          <Box padding={{ top: 'm' }}>
            <TagSyncConfigPanel />
          </Box>
        ),
      },
    ];

    // Add Export tab if user has permission
    if (canExport) {
      baseTabs.push({
        id: 'export',
        label: 'Export Configuration',
        content: (
          <Box padding={{ top: 'm' }}>
            <ConfigExportPanel onExportComplete={onDismiss} />
          </Box>
        ),
      });
    }

    // Add Import tab if user has permission
    if (canImport) {
      baseTabs.push({
        id: 'import',
        label: 'Import Configuration',
        content: (
          <Box padding={{ top: 'm' }}>
            <ConfigImportPanel onImportComplete={onDismiss} />
          </Box>
        ),
      });
    }
    
    return baseTabs;
  }, [canExport, canImport, onDismiss]);

  // Reset active tab to 'accounts' if current tab is not available
  React.useEffect(() => {
    const availableTabIds = tabs.map(tab => tab.id);
    if (!availableTabIds.includes(activeTab)) {
      setActiveTab('accounts');
    }
  }, [activeTab, tabs]);

  return (
    <Modal
      visible={visible}
      onDismiss={onDismiss}
      header="Settings"
      size="large"
    >
      <SpaceBetween size="l">
        <Tabs
          activeTabId={activeTab}
          onChange={({ detail }: { detail: { activeTabId: string } }) => setActiveTab(detail.activeTabId)}
          tabs={tabs}
        />
      </SpaceBetween>
    </Modal>
  );
};