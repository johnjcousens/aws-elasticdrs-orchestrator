/**
 * Regional Capacity Section
 * 
 * Displays combined per-region replication capacity across all accounts.
 * Replication capacity is unique as it's the only DRS quota that is per-account-per-region (300 max).
 * 
 * Now uses pre-calculated regional data from backend for better performance.
 */

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Box,
  ColumnLayout,
  StatusIndicator,
} from '@cloudscape-design/components';
import { CapacityGauge } from './CapacityGauge';
import type { RegionalCapacityBreakdown } from '../types/staging-accounts';

interface RegionalCapacitySectionProps {
  regionalCapacity: RegionalCapacityBreakdown[];
  combinedTotal: number;
  combinedMax: number;
  combinedPercent: number;
  combinedStatus: string;
}

export const RegionalCapacitySection: React.FC<RegionalCapacitySectionProps> = ({
  regionalCapacity,
  combinedTotal,
  combinedMax,
  combinedPercent,
  combinedStatus,
}) => {
  const getProgressStatus = (used: number, max: number): 'success' | 'warning' | 'error' => {
    const percent = (used / max) * 100;
    if (percent < 75) return 'success';
    if (percent < 90) return 'warning';
    return 'error';
  };

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Replication capacity (300 max per account per region) and recovery capacity (4,000 max per account per region)"
        >
          Regional Replication Capacity
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Combined Total */}
        <div>
          <Box variant="h3" padding={{ bottom: 'xs' }}>
            Combined Total
          </Box>
          <ColumnLayout columns={2} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Replicating Servers</Box>
              <Box variant="awsui-value-large">
                {combinedTotal} / {combinedMax.toLocaleString()}
              </Box>
              <Box variant="small" color="text-body-secondary">
                {combinedPercent.toFixed(1)}% used
              </Box>
            </div>
            <div>
              <CapacityGauge
                used={combinedTotal}
                total={combinedMax}
                size="medium"
                status={getProgressStatus(combinedTotal, combinedMax)}
              />
            </div>
          </ColumnLayout>
        </div>

        {/* Regional Breakdown */}
        {regionalCapacity.length > 0 && (
          <div>
            <Box variant="h3" padding={{ bottom: 'xs' }}>
              By Region
            </Box>
            <SpaceBetween size="m">
              {regionalCapacity.map((region) => (
                <Container key={region.region}>
                  <SpaceBetween size="s">
                    <Box variant="h4">{region.region}</Box>
                    
                    {/* Replication Capacity */}
                    <div>
                      <Box variant="small" color="text-body-secondary" padding={{ bottom: 'xxs' }}>
                        Replication: {region.replicatingServers} / {region.maxReplicating.toLocaleString()} servers ({region.accountCount} {region.accountCount === 1 ? 'account' : 'accounts'})
                      </Box>
                      <CapacityGauge
                        used={region.replicatingServers}
                        total={region.maxReplicating}
                        size="small"
                        status={getProgressStatus(region.replicatingServers, region.maxReplicating)}
                      />
                      <Box variant="small" color="text-body-secondary" padding={{ top: 'xxs' }}>
                        {region.replicationPercent.toFixed(1)}% • {region.replicationAvailable.toLocaleString()} available
                      </Box>
                    </div>

                    {/* Recovery Capacity */}
                    <div>
                      <Box variant="small" color="text-body-secondary" padding={{ bottom: 'xxs' }}>
                        Recovery: {region.recoveryServers} / {region.recoveryMax.toLocaleString()} servers
                      </Box>
                      <CapacityGauge
                        used={region.recoveryServers}
                        total={region.recoveryMax}
                        size="small"
                        status={getProgressStatus(region.recoveryServers, region.recoveryMax)}
                      />
                      <Box variant="small" color="text-body-secondary" padding={{ top: 'xxs' }}>
                        {region.recoveryPercent.toFixed(1)}% • {region.recoveryAvailable.toLocaleString()} available
                      </Box>
                    </div>
                  </SpaceBetween>
                </Container>
              ))}
            </SpaceBetween>
          </div>
        )}
      </SpaceBetween>
    </Container>
  );
};
