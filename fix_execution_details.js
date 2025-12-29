#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const filePath = 'frontend/src/pages/ExecutionDetailsPage.tsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Change 1: Add 'cancelling' status to polling list (around line 96-97)
const oldPollingCheck = `    const isActive = 
      execution.status === 'in_progress' || 
      execution.status === 'pending' ||
      execution.status === 'paused' ||
      execution.status === 'running' ||
      execution.status === 'started' ||
      execution.status === 'polling' ||
      execution.status === 'launching' ||
      execution.status === 'initiated' ||
      (execution.status as string) === 'RUNNING' ||
      (execution.status as string) === 'STARTED' ||
      (execution.status as string) === 'POLLING' ||
      (execution.status as string) === 'LAUNCHING' ||
      (execution.status as string) === 'INITIATED';`;

const newPollingCheck = `    const isActive = 
      execution.status === 'in_progress' || 
      execution.status === 'pending' ||
      execution.status === 'paused' ||
      execution.status === 'running' ||
      execution.status === 'started' ||
      execution.status === 'polling' ||
      execution.status === 'launching' ||
      execution.status === 'initiated' ||
      execution.status === 'cancelling' ||
      (execution.status as string) === 'RUNNING' ||
      (execution.status as string) === 'STARTED' ||
      (execution.status as string) === 'POLLING' ||
      (execution.status as string) === 'LAUNCHING' ||
      (execution.status as string) === 'INITIATED' ||
      (execution.status as string) === 'CANCELLING';`;

content = content.replace(oldPollingCheck, newPollingCheck);

// Change 2: Prevent cancel if already cancelling (around line 382)
const oldCanCancel = `  // Check if execution can be cancelled
  const canCancel = execution && (
    execution.status === 'in_progress' || 
    execution.status === 'pending' ||
    execution.status === 'paused' ||
    execution.status === 'running' ||
    execution.status === 'started' ||
    execution.status === 'polling' ||
    execution.status === 'launching' ||
    execution.status === 'initiated' ||
    (execution.status as string) === 'RUNNING' ||
    (execution.status as string) === 'STARTED' ||
    (execution.status as string) === 'PAUSED' ||
    (execution.status as string) === 'PENDING' ||
    (execution.status as string) === 'IN_PROGRESS' ||
    (execution.status as string) === 'POLLING' ||
    (execution.status as string) === 'LAUNCHING' ||
    (execution.status as string) === 'INITIATED'
  );`;

const newCanCancel = `  // Check if execution can be cancelled
  const canCancel = execution && (
    execution.status === 'in_progress' || 
    execution.status === 'pending' ||
    execution.status === 'paused' ||
    execution.status === 'running' ||
    execution.status === 'started' ||
    execution.status === 'polling' ||
    execution.status === 'launching' ||
    execution.status === 'initiated' ||
    (execution.status as string) === 'RUNNING' ||
    (execution.status as string) === 'STARTED' ||
    (execution.status as string) === 'PAUSED' ||
    (execution.status as string) === 'PENDING' ||
    (execution.status as string) === 'IN_PROGRESS' ||
    (execution.status as string) === 'POLLING' ||
    (execution.status as string) === 'LAUNCHING' ||
    (execution.status as string) === 'INITIATED'
  ) && !(
    execution.status === 'cancelling' ||
    (execution.status as string) === 'CANCELLING'
  );`;

content = content.replace(oldCanCancel, newCanCancel);

// Change 3: Pass execution status/endTime to WaveProgress (around line 750)
const oldWaveProgress = `            <WaveProgress 
              waves={mapWavesToWaveExecutions(execution)} 
              totalWaves={execution.totalWaves} 
              executionId={execution.executionId}
            />`;

const newWaveProgress = `            <WaveProgress 
              waves={mapWavesToWaveExecutions(execution)} 
              totalWaves={execution.totalWaves} 
              executionId={execution.executionId}
              executionStatus={execution.status}
              executionEndTime={execution.endTime}
            />`;

content = content.replace(oldWaveProgress, newWaveProgress);

// Write the file back
fs.writeFileSync(filePath, content, 'utf8');

console.log('Successfully applied all 3 changes to ExecutionDetailsPage.tsx');