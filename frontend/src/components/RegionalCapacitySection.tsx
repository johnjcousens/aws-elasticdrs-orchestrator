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
  Grid,
} from '@cloudscape-design/components';
import { CapacityGauge } from './CapacityGauge';
import type { RegionalCapacityBreakdown } from '../types/staging-accounts';

interface RegionalCapacitySectionProps {
  regionalCapacity: RegionalCapacityBreakdown[];
}

export const RegionalCapacitySection: React.FC<RegionalCapacitySectionProps> = ({
  regionalCapacity,
}) => {
  // Filter to only show regions with active replicating servers
  const activeRegions = regionalCapacity.filter(r => r.replicatingServers > 0);

  if (activeRegions.length === 0) {
    return null;
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          description="Per-region capacity across all accounts (300 replication / 4,000 recovery per account per region)"
        >
          Regional Capacity
        </Header>
      }
    >
      <ColumnLayout columns={activeRegions.length === 1 ? 1 : 2} variant="text-grid">
        {activeRegions.map((region) => (
          <SpaceBetween key={region.region} size="xs">
            <Box variant="h4">{region.region}</Box>
            
            {/* Replication */}
            <Box variant="small" color="text-body-secondary">
              Replication: {region.replicatingServers} / {region.maxReplicating.toLocaleString()} ({region.accountCount} acct{region.accountCount !== 1 ? 's' : ''})
            </Box>
            <CapacityGauge
              used={region.replicatingServers}
              total={region.maxReplicating}
              size="small"
            />

            {/* Recovery */}
            <Box variant="small" color="text-body-secondary" padding={{ top: 'xs' }}>
              Recovery: {region.recoveryServers} / {region.recoveryMax.toLocaleString()}
            </Box>
            <CapacityGauge
              used={region.recoveryServers}
              total={region.recoveryMax}
              size="small"
            />
          </SpaceBetween>
        ))}
      </ColumnLayout>
    </Container>
  );
};
