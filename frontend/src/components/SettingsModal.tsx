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

interface SettingsModalProps {
  visible: boolean;
  onDismiss: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  visible,
  onDismiss,
}) => {
  const [activeTab, setActiveTab] = useState('export');

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
