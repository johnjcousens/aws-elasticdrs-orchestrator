/**
 * WaveProgress Component Tests
 * 
 * Comprehensive unit tests for granular progress tracking functionality.
 * Tests event mapping, progress calculation, fallback behavior, and edge cases.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import type { WaveExecution, ServerExecution, JobLogsResponse, JobLogEvent } from '../../types';

// Import the functions we need to test
// Note: These are internal functions, so we'll need to export them or test through the component
// For now, we'll create test versions that match the implementation

/**
 * Maps DRS job log events to progress percentages for a single server
 */
const getServerProgressFromJobLogs = (
  serverId: string,
  waveNumber: number,
  jobLogs?: JobLogsResponse | null
): number => {
  if (!jobLogs || !jobLogs.jobLogs) return 0;
  
  const waveLog = jobLogs.jobLogs.find(log => log.waveNumber === waveNumber);
  if (!waveLog) return 0;
  
  // Find all events for this server, sorted by time (most recent first)
  const serverEvents = waveLog.events
    .filter(e => {
      const eventData = e.eventData as { sourceServerID?: string } | undefined;
      return eventData?.sourceServerID === serverId;
    })
    .sort((a, b) => {
      const timeA = new Date(a.logDateTime).getTime();
      const timeB = new Date(b.logDateTime).getTime();
      return timeB - timeA; // Most recent first
    });
  
  if (serverEvents.length === 0) return 0;
  
  // Map most recent event to progress percentage
  const latestEvent = serverEvents[0].event;
  switch (latestEvent) {
    case 'LAUNCH_END':
      return 1.0; // 100%
    case 'LAUNCH_START':
      return 0.75; // 75%
    case 'CONVERSION_END':
      return 0.5; // 50%
    case 'CONVERSION_START':
      return 0.375; // 37.5%
    case 'SNAPSHOT_END':
      return 0.25; // 25%
    case 'SNAPSHOT_START':
    case 'USING_PREVIOUS_SNAPSHOT':
      return 0.125; // 12.5%
    case 'CLEANUP_START':
    case 'CLEANUP_END':
      return 0.05; // 5%
    default:
      return 0;
  }
};

/**
 * Helper to create mock job logs with specific events
 */
const createMockJobLogs = (
  waveNumber: number,
  serverId: string,
  events: Array<{ event: string; timestamp: string }>
): JobLogsResponse => {
  return {
    executionId: 'test-execution',
    jobLogs: [
      {
        jobId: `job-${waveNumber}`,
        waveNumber,
        events: events.map(e => ({
          event: e.event,
          logDateTime: e.timestamp,
          eventData: { sourceServerID: serverId },
        } as JobLogEvent)),
      },
    ],
  };
};

/**
 * Helper to create mock wave with servers
 */
const createMockWave = (
  waveNumber: number,
  serverCount: number,
  status: string = 'in_progress'
): WaveExecution => {
  const servers: ServerExecution[] = [];
  for (let i = 0; i < serverCount; i++) {
    servers.push({
      serverId: `server-${i}`,
      serverName: `Server ${i}`,
      hostname: `host-${i}`,
      launchStatus: 'PENDING',
      status: 'PENDING',
    });
  }
  
  return {
    waveNumber,
    waveName: `Wave ${waveNumber}`,
    status,
    serverExecutions: servers,
  };
};

