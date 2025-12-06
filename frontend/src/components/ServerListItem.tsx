import React from 'react';
import { Box, Checkbox, StatusIndicator } from '@cloudscape-design/components';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  assignedToProtectionGroup?: {
    protectionGroupId: string;
    protectionGroupName: string;
  };
  selectable: boolean;
}

interface ServerListItemProps {
  server: DRSServer;
  selected: boolean;
  onToggle: () => void;
}

const getStateStatus = (state: string): 'success' | 'info' | 'error' | 'warning' | 'stopped' | 'pending' | 'in-progress' | 'loading' => {
  switch (state) {
    case 'READY_FOR_RECOVERY':
      return 'success';
    case 'SYNCING':
    case 'INITIATED':
      return 'in-progress';
    case 'DISCONNECTED':
    case 'STOPPED':
      return 'error';
    default:
      return 'pending';
  }
};

export const ServerListItem: React.FC<ServerListItemProps> = ({
  server,
  selected,
  onToggle
}) => {
  const { sourceServerID, hostname, state, assignedToProtectionGroup, selectable } = server;
  
  return (
    <div
      style={{
        padding: '12px 16px',
        borderBottom: '1px solid #e9ebed',
        opacity: selectable ? 1 : 0.6,
        backgroundColor: selectable ? 'transparent' : '#f2f3f3',
        cursor: selectable ? 'pointer' : 'not-allowed',
      }}
      onClick={selectable ? onToggle : undefined}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
        <div style={{ marginRight: '12px', paddingTop: '2px' }}>
          <Checkbox
            checked={selected}
            disabled={!selectable}
            onChange={onToggle}
          />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontWeight: 600, marginRight: '8px' }}>
              {hostname}
            </span>
            <StatusIndicator type={getStateStatus(state)}>
              {state}
            </StatusIndicator>
          </div>
          <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '4px' }}>
            {sourceServerID}
          </div>
          {assignedToProtectionGroup && (
            <div style={{ fontSize: '12px', color: '#d13212', marginTop: '4px' }}>
              Already assigned to: {assignedToProtectionGroup.protectionGroupName}
            </div>
          )}
          {selectable && (
            <div style={{ fontSize: '12px', color: '#037f0c', marginTop: '4px' }}>
              Available
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
