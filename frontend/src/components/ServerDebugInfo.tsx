import React from 'react';
import type { DRSServer } from '../types';

interface ServerDebugInfoProps {
  server: DRSServer;
}

export const ServerDebugInfo: React.FC<ServerDebugInfoProps> = ({ server }) => {
  console.log('🐛 ServerDebugInfo render for:', server.hostname);
  
  return (
    <div style={{ 
      border: '2px solid blue', 
      padding: '10px', 
      margin: '5px',
      backgroundColor: '#e3f2fd',
      fontSize: '12px',
      fontFamily: 'monospace'
    }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#1976d2' }}>
        🐛 DEBUG: {server.hostname}
      </h4>
      
      <div><strong>Server Object Keys:</strong> {Object.keys(server).join(', ')}</div>
      
      <div style={{ marginTop: '5px' }}>
        <strong>Hardware Field:</strong>
        <div style={{ marginLeft: '10px' }}>
          <div>Exists: {String(!!server.hardware)}</div>
          <div>Type: {typeof server.hardware}</div>
          <div>Value: {JSON.stringify(server.hardware, null, 2)}</div>
        </div>
      </div>
      
      {server.hardware && (
        <div style={{ marginTop: '5px', backgroundColor: '#c8e6c9', padding: '5px' }}>
          <strong>✅ Hardware Data Found:</strong>
          <div>CPU Cores: {server.hardware.totalCores} (type: {typeof server.hardware.totalCores})</div>
          <div>RAM GiB: {server.hardware.ramGiB} (type: {typeof server.hardware.ramGiB})</div>
          <div>Disk GiB: {server.hardware.totalDiskGiB} (type: {typeof server.hardware.totalDiskGiB})</div>
        </div>
      )}
      
      {!server.hardware && (
        <div style={{ marginTop: '5px', backgroundColor: '#ffcdd2', padding: '5px' }}>
          <strong>❌ No Hardware Data</strong>
        </div>
      )}
    </div>
  );
};