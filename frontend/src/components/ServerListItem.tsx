import React, { useState } from 'react';
import { Checkbox, StatusIndicator } from '@cloudscape-design/components';
import type { DRSServer } from '../types';

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
  const [expanded, setExpanded] = useState(false);
  
  // Extract fields directly without destructuring to avoid any potential issues
  const sourceServerID = server.sourceServerID;
  const hostname = server.hostname;
  const fqdn = server.fqdn;
  const nameTag = server.nameTag;
  const sourceInstanceId = server.sourceInstanceId;
  const sourceIp = server.sourceIp;
  const sourceMac = server.sourceMac;
  const sourceRegion = server.sourceRegion;
  const sourceAccount = server.sourceAccount;
  const os = server.os;
  const state = server.state;
  const hardware = server.hardware;
  const networkInterfaces = server.networkInterfaces;
  const drsTags = server.drsTags;
  const assignedToProtectionGroup = server.assignedToProtectionGroup;
  const selectable = server.selectable;
  
  // Get the actual name tag value - prefer nameTag field, fallback to drsTags.Name
  const actualNameTag = nameTag || (drsTags?.Name);
  
  // Filter out Name tag from DRS tags display (already shown as nameTag)
  const displayTags = drsTags ? Object.entries(drsTags).filter(([k]) => k !== 'Name') : [];
  
  // Display name: prefer Name tag, fall back to hostname
  const displayName = actualNameTag || hostname;
  
  return (
    <div
      style={{
        padding: '16px',
        borderBottom: '1px solid #e9ebed',
        opacity: selectable ? 1 : 0.6,
        backgroundColor: selectable ? 'transparent' : '#f9f9f9',
        transition: 'background-color 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ paddingTop: '2px' }}>
          <Checkbox
            checked={selected}
            disabled={!selectable}
            onChange={(e) => { e.stopPropagation(); onToggle(); }}
          />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          {/* Primary: Name and status */}
          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center', 
              marginBottom: '8px', 
              cursor: 'pointer',
              gap: '8px'
            }}
            onClick={() => setExpanded(!expanded)}
          >
            <span style={{ 
              fontWeight: 600, 
              fontSize: '14px',
              color: '#16191f',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {displayName}
            </span>
            <StatusIndicator type={getStateStatus(state)}>
              {state}
            </StatusIndicator>
            <span style={{ 
              fontSize: '11px', 
              color: '#0972d3',
              marginLeft: 'auto',
              flexShrink: 0
            }}>
              {expanded ? '▼' : '▶'} Details
            </span>
          </div>
          
          {/* Compact key information */}
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '2fr 1fr 1fr 1fr', 
            gap: '4px 16px',
            fontSize: '12px', 
            color: '#5f6b7a', 
            marginBottom: '4px'
          }}>
            {/* FQDN - first position, wider column, no label */}
            <div style={{ gridColumn: '1' }}>
              {fqdn ? (
                <span style={{ fontWeight: 500, color: '#0972d3' }}>{fqdn}</span>
              ) : (
                <span style={{ color: '#879596' }}>No FQDN</span>
              )}
            </div>
            
            {/* Hardware info - positions 2, 3, 4 */}
            {hardware ? (
              <>
                <div style={{ gridColumn: '2' }}>
                  <span style={{ fontWeight: 500 }}>CPU:</span> {hardware.totalCores} cores
                </div>
                <div style={{ gridColumn: '3' }}>
                  <span style={{ fontWeight: 500 }}>RAM:</span> {hardware.ramGiB} GiB
                </div>
                <div style={{ gridColumn: '4' }}>
                  <span style={{ fontWeight: 500 }}>IP:</span> {sourceIp || 'N/A'}
                </div>
              </>
            ) : (
              <>
                <div style={{ gridColumn: '2', color: '#879596' }}>CPU: Unknown</div>
                <div style={{ gridColumn: '3', color: '#879596' }}>RAM: Unknown</div>
                <div style={{ gridColumn: '4', color: '#879596' }}>IP: {sourceIp || 'N/A'}</div>
              </>
            )}
          </div>
          
          {/* Expanded details */}
          {expanded && (
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              backgroundColor: '#fafafa', 
              borderRadius: '4px',
              fontSize: '12px'
            }}>
              {/* Identification */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#16191f' }}>Identification</div>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '4px 12px' }}>
                  <span style={{ color: '#5f6b7a' }}>Hostname:</span>
                  <span>{hostname || 'N/A'}</span>
                  <span style={{ color: '#5f6b7a' }}>FQDN:</span>
                  <span>{fqdn || 'N/A'}</span>
                  <span style={{ color: '#5f6b7a' }}>AWS Instance ID:</span>
                  <span>{sourceInstanceId || 'N/A'}</span>
                  <span style={{ color: '#5f6b7a' }}>DRS Server ID:</span>
                  <span style={{ fontFamily: 'monospace', fontSize: '11px' }}>{sourceServerID}</span>
                </div>
              </div>
              
              {/* Hardware Details */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#16191f' }}>Hardware Details</div>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '4px 12px' }}>
                  <span style={{ color: '#5f6b7a' }}>CPU Model:</span>
                  <span>{hardware?.cpus?.[0]?.modelName ?? 'Unknown'}</span>
                  <span style={{ color: '#5f6b7a' }}>CPU Cores:</span>
                  <span>{hardware?.totalCores ?? 'Unknown'} cores</span>
                  <span style={{ color: '#5f6b7a' }}>RAM:</span>
                  <span>{hardware?.ramGiB ?? 'Unknown'} GiB ({hardware?.ramBytes ? `${(hardware.ramBytes / (1024**3)).toFixed(1)} GB` : 'Unknown'})</span>
                  <span style={{ color: '#5f6b7a' }}>Storage:</span>
                  <div>
                    {hardware?.disks?.length ? (
                      <>
                        <div style={{ marginBottom: '4px' }}>
                          <strong>Total:</strong> {hardware.totalDiskGiB} GiB
                        </div>
                        {hardware.disks.map((disk, i) => (
                          <div key={i} style={{ fontSize: '11px', color: '#879596', marginBottom: '2px' }}>
                            • {disk.deviceName}: {disk.sizeGiB} GiB ({(disk.bytes / (1024**3)).toFixed(1)} GB)
                          </div>
                        ))}
                      </>
                    ) : (
                      'Unknown'
                    )}
                  </div>
                </div>
              </div>
              
              {/* Network */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#16191f' }}>Network</div>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '4px 12px' }}>
                  <span style={{ color: '#5f6b7a' }}>Primary IP:</span>
                  <span>{sourceIp || 'N/A'}</span>
                  <span style={{ color: '#5f6b7a' }}>MAC Address:</span>
                  <span>{sourceMac || 'N/A'}</span>
                  {networkInterfaces && networkInterfaces.length > 1 && (
                    <>
                      <span style={{ color: '#5f6b7a' }}>All Interfaces:</span>
                      <div>
                        {networkInterfaces.map((nic, i) => (
                          <div key={i} style={{ fontSize: '11px', color: '#879596', marginBottom: '2px' }}>
                            • {nic.ips.join(', ')} ({nic.macAddress})
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>
              
              {/* Source */}
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: '#16191f' }}>Source</div>
                <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '4px 12px' }}>
                  <span style={{ color: '#5f6b7a' }}>Region:</span>
                  <span>{sourceRegion || 'N/A'}</span>
                  <span style={{ color: '#5f6b7a' }}>Account:</span>
                  <span>{sourceAccount || 'N/A'}</span>
                  {os && (
                    <>
                      <span style={{ color: '#5f6b7a' }}>Operating System:</span>
                      <span>{os}</span>
                    </>
                  )}
                </div>
              </div>
              
              {/* All Tags */}
              {(() => {
                // Combine all available tags - start with drsTags and ensure Name tag is included
                const allTags = { ...(drsTags || {}) };
                
                // If nameTag exists but Name is not in drsTags, add it
                if (nameTag && !allTags.Name) {
                  allTags.Name = nameTag;
                }
                
                // Only show tags section if we have any tags
                return Object.keys(allTags).length > 0 ? (
                  <div>
                    <div style={{ fontWeight: 600, marginBottom: '6px', color: '#16191f' }}>Tags</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {Object.entries(allTags).map(([key, value]) => (
                        <span key={key} style={{ 
                          backgroundColor: key === 'Name' ? '#e8f4fd' : '#f2f8fd', 
                          padding: '4px 8px', 
                          borderRadius: '4px',
                          fontSize: '11px',
                          border: key === 'Name' ? '1px solid #0972d3' : '1px solid #d5dbdb',
                          color: key === 'Name' ? '#0972d3' : '#5f6b7a',
                          fontWeight: key === 'Name' ? 500 : 400
                        }}>
                          <strong>{key}:</strong> {value}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null;
              })()}
            </div>
          )}
          
          {/* Assignment status */}
          {assignedToProtectionGroup && (
            <div style={{ 
              fontSize: '11px', 
              color: '#d13212', 
              marginTop: '6px',
              padding: '4px 8px',
              backgroundColor: '#fdf2f2',
              borderRadius: '4px',
              border: '1px solid #f5c6cb'
            }}>
              ⚠️ Already assigned to: <strong>{assignedToProtectionGroup.protectionGroupName}</strong>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