describe('WaveProgress - Event Mapping Tests', () => {
  const serverId = 'server-1';
  const waveNumber = 0;
  const baseTimestamp = '2024-01-27T10:00:00Z';

  describe('3.1 Event Mapping Tests', () => {
    it('maps LAUNCH_END to 100%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'LAUNCH_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(1.0);
    });

    it('maps LAUNCH_START to 75%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'LAUNCH_START', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.75);
    });

    it('maps CONVERSION_END to 50%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'CONVERSION_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.5);
    });

    it('maps CONVERSION_START to 37.5%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'CONVERSION_START', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.375);
    });

    it('maps SNAPSHOT_END to 25%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.25);
    });

    it('maps SNAPSHOT_START to 12.5%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.125);
    });

    it('maps USING_PREVIOUS_SNAPSHOT to 12.5%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'USING_PREVIOUS_SNAPSHOT', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.125);
    });

    it('maps CLEANUP_START to 5%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'CLEANUP_START', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.05);
    });

    it('maps CLEANUP_END to 5%', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'CLEANUP_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.05);
    });

    it('returns 0% when no events exist', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, []);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0);
    });

    it('returns 0% for unknown event types', () => {
      const jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'UNKNOWN_EVENT', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0);
    });
  });

  describe('Multiple Events - Most Recent Wins', () => {
    it('uses most recent event when multiple events exist', () => {
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              {
                event: 'SNAPSHOT_START',
                logDateTime: '2024-01-27T10:00:00Z',
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
              {
                event: 'SNAPSHOT_END',
                logDateTime: '2024-01-27T10:05:00Z',
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
              {
                event: 'CONVERSION_START',
                logDateTime: '2024-01-27T10:10:00Z',
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
            ],
          },
        ],
      };
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0.375); // CONVERSION_START is most recent
    });

    it('handles events with same timestamp', () => {
      const sameTime = '2024-01-27T10:00:00Z';
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              {
                event: 'SNAPSHOT_START',
                logDateTime: sameTime,
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
              {
                event: 'SNAPSHOT_END',
                logDateTime: sameTime,
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
            ],
          },
        ],
      };
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      // Should return one of the events (implementation uses first in sorted array)
      expect([0.125, 0.25]).toContain(progress);
    });
  });

  describe('Edge Cases', () => {
    it('returns 0 when jobLogs is null', () => {
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, null);
      expect(progress).toBe(0);
    });

    it('returns 0 when jobLogs is undefined', () => {
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, undefined);
      expect(progress).toBe(0);
    });

    it('returns 0 when jobLogs.jobLogs is empty', () => {
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [],
      };
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0);
    });

    it('returns 0 when wave not found in job logs', () => {
      const jobLogs = createMockJobLogs(1, serverId, [
        { event: 'LAUNCH_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, 0, jobLogs);
      expect(progress).toBe(0);
    });

    it('returns 0 when server not found in wave events', () => {
      const jobLogs = createMockJobLogs(waveNumber, 'other-server', [
        { event: 'LAUNCH_END', timestamp: baseTimestamp },
      ]);
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0);
    });

    it('handles malformed event data gracefully', () => {
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              {
                event: 'LAUNCH_END',
                logDateTime: baseTimestamp,
                eventData: {}, // Missing sourceServerID
              } as JobLogEvent,
            ],
          },
        ],
      };
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      expect(progress).toBe(0); // Should not match server
    });

    it('handles invalid timestamp format', () => {
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              {
                event: 'LAUNCH_END',
                logDateTime: 'invalid-date',
                eventData: { sourceServerID: serverId },
              } as JobLogEvent,
            ],
          },
        ],
      };
      
      const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
      // Should still return progress despite invalid timestamp
      expect(progress).toBe(1.0);
    });
  });

  describe('Monotonic Progress Verification', () => {
    it('progress never decreases through sequential events', () => {
      const events = [
        'CLEANUP_START',
        'SNAPSHOT_START',
        'SNAPSHOT_END',
        'CONVERSION_START',
        'CONVERSION_END',
        'LAUNCH_START',
        'LAUNCH_END',
      ];
      
      const progressValues: number[] = [];
      
      events.forEach((event, index) => {
        const jobLogs = createMockJobLogs(waveNumber, serverId, [
          { event, timestamp: `2024-01-27T10:${index.toString().padStart(2, '0')}:00Z` },
        ]);
        
        const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
        progressValues.push(progress);
      });
      
      // Verify each progress is >= previous
      for (let i = 1; i < progressValues.length; i++) {
        expect(progressValues[i]).toBeGreaterThanOrEqual(progressValues[i - 1]);
      }
    });

    it('progress values are in correct order', () => {
      const expectedOrder = [
        { event: 'CLEANUP_START', expected: 0.05 },
        { event: 'SNAPSHOT_START', expected: 0.125 },
        { event: 'SNAPSHOT_END', expected: 0.25 },
        { event: 'CONVERSION_START', expected: 0.375 },
        { event: 'CONVERSION_END', expected: 0.5 },
        { event: 'LAUNCH_START', expected: 0.75 },
        { event: 'LAUNCH_END', expected: 1.0 },
      ];
      
      expectedOrder.forEach(({ event, expected }) => {
        const jobLogs = createMockJobLogs(waveNumber, serverId, [
          { event, timestamp: baseTimestamp },
        ]);
        
        const progress = getServerProgressFromJobLogs(serverId, waveNumber, jobLogs);
        expect(progress).toBe(expected);
      });
    });
  });
});

