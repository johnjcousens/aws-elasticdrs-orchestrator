/**
 * Settings Modal Component
 * 
 * Provides configuration export/import functionality accessed via the Settings gear icon.
 * Contains tabs for Export and Import operations.
 */

import React, { useState } from 'react';
import {
  Modal,
  Tabs,
  SpaceBetween,
  Box,
} from '@cloudscape-design/components';
import { ConfigExportPanel } from './ConfigExportPanel';
import { ConfigImportPanel } from './ConfigImportPanel';
import AccountManagementPanel from './AccountManagementPanel';

interface SettingsModalProps {
  visible: boolean;
  onDismiss: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  visible,
  onDismiss,
}) => {
  const [activeTab, setActiveTab] = useState('accounts');

  // Only render modal content when visible to prevent unnecessary API calls
  if (!visible) {
    return (
      <Modal
        visible={false}
        onDismiss={onDismiss}
        header="Settings"
        size="large"
      />
    );
  }

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
          onChange={({ detail }) => setActiveTab(detail.activeTabId)}
          tabs={[
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
              id: 'export',
              label: 'Export Configuration',
              content: (
                <Box padding={{ top: 'm' }}>
                  <ConfigExportPanel onExportComplete={onDismiss} />
                </Box>
              ),
            },
            {
              id: 'import',
              label: 'Import Configuration',
              content: (
                <Box padding={{ top: 'm' }}>
                  <ConfigImportPanel onImportComplete={onDismiss} />
                </Box>
              ),
            },
          ]}
        />
      </SpaceBetween>
    </Modal>
  );
};
