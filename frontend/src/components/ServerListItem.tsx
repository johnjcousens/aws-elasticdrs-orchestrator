import React from 'react';
import { Box, Checkbox, StatusIndicator } from '@cloudscape-design/components';

interface DRSServer {
  sourceServerID: string;
  hostname: string;
  nameTag?: string;
  sourceInstanceId?: string;
  sourceIp?: string;
  sourceRegion?: string;
  sourceAccount?: string;
  os?: string;
  state: string;
  replicationState: string;
  lagDuration: string;
  drsTags?: Record<string, string>;
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
  const { 
    sourceServerID, hostname, nameTag, sourceInstanceId, sourceIp, 
    sourceRegion, sourceAccount, state, drsTags, assignedToProtectionGroup, selectable 
  } = server;
  
  // Filter out Name tag from DRS tags display (already shown as nameTag)
  const displayTags = drsTags ? Object.entries(drsTags).filter(([k]) => k !== 'Name') : [];
  
  // Display name: prefer Name tag, fall back to hostname
  const displayName = nameTag || hostname;
  
  return (
    <div
      style={{
        padding: '12px 16px',
        borderBottom: '1px solid #e9ebed',
        opacity: selectable ? 1 : 0.6,
        backgroundColor: selectable ? 'transparent' : '#f2f3f3',
        cursor: selectable ? 'pointer' : 'not-allowed',
      }}
      onClick={(e) => {
        e.preventDefault();
        if (selectable) onToggle();
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
        <div style={{ marginRight: '12px', paddingTop: '2px' }}>
          <Checkbox
            checked={selected}
            disabled={!selectable}
            onChange={(e) => { e.stopPropagation(); onToggle(); }}
          />
        </div>
        <div style={{ flex: 1 }}>
          {/* Primary: Name tag or hostname with status */}
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600, marginRight: '8px' }}>
              {displayName}
            </span>
            <StatusIndicator type={getStateStatus(state)}>
              {state}
            </StatusIndicator>
          </div>
          
          {/* Secondary: Hostname, Instance ID, IP */}
          <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '2px' }}>
            <span style={{ marginRight: '12px' }}>
              <strong>Hostname:</strong> {hostname || 'N/A'}
            </span>
            <span style={{ marginRight: '12px' }}>
              <strong>Instance:</strong> {sourceInstanceId || 'N/A'}
            </span>
            <span>
              <strong>IP:</strong> {sourceIp || 'N/A'}
            </span>
          </div>
          
          {/* Tertiary: Region/Account info */}
          <div style={{ fontSize: '12px', color: '#5f6b7a', marginBottom: '2px' }}>
            <span style={{ marginRight: '12px' }}>
              <strong>Source Region:</strong> {sourceRegion || 'N/A'}
            </span>
            <span>
              <strong>Account:</strong> {sourceAccount || 'N/A'}
            </span>
          </div>
          
          {/* DRS Tags (for tag-based selection) */}
          {displayTags.length > 0 && (
            <div style={{ fontSize: '11px', color: '#0972d3', marginBottom: '4px' }}>
              <strong>Tags:</strong>{' '}
              {displayTags.map(([key, value], idx) => (
                <span key={key} style={{ 
                  backgroundColor: '#f2f8fd', 
                  padding: '1px 6px', 
                  borderRadius: '3px',
                  marginRight: '4px'
                }}>
                  {key}={value}
                </span>
              ))}
            </div>
          )}
          
          {/* DRS Server ID */}
          <div style={{ fontSize: '11px', color: '#879596', marginBottom: '4px' }}>
            DRS ID: {sourceServerID}
          </div>
          
          {/* Assignment status */}
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