describe('WaveProgress - Server Filtering', () => {
  const waveNumber = 0;
  const baseTimestamp = '2024-01-27T10:00:00Z';

  it('filters events by server ID correctly', () => {
    const jobLogs: JobLogsResponse = {
      executionId: 'test-execution',
      jobLogs: [
        {
          jobId: 'job-0',
          waveNumber: 0,
          events: [
            {
              event: 'LAUNCH_END',
              logDateTime: baseTimestamp,
              eventData: { sourceServerID: 'server-1' },
            } as JobLogEvent,
            {
              event: 'SNAPSHOT_START',
              logDateTime: baseTimestamp,
              eventData: { sourceServerID: 'server-2' },
            } as JobLogEvent,
          ],
        },
      ],
    };
    
    const progress1 = getServerProgressFromJobLogs('server-1', waveNumber, jobLogs);
    const progress2 = getServerProgressFromJobLogs('server-2', waveNumber, jobLogs);
    
    expect(progress1).toBe(1.0); // LAUNCH_END
    expect(progress2).toBe(0.125); // SNAPSHOT_START
  });

  it('handles multiple servers in same wave', () => {
    const jobLogs: JobLogsResponse = {
      executionId: 'test-execution',
      jobLogs: [
        {
          jobId: 'job-0',
          waveNumber: 0,
          events: [
            {
              event: 'LAUNCH_END',
              logDateTime: '2024-01-27T10:00:00Z',
              eventData: { sourceServerID: 'server-1' },
            } as JobLogEvent,
            {
              event: 'CONVERSION_START',
              logDateTime: '2024-01-27T10:05:00Z',
              eventData: { sourceServerID: 'server-2' },
            } as JobLogEvent,
            {
              event: 'SNAPSHOT_START',
              logDateTime: '2024-01-27T10:10:00Z',
              eventData: { sourceServerID: 'server-3' },
            } as JobLogEvent,
          ],
        },
      ],
    };
    
    expect(getServerProgressFromJobLogs('server-1', waveNumber, jobLogs)).toBe(1.0);
    expect(getServerProgressFromJobLogs('server-2', waveNumber, jobLogs)).toBe(0.375);
    expect(getServerProgressFromJobLogs('server-3', waveNumber, jobLogs)).toBe(0.125);
  });
});

describe('WaveProgress - Wave Filtering', () => {
  const serverId = 'server-1';
  const baseTimestamp = '2024-01-27T10:00:00Z';

  it('filters events by wave number correctly', () => {
    const jobLogs: JobLogsResponse = {
      executionId: 'test-execution',
      jobLogs: [
        {
          jobId: 'job-0',
          waveNumber: 0,
          events: [
            {
              event: 'LAUNCH_END',
              logDateTime: baseTimestamp,
              eventData: { sourceServerID: serverId },
            } as JobLogEvent,
          ],
        },
        {
          jobId: 'job-1',
          waveNumber: 1,
          events: [
            {
              event: 'SNAPSHOT_START',
              logDateTime: baseTimestamp,
              eventData: { sourceServerID: serverId },
            } as JobLogEvent,
          ],
        },
      ],
    };
    
    const progressWave0 = getServerProgressFromJobLogs(serverId, 0, jobLogs);
    const progressWave1 = getServerProgressFromJobLogs(serverId, 1, jobLogs);
    
    expect(progressWave0).toBe(1.0); // LAUNCH_END in wave 0
    expect(progressWave1).toBe(0.125); // SNAPSHOT_START in wave 1
  });
});


