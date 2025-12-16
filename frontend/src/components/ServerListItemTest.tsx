import React from 'react';
import type { DRSServer } from '../types';

// Minimal test component to isolate the hardware display issue
export const ServerListItemTest: React.FC<{ server: DRSServer }> = ({ server }) => {
  console.log('ServerListItemTest render:', {
    hostname: server.hostname,
    hasHardware: !!server.hardware,
    hardware: server.hardware,
    hardwareKeys: server.hardware ? Object.keys(server.hardware) : 'none'
  });

  const hardware = server.hardware;
  
  return (
    <div style={{ border: '1px solid red', padding: '10px', margin: '5px' }}>
      <h3>TEST: {server.hostname}</h3>
      <div>Hardware exists: {String(!!hardware)}</div>
      <div>Hardware object: {JSON.stringify(hardware)}</div>
      
      {hardware ? (
        <div style={{ backgroundColor: 'lightgreen', padding: '5px' }}>
          <div>✅ Hardware condition is TRUE</div>
          <div>CPU: {hardware.totalCores || 'Unknown'} cores</div>
          <div>RAM: {hardware.ramGiB || 'Unknown'} GiB</div>
          <div>Disk: {hardware.totalDiskGiB || 'Unknown'} GiB</div>
        </div>
      ) : (
        <div style={{ backgroundColor: 'lightcoral', padding: '5px' }}>
          ❌ NO HARDWARE DATA FOUND
        </div>
      )}
    </div>
  );
};