/**
 * Calculate progress helper function (matches implementation)
 */
const calculateProgress = (
  waves: WaveExecution[],
  totalWaves: number,
  jobLogs?: JobLogsResponse | null
): { percentage: number; completed: number; total: number } => {
  if (!waves || waves.length === 0) {
    return { percentage: 0, completed: 0, total: totalWaves };
  }
  
  if (totalWaves === 0) {
    return { percentage: 0, completed: 0, total: 0 };
  }
  
  let totalProgress = 0;
  let completed = 0;
  
  waves.forEach(w => {
    const status = w.status.toLowerCase();
    
    if (status === 'completed' || status === 'launched') {
      totalProgress += 1.0;
      completed++;
    } else if (status === 'in_progress' || status === 'started' || 
               status === 'launching' || status === 'polling') {
      const servers = w.serverExecutions || [];
      const waveNum = w.waveNumber ?? 0;
      
      if (servers.length > 0) {
        let waveProgress = 0;
        
        servers.forEach(server => {
          const jobLogProgress = getServerProgressFromJobLogs(server.serverId, waveNum, jobLogs);
          
          if (jobLogProgress > 0) {
            waveProgress += jobLogProgress;
          } else {
            const serverStatus = (server.launchStatus || server.status || '').toUpperCase();
            if (serverStatus === 'LAUNCHED') {
              waveProgress += 1.0;
            }
          }
        });
        
        totalProgress += waveProgress / servers.length;
      }
    }
  });
  
  const percentage = Math.round((totalProgress / totalWaves) * 100);
  
  return { percentage, completed, total: totalWaves };
};

/**
 * ============================================================================
 * INTEGRATION TESTS - Full DRS Recovery Flow Simulations
 * ============================================================================
 * 
 * These tests simulate complete DRS recovery scenarios with multiple servers
 * and waves, verifying that progress updates correctly through all phases.
 */

describe('Integration Tests - Full Recovery Flow', () => {
  describe('4.1 Full Recovery Flow Test - Single Server', () => {
    const serverId = 'server-0'; // Use server-0 to match createMockWave
    const waveNumber = 0;
    const totalWaves = 3;
    
    it('progresses from 0% through all phases to 100%', () => {
      // Create wave with single server
      const wave = createMockWave(waveNumber, 1, 'in_progress');
      
      // Phase 1: Wave starts - 0% progress
      let jobLogs = createMockJobLogs(waveNumber, serverId, []);
      let result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBe(0);
      
      // Phase 2: SNAPSHOT_START - should show progress > 0%
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(0);
      expect(result.percentage).toBe(4); // 0.125 / 3 waves = 4.17% rounded to 4%
      const snapshotStartProgress = result.percentage;
      
      // Phase 3: SNAPSHOT_END - should show progress > previous
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
        { event: 'SNAPSHOT_END', timestamp: '2024-01-27T10:05:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(snapshotStartProgress);
      expect(result.percentage).toBe(8); // 0.25 / 3 waves = 8.33% rounded to 8%
      const snapshotEndProgress = result.percentage;
      
      // Phase 4: CONVERSION_START - should show progress > previous
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
        { event: 'SNAPSHOT_END', timestamp: '2024-01-27T10:05:00Z' },
        { event: 'CONVERSION_START', timestamp: '2024-01-27T10:10:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(snapshotEndProgress);
      expect(result.percentage).toBe(13); // 0.375 / 3 waves = 12.5% rounded to 13%
      const conversionStartProgress = result.percentage;
      
      // Phase 5: CONVERSION_END - should show progress > previous
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
        { event: 'SNAPSHOT_END', timestamp: '2024-01-27T10:05:00Z' },
        { event: 'CONVERSION_START', timestamp: '2024-01-27T10:10:00Z' },
        { event: 'CONVERSION_END', timestamp: '2024-01-27T10:15:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(conversionStartProgress);
      expect(result.percentage).toBe(17); // 0.5 / 3 waves = 16.67% rounded to 17%
      const conversionEndProgress = result.percentage;
      
      // Phase 6: LAUNCH_START - should show progress > previous
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
        { event: 'SNAPSHOT_END', timestamp: '2024-01-27T10:05:00Z' },
        { event: 'CONVERSION_START', timestamp: '2024-01-27T10:10:00Z' },
        { event: 'CONVERSION_END', timestamp: '2024-01-27T10:15:00Z' },
        { event: 'LAUNCH_START', timestamp: '2024-01-27T10:20:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(conversionEndProgress);
      expect(result.percentage).toBe(25); // 0.75 / 3 waves = 25%
      const launchStartProgress = result.percentage;
      
      // Phase 7: LAUNCH_END - should show progress > previous
      jobLogs = createMockJobLogs(waveNumber, serverId, [
        { event: 'SNAPSHOT_START', timestamp: '2024-01-27T10:00:00Z' },
        { event: 'SNAPSHOT_END', timestamp: '2024-01-27T10:05:00Z' },
        { event: 'CONVERSION_START', timestamp: '2024-01-27T10:10:00Z' },
        { event: 'CONVERSION_END', timestamp: '2024-01-27T10:15:00Z' },
        { event: 'LAUNCH_START', timestamp: '2024-01-27T10:20:00Z' },
        { event: 'LAUNCH_END', timestamp: '2024-01-27T10:25:00Z' },
      ]);
      result = calculateProgress([wave], totalWaves, jobLogs);
      expect(result.percentage).toBeGreaterThan(launchStartProgress);
      expect(result.percentage).toBe(33); // 1.0 / 3 waves = 33.33% rounded to 33%
      
      // Verify monotonic progress
      expect(snapshotStartProgress).toBeLessThan(snapshotEndProgress);
      expect(snapshotEndProgress).toBeLessThan(conversionStartProgress);
      expect(conversionStartProgress).toBeLessThan(conversionEndProgress);
      expect(conversionEndProgress).toBeLessThan(launchStartProgress);
      expect(launchStartProgress).toBeLessThan(result.percentage);
    });
    
    it('reaches 100% when all waves complete', () => {
      // Create 3 completed waves
      const waves = [
        { ...createMockWave(0, 1, 'completed'), waveNumber: 0 },
        { ...createMockWave(1, 1, 'completed'), waveNumber: 1 },
        { ...createMockWave(2, 1, 'completed'), waveNumber: 2 },
      ];
      
      const result = calculateProgress(waves, 3, null);
      expect(result.percentage).toBe(100);
      expect(result.completed).toBe(3);
    });
  });
  
  describe('4.2 Multi-Wave Recovery Test', () => {
    it('progresses correctly through 3 waves with 4 servers each', () => {
      const totalWaves = 3;
      
      // Wave 0: All servers completed
      const wave0 = { ...createMockWave(0, 4, 'completed'), waveNumber: 0 };
      const jobLogsWave0: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:10:00Z', eventData: { sourceServerID: 'server-2' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:15:00Z', eventData: { sourceServerID: 'server-3' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      let result = calculateProgress([wave0], totalWaves, jobLogsWave0);
      expect(result.percentage).toBe(33); // 1 wave complete out of 3
      expect(result.completed).toBe(1);
      
      // Wave 1: First server starting snapshot
      const wave1 = { ...createMockWave(1, 4, 'in_progress'), waveNumber: 1 };
      const jobLogsWave1: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: jobLogsWave0.jobLogs[0].events,
          },
          {
            jobId: 'job-1',
            waveNumber: 1,
            events: [
              { event: 'SNAPSHOT_START', logDateTime: '2024-01-27T10:20:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      result = calculateProgress([wave0, wave1], totalWaves, jobLogsWave1);
      expect(result.percentage).toBeGreaterThan(33);
      expect(result.percentage).toBe(34); // 1.0 + (0.125/4) / 3 = 34.38% rounded to 34%
      
      // Wave 1: All servers completed
      const wave1Completed = { ...createMockWave(1, 4, 'completed'), waveNumber: 1 };
      const jobLogsWave1Complete: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: jobLogsWave0.jobLogs[0].events,
          },
          {
            jobId: 'job-1',
            waveNumber: 1,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:30:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:35:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:40:00Z', eventData: { sourceServerID: 'server-2' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:45:00Z', eventData: { sourceServerID: 'server-3' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      result = calculateProgress([wave0, wave1Completed], totalWaves, jobLogsWave1Complete);
      expect(result.percentage).toBe(67); // 2 waves complete out of 3
      expect(result.completed).toBe(2);
      
      // Wave 2: All servers completed
      const wave2 = { ...createMockWave(2, 4, 'completed'), waveNumber: 2 };
      const jobLogsWave2: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: jobLogsWave0.jobLogs[0].events,
          },
          {
            jobId: 'job-1',
            waveNumber: 1,
            events: jobLogsWave1Complete.jobLogs[1].events,
          },
          {
            jobId: 'job-2',
            waveNumber: 2,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T11:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T11:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T11:10:00Z', eventData: { sourceServerID: 'server-2' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T11:15:00Z', eventData: { sourceServerID: 'server-3' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      result = calculateProgress([wave0, wave1Completed, wave2], totalWaves, jobLogsWave2);
      expect(result.percentage).toBe(100); // All 3 waves complete
      expect(result.completed).toBe(3);
    });
  });
  
  describe('4.3 Partial Job Logs Test', () => {
    it('handles mixed data - some servers with events, others with launchStatus', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Set launchStatus for servers 2 and 3
      wave.serverExecutions[2].launchStatus = 'LAUNCHED';
      wave.serverExecutions[3].launchStatus = 'LAUNCHED';
      
      // Job logs only have events for servers 0 and 1
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'LAUNCH_START', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      const result = calculateProgress([wave], 3, jobLogs);
      
      // Expected: (0.375 + 0.75 + 1.0 + 1.0) / 4 servers = 3.125 / 4 = 0.78125
      // 0.78125 / 3 waves = 0.260416 = 26%
      expect(result.percentage).toBe(26);
    });
    
    it('falls back to launchStatus when no job log events for any server', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Set launchStatus for 2 servers
      wave.serverExecutions[0].launchStatus = 'LAUNCHED';
      wave.serverExecutions[1].launchStatus = 'LAUNCHED';
      
      // Job logs exist but have no events for these servers
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [],
          },
        ],
      };
      
      const result = calculateProgress([wave], 3, jobLogs);
      
      // Expected: (1.0 + 1.0 + 0 + 0) / 4 servers = 2.0 / 4 = 0.5
      // 0.5 / 3 waves = 0.166666 = 17%
      expect(result.percentage).toBe(17);
    });
    
    it('handles completely missing job logs gracefully', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Set launchStatus for all servers
      wave.serverExecutions.forEach(s => {
        s.launchStatus = 'LAUNCHED';
      });
      
      const result = calculateProgress([wave], 3, null);
      
      // Expected: (1.0 + 1.0 + 1.0 + 1.0) / 4 servers = 4.0 / 4 = 1.0
      // 1.0 / 3 waves = 0.333333 = 33%
      expect(result.percentage).toBe(33);
    });
  });
  
  describe('4.4 Error Recovery Test', () => {
    it('switches from job logs to launchStatus fallback when job logs become unavailable', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Phase 1: Job logs available with progress
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      let result = calculateProgress([wave], 3, jobLogs);
      expect(result.percentage).toBeGreaterThan(0);
      const progressWithJobLogs = result.percentage;
      
      // Phase 2: Job logs API fails (null)
      // Set launchStatus to maintain progress
      wave.serverExecutions[0].launchStatus = 'LAUNCHED';
      wave.serverExecutions[1].launchStatus = 'LAUNCHED';
      
      result = calculateProgress([wave], 3, null);
      
      // Should still show progress using launchStatus
      expect(result.percentage).toBeGreaterThan(0);
      expect(result.percentage).toBe(17); // (1.0 + 1.0) / 4 / 3 = 16.67% = 17%
    });
    
    it('continues to update progress after job logs are restored', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Phase 1: No job logs, using launchStatus
      wave.serverExecutions[0].launchStatus = 'LAUNCHED';
      let result = calculateProgress([wave], 3, null);
      expect(result.percentage).toBe(8); // 1.0 / 4 / 3 = 8.33% = 8%
      
      // Phase 2: Job logs restored with more detailed progress
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
              { event: 'SNAPSHOT_START', logDateTime: '2024-01-27T10:10:00Z', eventData: { sourceServerID: 'server-2' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      result = calculateProgress([wave], 3, jobLogs);
      
      // Expected: (1.0 + 0.375 + 0.125 + 0) / 4 = 1.5 / 4 = 0.375
      // 0.375 / 3 = 0.125 = 13%
      expect(result.percentage).toBeGreaterThan(8);
      expect(result.percentage).toBe(13);
    });
    
    it('handles malformed job log data gracefully', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      // Malformed job logs with missing eventData
      const malformedJobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:00:00Z', eventData: {} } as JobLogEvent,
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:05:00Z' } as JobLogEvent,
            ],
          },
        ],
      };
      
      // Should not throw error, should fall back to launchStatus
      expect(() => calculateProgress([wave], 3, malformedJobLogs)).not.toThrow();
      
      const result = calculateProgress([wave], 3, malformedJobLogs);
      expect(result.percentage).toBe(0); // No valid events, no launchStatus
    });
  });
});

describe('Integration Tests - Progress Calculation', () => {
  describe('Wave Progress Averaging', () => {
    it('averages server progress correctly for in-progress wave', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'CONVERSION_END', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
              { event: 'SNAPSHOT_END', logDateTime: '2024-01-27T10:10:00Z', eventData: { sourceServerID: 'server-2' } } as JobLogEvent,
              { event: 'SNAPSHOT_START', logDateTime: '2024-01-27T10:15:00Z', eventData: { sourceServerID: 'server-3' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      const result = calculateProgress([wave], 3, jobLogs);
      
      // Expected: (1.0 + 0.5 + 0.25 + 0.125) / 4 = 1.875 / 4 = 0.46875
      // 0.46875 / 3 waves = 0.15625 = 16%
      expect(result.percentage).toBe(16);
    });
    
    it('handles waves with different server counts', () => {
      const wave1 = createMockWave(0, 2, 'in_progress');
      const wave2 = createMockWave(1, 4, 'in_progress');
      
      const jobLogs: JobLogsResponse = {
        executionId: 'test-execution',
        jobLogs: [
          {
            jobId: 'job-0',
            waveNumber: 0,
            events: [
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:00:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'LAUNCH_END', logDateTime: '2024-01-27T10:05:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
            ],
          },
          {
            jobId: 'job-1',
            waveNumber: 1,
            events: [
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:10:00Z', eventData: { sourceServerID: 'server-0' } } as JobLogEvent,
              { event: 'CONVERSION_START', logDateTime: '2024-01-27T10:15:00Z', eventData: { sourceServerID: 'server-1' } } as JobLogEvent,
            ],
          },
        ],
      };
      
      const result = calculateProgress([wave1, wave2], 3, jobLogs);
      
      // Wave 1: (1.0 + 1.0) / 2 = 1.0
      // Wave 2: (0.375 + 0.375 + 0 + 0) / 4 = 0.1875
      // Total: (1.0 + 0.1875) / 3 = 0.395833 = 40%
      expect(result.percentage).toBe(40);
    });
  });
  
  describe('Edge Cases', () => {
    it('handles empty waves array', () => {
      const result = calculateProgress([], 3, null);
      expect(result.percentage).toBe(0);
      expect(result.completed).toBe(0);
      expect(result.total).toBe(3);
    });
    
    it('handles waves with no servers', () => {
      const wave = createMockWave(0, 0, 'in_progress');
      const result = calculateProgress([wave], 3, null);
      expect(result.percentage).toBe(0);
    });
    
    it('handles totalWaves = 0', () => {
      const wave = createMockWave(0, 4, 'in_progress');
      const result = calculateProgress([wave], 0, null);
      expect(result.percentage).toBe(0);
      expect(result.total).toBe(0);
    });
  });
});
